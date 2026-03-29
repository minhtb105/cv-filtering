# Phase 3D: Database Schema Migration Guide

**Status**: Phase 3D Implementation Plan  
**Date**: March 2026  
**Target**: Migrate from current schema to ATS-standard enhanced schema

---

## 📋 Table of Contents

1. [Overview & Strategy](#overview--strategy)
2. [PostgreSQL Schema Design](#postgresql-schema-design)
3. [MongoDB Collections Design](#mongodb-collections-design)
4. [Migration Scripts](#migration-scripts)
5. [Indexing Strategy](#indexing-strategy)
6. [Backward Compatibility](#backward-compatibility)
7. [Performance Considerations](#performance-considerations)

---

## Overview & Strategy

### Current Limitations
- Certifications & Languages: Text arrays (can't query by field)
- No structured location data
- No parsing metadata (confidence scores, extraction method)
- No derived fields in database
- No skill vector for ML/embedding searches
- Basic experience model (missing skills_used, impact_score)

### Goals
- ✅ Support structured, queryable data
- ✅ Enable ML-ready features (skill vectors, embeddings)
- ✅ Add audit trail (parser_version, parsing_metadata)
- ✅ Support full-text search on normalized skills
- ✅ Maintain backward compatibility during migration
- ✅ Zero downtime migration strategy

### Migration Strategy
1. **Phase 1**: Create new schema alongside existing (2-3 hours)
2. **Phase 2**: Backfill historical data with data transformation (4-6 hours)
3. **Phase 3**: Validate data integrity (2-3 hours)
4. **Phase 4**: Cutover (blue-green deployment) (30 mins)
5. **Phase 5**: Monitor & rollback plan (ongoing)

---

## PostgreSQL Schema Design

### 1. Candidates Table (Enhanced)

```sql
-- Core candidate information with enhanced fields
CREATE TABLE candidates (
    candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Contact Info
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone_e164 VARCHAR(20),  -- E.164 format (+84912345678)
    phone_raw VARCHAR(50),   -- Original format (backup)
    
    -- Location (Structured)
    location_city VARCHAR(100),
    location_country VARCHAR(100),
    location_country_code CHAR(2),
    location_remote_eligible BOOLEAN DEFAULT FALSE,
    
    -- Contact URLs
    linkedin_url VARCHAR(500),
    github_url VARCHAR(500),
    portfolio_url VARCHAR(500),
    
    -- Professional Summary
    summary_text TEXT,
    summary_embedding vector(1536),  -- OpenAI embedding for semantic search
    
    -- Metadata
    parser_version VARCHAR(50),
    extraction_method VARCHAR(30) DEFAULT 'pymupdf',  -- pymupdf|pdfplumber|ocr|manual
    extraction_confidence DECIMAL(3,2) DEFAULT 0.5,   -- 0-1
    raw_text_length INTEGER,
    detected_language VARCHAR(10) DEFAULT 'en',       -- vi|en|zh|etc
    
    -- Derived Fields (computed)
    total_experience_months INTEGER DEFAULT 0,
    seniority_level VARCHAR(20) DEFAULT 'mid',        -- junior|mid|senior|lead|principal
    skill_count INTEGER DEFAULT 0,
    avg_project_impact DECIMAL(3,2) DEFAULT 0,
    current_role VARCHAR(255),
    years_in_current_role DECIMAL(4,2) DEFAULT 0,
    highest_education_level VARCHAR(50),              -- high_school|bachelor|master|phd
    languages_spoken_count INTEGER DEFAULT 0,
    certifications_active_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parsed_at TIMESTAMP,
    
    -- Soft delete
    deleted_at TIMESTAMP,
    
    CONSTRAINT email_format CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$' OR email IS NULL),
    CONSTRAINT phone_format CHECK (phone_e164 ~ '^\+\d{10,15}$' OR phone_e164 IS NULL)
);

CREATE INDEX idx_candidates_email ON candidates(email);
CREATE INDEX idx_candidates_seniority ON candidates(seniority_level);
CREATE INDEX idx_candidates_location ON candidates(location_country_code, location_city);
CREATE INDEX idx_candidates_language ON candidates(detected_language);
CREATE INDEX idx_candidates_summary_embedding ON candidates USING ivfflat (summary_embedding vector_cosine_ops);
CREATE INDEX idx_candidates_created ON candidates(created_at DESC);
```

### 2. Skills Table (Normalized)

```sql
-- Skills lookup/dictionary (normalized)
CREATE TABLE skill_catalog (
    skill_id SERIAL PRIMARY KEY,
    
    -- Normalization
    canonical_name VARCHAR(100) UNIQUE NOT NULL,  -- "python", "react", "sql", etc
    display_name VARCHAR(150),                     -- "Python 3", "React.js", etc
    
    -- Categorization
    category VARCHAR(50),                          -- "language", "framework", "tool", "platform", etc
    subcategory VARCHAR(50),                       -- "backend", "frontend", "infrastructure", etc
    
    -- Metadata
    proficiency_levels TEXT[],                     -- ['beginner','intermediate','advanced','expert']
    related_skills TEXT[],                         -- Skills often seen together
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skills per candidate (structured)
CREATE TABLE candidate_skills (
    skill_assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skill_catalog(skill_id),
    
    -- Proficiency Info
    proficiency_level VARCHAR(20),                 -- junior|mid|senior|lead|principal
    years_experience DECIMAL(5,1),
    confidence DECIMAL(3,2),                       -- How confident extraction was (0-1)
    
    -- Context
    last_used_date DATE,                           -- YYYY-MM format
    frequency_mentions INTEGER DEFAULT 1,          -- How many times mentioned in CV
    
    -- Evidence (JSON for flexibility, could also normalize to separate table)
    evidence_json JSONB,  -- [ 
                          --   { project: "...", context: "...", quote: "...", metrics: [...], confidence: 0.9 },
                          --   ...
                          -- ]
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(candidate_id, skill_id)
);

CREATE INDEX idx_candidate_skills_candidate ON candidate_skills(candidate_id);
CREATE INDEX idx_candidate_skills_skill ON candidate_skills(skill_id);
CREATE INDEX idx_candidate_skills_confidence ON candidate_skills(confidence DESC);
```

### 3. Experience Table (Enhanced)

```sql
CREATE TABLE candidate_experience (
    experience_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    
    -- Position Info
    company_name VARCHAR(255) NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    job_description TEXT,
    
    -- Timeline
    start_date DATE NOT NULL,                      -- YYYY-MM format
    end_date DATE,                                 -- NULL if current role
    duration_months INTEGER,
    is_current BOOLEAN DEFAULT FALSE,
    
    -- Skills & Impact
    skills_used TEXT[],                            -- Denormalized for query speed
    achievements TEXT[],
    impact_score INTEGER,                          -- 1-5 scale
    evidence_strength DECIMAL(3,2),                -- 0-1
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT date_order CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE INDEX idx_experience_candidate ON candidate_experience(candidate_id);
CREATE INDEX idx_experience_current ON candidate_experience(is_current, candidate_id);
```

### 4. Certifications Table (Structured)

```sql
CREATE TABLE candidate_certifications (
    certification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    
    certification_name VARCHAR(255) NOT NULL,
    issuer_name VARCHAR(255) NOT NULL,
    
    -- Timeline
    issue_date DATE,                               -- YYYY-MM
    expiry_date DATE,                              -- NULL if non-expiring
    is_current BOOLEAN DEFAULT TRUE,
    
    credential_id VARCHAR(255),                    -- ID or URL
    credential_url VARCHAR(500),
    confidence DECIMAL(3,2) DEFAULT 0.7,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT cert_dates_valid CHECK (expiry_date IS NULL OR expiry_date >= issue_date)
);

CREATE INDEX idx_certifications_candidate ON candidate_certifications(candidate_id);
CREATE INDEX idx_certifications_current ON candidate_certifications(is_current);
CREATE INDEX idx_certifications_expiry ON candidate_certifications(expiry_date) WHERE is_current;
```

### 5. Languages Table (Structured)

```sql
CREATE TABLE candidate_languages (
    language_assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    
    language_name VARCHAR(100) NOT NULL,
    cefr_level VARCHAR(10) NOT NULL,               -- A1|A2|B1|B2|C1|C2|NATIVE|FLUENT
    is_native BOOLEAN DEFAULT FALSE,
    confidence DECIMAL(3,2) DEFAULT 0.6,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(candidate_id, language_name)
);

CREATE INDEX idx_languages_candidate ON candidate_languages(candidate_id);
```

### 6. Jobs Table (Enhanced)

```sql
CREATE TABLE job_descriptions (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    job_title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    job_description TEXT NOT NULL,
    
    -- Requirements
    required_skills TEXT[] NOT NULL,
    preferred_skills TEXT[] DEFAULT '{}',
    required_experience_months INTEGER,
    
    seniority_level VARCHAR(20),                   -- junior|mid|senior|lead|principal
    location_city VARCHAR(100),
    location_country VARCHAR(100),
    location_remote BOOLEAN DEFAULT FALSE,
    
    required_languages TEXT[] DEFAULT '{}',
    salary_range VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT has_skills CHECK (array_length(required_skills, 1) > 0)
);

CREATE INDEX idx_jobs_seniority ON job_descriptions(seniority_level);
CREATE INDEX idx_jobs_created ON job_descriptions(created_at DESC);
```

### 7. Matching Scores Table (Materialized)

```sql
CREATE TABLE matching_scores (
    matching_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    candidate_id UUID NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES job_descriptions(job_id) ON DELETE CASCADE,
    
    -- Component Scores
    skill_match DECIMAL(3,2),
    skill_match_required DECIMAL(3,2),
    skill_match_preferred DECIMAL(3,2),
    experience_match DECIMAL(3,2),
    seniority_fit DECIMAL(3,2),
    project_relevance DECIMAL(3,2),
    education_fit DECIMAL(3,2),
    location_fit DECIMAL(3,2),
    language_fit DECIMAL(3,2),
    
    -- Overall
    overall_score DECIMAL(4,3),                    -- 0-1.0
    match_percentage DECIMAL(5,1),                 -- 0-100%
    
    -- Gaps
    missing_required_skills TEXT[],
    missing_preferred_skills TEXT[],
    experience_gap_months INTEGER,
    
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    matching_model_version VARCHAR(50),
    
    UNIQUE(candidate_id, job_id),
    CONSTRAINT score_range CHECK (overall_score BETWEEN 0 AND 1)
);

CREATE INDEX idx_matching_candidate ON matching_scores(candidate_id);
CREATE INDEX idx_matching_job ON matching_scores(job_id);
CREATE INDEX idx_matching_score_desc ON matching_scores(overall_score DESC);
CREATE INDEX idx_matching_calculated ON matching_scores(calculated_at DESC);
```

---

## MongoDB Collections Design

### Alternative: MongoDB Collections

```javascript
db.createCollection("candidates", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "email", "contact"],
      properties: {
        _id: { bsonType: "objectId" },
        
        name: { bsonType: "string" },
        email: { bsonType: "string" },
        phone_e164: { bsonType: "string" },
        
        contact: {
          bsonType: "object",
          properties: {
            location: {
              bsonType: "object",
              properties: {
                city: { bsonType: "string" },
                country: { bsonType: "string" },
                country_code: { bsonType: "string" }
              }
            },
            linkedin_url: { bsonType: "string" },
            github_url: { bsonType: "string" }
          }
        },
        
        skills: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              canonical_name: { bsonType: "string" },
              years_experience: { bsonType: "double" },
              confidence: { bsonType: "double" },
              evidence: { bsonType: "array" }
            }
          }
        },
        
        experience: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              company: { bsonType: "string" },
              title: { bsonType: "string" },
              duration_months: { bsonType: "int" },
              skills_used: { bsonType: "array" }
            }
          }
        },
        
        certifications: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              name: { bsonType: "string" },
              issuer: { bsonType: "string" },
              is_current: { bsonType: "bool" }
            }
          }
        },
        
        seniority_level: { bsonType: "string" },
        total_experience_months: { bsonType: "int" },
        
        parsing_metadata: {
          bsonType: "object",
          properties: {
            parser_version: { bsonType: "string" },
            extraction_method: { bsonType: "string" },
            confidence_score: { bsonType: "double" }
          }
        },
        
        created_at: { bsonType: "date" },
        updated_at: { bsonType: "date" }
      }
    }
  }
});

db.candidates.createIndex({ email: 1 });
db.candidates.createIndex({ seniority_level: 1 });
db.candidates.createIndex({ "contact.location.country_code": 1 });
db.candidates.createIndex({ overall_score: -1 });
```

---

## Migration Scripts

### Migration Strategy

```bash
# 1. Create new schema
psql -U postgres < schema_enhanced.sql

# 2. Backfill data (idempotent)
python3 scripts/migrate_candidates.py --batch-size 1000

# 3. Validate
python3 scripts/validate_migration.py

# 4. Cutover (using feature flag)
# - Set MIGRATION_ENABLED=true
# - Read from new schema
# - Write to both schemas (dual-write)
# - Monitor for 24 hours

# 5. Cleanup old schema (after validation)
python3 scripts/cleanup_old_data.py --dry-run
psql -U postgres < schema_cleanup.sql
```

### Python Migration Script

```python
# scripts/migrate_candidates.py
import asyncio
from sqlalchemy import create_engine
import logging

logger = logging.getLogger(__name__)

async def migrate_candidates(batch_size: int = 1000):
    """Migrate candidates from old schema to new schema"""
    
    # Connect to database
    engine = create_engine("postgresql://user:pass@localhost/cv_filtering")
    
    # Get all candidates from old schema
    with engine.connect() as conn:
        old_candidates = conn.execute(
            "SELECT * FROM candidates_old ORDER BY id"
        ).fetchall()
    
    # Transform and insert into new schema
    for batch in chunks(old_candidates, batch_size):
        transformed = [
            transform_candidate(c) for c in batch
        ]
        
        with engine.begin() as conn:
            conn.execute(
                insert(candidates).values(transformed)
            )
        
        logger.info(f"Migrated {len(batch)} candidates")

def transform_candidate(old_candidate):
    """Transform old schema to new schema"""
    return {
        'candidate_id': old_candidate.id,
        'name': old_candidate.name,
        'email': old_candidate.email,
        'phone_e164': normalize_phone(old_candidate.phone),
        'location_country': old_candidate.location,
        # ... map other fields
    }
```

---

## Indexing Strategy

### Query Patterns & Indexes

```sql
-- 1. Search candidates by location + seniority (Common)
CREATE INDEX idx_candidates_location_seniority 
  ON candidates(location_country_code, seniority_level);

-- 2. Find active certifications expiring soon (Periodic)
CREATE INDEX idx_certifications_expiry_active 
  ON candidate_certifications(expiry_date, is_current)
  WHERE is_current = true;

-- 3. Top matches for a job (Very common)
CREATE INDEX idx_matching_job_score 
  ON matching_scores(job_id, overall_score DESC);

-- 4. Semantic search on summary (Optional, needs vector DB)
CREATE INDEX idx_candidates_summary_embedding 
  ON candidates USING ivfflat (summary_embedding vector_cosine_ops);

-- 5. Full-text search on skills (For UI search)
CREATE INVERTED INDEX idx_candidate_skills_fulltext
  ON candidate_skills USING GIN (skill_display_name gin_trgm_ops);
```

---

## Backward Compatibility

### Migration Phase 1: Dual-Write

```python
# app/db/migrations.py
async def save_candidate_v2(profile: CandidateProfile):
    """Save to both old and new schema"""
    
    # Write to new schema
    await insert_candidate_enhanced(profile)
    
    # Write to old schema (if old system still running)
    await insert_candidate_legacy(profile)
```

### Migration Phase 2: Read Switch

```python
# Feature flag to control which schema to read from
READ_FROM_ENHANCED = os.getenv("ENHANCED_SCHEMA_ENABLED", "false") == "true"

async def get_candidate(candidate_id):
    if READ_FROM_ENHANCED:
        return await get_candidate_enhanced(candidate_id)
    else:
        return await get_candidate_legacy(candidate_id)
```

---

## Performance Considerations

### 1. Denormalization Strategy
- Store `skills_used` (TEXT[]) in `experience` for fast queries
- Store `seniority_level` in `candidates` to avoid joins

### 2. Query Optimization
```sql
-- Instead of JOIN (slow)
SELECT c.*, e.skills_used FROM candidates c
  JOIN candidate_experience e ON c.candidate_id = e.candidate_id

-- Denormalize as
SELECT candidate_id, seniority_level FROM candidates
  -- seniority already computed at save time
```

### 3. Caching Strategy
- Cache matching scores (invalidate on CV/JD update)
- Cache skill catalog (infrequently changes)
- Short-lived cache for rankings

### 4. Partitioning (if >100M candidates)
```sql
-- Partition by seniority level
CREATE TABLE candidates_junior PARTITION OF candidates
  FOR VALUES IN ('junior');
```

---

## Rollback Plan

### If Migration Fails
1. Stop writes to new schema
2. Switch reads back to old schema
3. Investigate data inconsistency
4. Re-run migration with fixes
5. Validate again before cutover

### Monitoring During Migration
```python
# Monitor data consistency
async def validate_migration():
    old_count = await count_candidates_old()
    new_count = await count_candidates_new()
    
    assert old_count == new_count, "Row count mismatch!"
    
    # Spot check random candidates
    for _ in range(100):
        old = get_random_candidate_old()
        new = get_random_candidate_new(old.id)
        assert old.name == new.name, f"Name mismatch: {old.name} vs {new.name}"
```

---

## Timeline & Effort

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| 3D-1 | Create PostgreSQL schemas | 2-3 hrs | ⏳ |
| 3D-2 | Write migration scripts | 2-3 hrs | ⏳ |
| 3D-3 | Test on staging | 4-6 hrs | ⏳ |
| 3D-4 | Backfill + validate | 6-8 hrs | ⏳ |
| 3D-5 | Production cutover | 30 mins | ⏳ |

**Total Estimated Time**: 1-2 days (depending on data volume)

---

## Next Steps

1. ✅ Review schema design with team
2. ✅ Test on staging environment
3. ✅ Create rollback procedures
4. ✅ Schedule cutover window
5. ✅ Execute migration with monitoring
6. ✅ Validate data integrity
7. ✅ Decommission old schema (after 30-day stability period)

---

**Questions?** See [IMPLEMENTATION_COMPLETE.md](../IMPLEMENTATION_COMPLETE.md)
