# API Documentation - CV Intelligence Platform

**Base URL**: `http://localhost:8000`  
**Documentation**: `http://localhost:8000/docs` (auto-generated Swagger UI)

---

## Authentication
Currently no authentication. Add in deployment phase.

---

## Endpoints

### 1. Search Candidates
**Endpoint**: `POST /search`  
**Description**: Search for candidates using hybrid retrieval (semantic + keyword)

#### Request
```json
{
  "query": "Python developer with 5 years experience",
  "k": 10,
  "semantic_weight": 0.6
}
```

#### Parameters
- `query` (string, required): Search query
- `k` (int, optional): Number of results (default: 10, max: 20)
- `semantic_weight` (float, optional): Weight for semantic search (0-1, default: 0.6)

#### Response
```json
[
  {
    "candidate_id": "cand_b1003fe82c76",
    "score": 0.85,
    "semantic_score": 0.92,
    "keyword_score": 0.78,
    "name": "John Python Developer",
    "skills": ["Python", "Django", "REST", "PostgreSQL"]
  },
  ...
]
```

#### Example
```bash
# Python
import requests

response = requests.post("http://localhost:8000/search", json={
    "query": "python developer django",
    "k": 5,
    "semantic_weight": 0.7
})
candidates = response.json()
for cand in candidates:
    print(f"{cand['name']}: {cand['score']:.3f}")
```

```bash
# cURL
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"python developer","k":5}'
```

---

### 2. Get Candidate
**Endpoint**: `GET /candidates/{candidate_id}`  
**Description**: Get detailed information about a candidate

#### Parameters
- `candidate_id` (string, path): Candidate ID (e.g., `cand_001`)

#### Response
```json
{
  "candidate_id": "cand_b1003fe82c76",
  "name": "John Python Developer",
  "email": "john@example.com",
  "skills": ["Python", "Django", "REST", "PostgreSQL", "AWS"],
  "years_experience": 5.5,
  "experiences": [
    {
      "title": "Senior Python Developer",
      "company": "TechCorp",
      "duration": "2020-Present"
    },
    {
      "title": "Python Developer",
      "company": "StartupXYZ",
      "duration": "2018-2020"
    }
  ]
}
```

#### Example
```bash
curl "http://localhost:8000/candidates/cand_b1003fe82c76"
```

---

### 3. Score Candidates
**Endpoint**: `POST /score`  
**Description**: Score candidates for a specific job using multi-factor ranking

#### Request
```json
{
  "job_description": "Senior Python Developer needed. 5+ years required. Must know Django, REST APIs, and PostgreSQL.",
  "candidate_ids": ["cand_001", "cand_002", "cand_003"],
  "model": "hybrid"
}
```

#### Parameters
- `job_description` (string, required): Job posting text
- `candidate_ids` (list[string], required): Candidate IDs to score
- `model` (string, optional): Scoring model - "hybrid" (default), "rule_based", "llm"

#### Response
```json
{
  "results": [
    {
      "candidate_id": "cand_001",
      "score": 0.87,
      "skill_match": 0.95,
      "experience_match": 1.00,
      "breakdownstr": {
        "total_score": 0.87,
        "skill_match": 0.95,
        "experience_match": 1.00,
        "seniority": 0.85,
        "education": 0.80,
        "language_match": 0.95,
        "breakdown": {...}
      }
    },
    {
      "candidate_id": "cand_002",
      "score": 0.76,
      ...
    }
  ]
}
```

#### Scoring Factors
The response includes scores for:
- `skill_match` (0-1): How well candidate's skills match job requirements
- `experience_match` (0-1): Years of experience alignment
- `seniority` (0-1): Career level match (junior/mid/senior)
- `education` (0-1): Degree/credential match
- `language_match` (0-1): Language requirement fulfillment
- Total is weighted combination of above

#### Example
```bash
curl -X POST "http://localhost:8000/score" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Python Engineer with 5+ years",
    "candidate_ids": ["cand_001", "cand_002"]
  }'
```

---

### 4. Similar Candidates
**Endpoint**: `GET /candidates/{candidate_id}/similar`  
**Description**: Find candidates similar to a specified candidate

#### Parameters
- `candidate_id` (string, path): Reference candidate ID
- `k` (int, query): Number of similar candidates (default: 5, range: 1-20)

#### Response
```json
[
  {
    "candidate_id": "cand_005",
    "name": "Similar Developer",
    "similarity": 0.92
  },
  {
    "candidate_id": "cand_007",
    "name": "Another Match",
    "similarity": 0.88
  }
]
```

#### Example
```bash
curl "http://localhost:8000/candidates/cand_001/similar?k=5"
```

---

### 5. Health Check
**Endpoint**: `GET /health`  
**Description**: Check if API is online

#### Response
```json
{
  "status": "online",
  "timestamp": "2026-03-20T10:30:45.123456"
}
```

#### Example
```bash
curl http://localhost:8000/health
```

---

### 6. System Statistics
**Endpoint**: `GET /stats`  
**Description**: Get platform statistics

#### Response
```json
{
  "total_candidates": 258,
  "retrieval_stats": {
    "vector_index": {
      "total_vectors": 258,
      "dimension": 384,
      "indexed_candidates": 258,
      "created_at": "2026-03-20T06:48:45.123456"
    },
    "keyword_index": {
      "documents": 258,
      "terms": 2547
    },
    "cached_candidates": 258
  },
  "timestamp": "2026-03-20T10:35:12.654321"
}
```

#### Example
```bash
curl http://localhost:8000/stats
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Query cannot be empty"
}
```

### 404 Not Found
```json
{
  "detail": "Candidate not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting
Currently none. Add in production:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
@app.post("/search")
@limiter.limit("100/minute")
async def search_candidates(request: SearchRequest):
    ...
```

---

## Authentication (Planned)
For future deployment, add:
```python
from fastapi.security import HTTPBearer, HTTPAuthenticationCredentials

security = HTTPBearer()

@app.post("/search")
async def search_candidates(
    request: SearchRequest,
    credentials: HTTPAuthenticationCredentials = Depends(security)
):
    token = credentials.credentials
    verify_token(token)  # Custom verification
    ...
```

---

## Performance Tips

1. **Batch Scoring**: Score multiple candidates in one request
   ```bash
   # Better: Score 10 candidates in 1 call
   curl -X POST http://localhost:8000/score \
     -d '{"candidate_ids": ["cand_1", "cand_2", ...]}' 
   # Query time: ~50ms
   
   # Worse: Score 10 candidates in 10 calls
   # Total time: ~500ms
   ```

2. **Hybrid Search Weight**: Tune for your use case
   - `semantic_weight=1.0`: Pure semantic (best for skill description matching)
   - `semantic_weight=0.5`: Balanced (recommended for most use cases)
   - `semantic_weight=0.0`: Pure keyword (best for exact title matching)

3. **Limit Result Count**: Only request needed results
   ```bash
   # Better: k=10
   curl http://localhost:8000/search?query=python&k=10
   
   # Worse: k=100 (uses more memory, slower sorting)
   ```

---

## Example Workflows

### Workflow 1: Find Top 5 Candidates for Job
```python
import requests

# 1. Search for candidates matching job
job_skills = "python django rest api postgresql"
search_response = requests.post(
    "http://localhost:8000/search",
    json={
        "query": job_skills,
        "k": 20,
        "semantic_weight": 0.6
    }
)
candidate_ids = [c["candidate_id"] for c in search_response.json()]

# 2. Score those candidates against full job description
job_desc = """
Senior Python Developer
5+ years experience with Python and Django
REST API design experience
PostgreSQL database skills
Team lead in previous role
"""

scoring_response = requests.post(
    "http://localhost:8000/score",
    json={
        "job_description": job_desc,
        "candidate_ids": candidate_ids[:10]
    }
)

# 3. Extract top 5
results = scoring_response.json()["results"]
top_5 = sorted(results, key=lambda x: x["score"], reverse=True)[:5]

for rank, candidate in enumerate(top_5, 1):
    print(f"{rank}. {candidate['candidate_id']}: {candidate['score']:.2f}")
```

### Workflow 2: Find Similar Candidates
```python
# Find candidates similar to "cand_001"
similar = requests.get(
    "http://localhost:8000/candidates/cand_001/similar?k=10"
).json()

for similar_candidate in similar:
    print(f"{similar_candidate['name']}: "
          f"similarity={similar_candidate['similarity']:.2f}")
```

### Workflow 3: Search with Custom Weight
```python
# Emphasize semantic matching for skill-focused search
results = requests.post(
    "http://localhost:8000/search",
    json={
        "query": "machine learning tensorflow pytorch",
        "k": 10,
        "semantic_weight": 0.8  # 80% semantic, 20% keyword
    }
).json()
```

---

## Deployment Checklist

Before going to production:

- [ ] Add authentication (API keys or JWT)
- [ ] Enable HTTPS/TLS
- [ ] Add rate limiting (100/min per IP)
- [ ] Setup logging and monitoring
- [ ] Configure CORS if serving multiple domains
- [ ] Setup error tracking (Sentry)
- [ ] Add request validation and sanitization
- [ ] Setup database persistence for audit trail
- [ ] Container image (Docker)
- [ ] Load balancing for scale (separate API instances)
- [ ] Cache invalidation strategy
- [ ] Backup/restore procedures

---

## Troubleshooting

### Embedding Model Not Found
```
ModuleNotFoundError: No module named 'faiss'
```
**Fix**: `pip install faiss-cpu sentence-transformers`

### Candidate Not Found
```
{"detail": "Candidate not found"}
```
**Fix**: Verify candidate_id exists by checking `/stats` or previous `/search` results

### Empty Search Results
**Possible causes**:
1. All candidates already indexed with same query
2. Semantic_weight too low (try increasing to 0.8)
3. Query too specific (try broader terms)

**Debug**:
```bash
# Check system stats
curl http://localhost:8000/stats

# Try pure keyword search
curl -X POST http://localhost:8000/search \
  -d '{"query":"python","k":10,"semantic_weight":0.0}'
```

---

## Support
For issues, see: [PROGRESS_REPORT.md](./PROGRESS_REPORT.md)
