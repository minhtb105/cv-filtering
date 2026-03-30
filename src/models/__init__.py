"""
CV Intelligence Platform Data Models

This module provides the core data models organized into logical groups:
- extraction: PDF extraction pipeline data structures
- domain: Business domain models (candidates, jobs, assessments)
- validation: Validation utilities and enums
- api: API request/response schemas
"""

# Re-export main models for convenient imports
from .extraction.pdf_dataclasses import (
    Word,
    Line, 
    Block,
    PageGeometry,
    ExtractionResult
)

from .domain.candidate import (
    CandidateProfile,
    ContactInfo,
    Skill,
    SkillEvidence,
    CareerProgression,
    Project,
    Education,
    Certification,
    Language,
    RiskFlag,
    DerivedFields,
    ParsingMetadata
)

from .domain.job import (
    JobDescription,
    ScoreBreakdown
)

from .domain.assessment import (
    Assessment,
    MatchingScore
)

from .domain.interview import (
    InterviewFeedback,
    DecisionResult
)

from .domain.cv_version import (
    CVVersion
)

from .validation.enums import (
    CEFRLEVEL,
    SeniorityLevel,
    ExtractionMethod,
    RiskFlagType,
    RiskLevel,
    DecisionType,
    InterviewRound,
    InterviewDecision
)

from .validation.validators import (
    PhoneValidator,
    DateValidator
)

from .api.requests import (
    ExtractCVRequest,
    NormalizeJDRequest,
    AssessRequest,
    SearchReuseRequest,
    MatchCandidateRequest
)

from .api.responses import (
    ExtractCVResponse,
    NormalizeJDResponse,
    AssessResponse,
    SearchReuseResponse,
    HealthCheckResponse,
    MatchCandidateResponse
)

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