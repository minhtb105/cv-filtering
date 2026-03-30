"""
Enhanced Pydantic schemas for CV Intelligence Platform
Comprehensive ATS-standard data models with normalization, validation, and matching

This file now serves as a compatibility layer that re-exports all models from the
new organized src/models/ directory structure.

Features:
- ✅ Structured certifications (issuer, dates, credential tracking)
- ✅ Structured languages (CEFR levels A1-C2)
- ✅ E.164 phone normalization
- ✅ Derived fields (total_experience_months, skill_vector, seniority)
- ✅ Metadata tracking (parser_version, extraction_method, confidence_score)
- ✅ Matching model with score components
- ✅ Enhanced validation constraints
"""

# Re-export all models from the new organized structure
from src.models import *

# Keep the original __all__ for backward compatibility
__all__ = [
    # Extraction models
    'Word', 'Line', 'Block', 'PageGeometry', 'ExtractionResult',
    
    # Domain models
    'CandidateProfile', 'ContactInfo', 'Skill', 'SkillEvidence',
    'CareerProgression', 'Project', 'Education', 'Certification', 'Language',
    'RiskFlag', 'DerivedFields', 'ParsingMetadata',
    'JobDescription', 'ScoreBreakdown',
    'Assessment', 'MatchingScore',
    'InterviewFeedback', 'DecisionResult',
    'CVVersion',
    
    # Validation
    'CEFRLEVEL', 'SeniorityLevel', 'ExtractionMethod', 'RiskFlagType',
    'RiskLevel', 'DecisionType', 'InterviewRound', 'InterviewDecision',
    'PhoneValidator', 'DateValidator',
    
    # API
    'ExtractCVRequest', 'NormalizeJDRequest', 'AssessRequest', 'SearchReuseRequest',
    'MatchCandidateRequest',
    'ExtractCVResponse', 'NormalizeJDResponse', 'AssessResponse', 'SearchReuseResponse',
    'HealthCheckResponse', 'MatchCandidateResponse'
]
