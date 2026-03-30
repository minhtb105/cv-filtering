"""
Domain Models for CV Intelligence Platform

Contains the core business domain models that represent the entities in the CV
Intelligence Platform including candidates, jobs, assessments, and related entities.
"""

from .candidate import (
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

from .job import (
    JobDescription,
    ScoreBreakdown
)

from .assessment import (
    Assessment,
    MatchingScore
)

from .interview import (
    InterviewFeedback,
    DecisionResult
)

from .cv_version import (
    CVVersion
)

__all__ = [
    # Candidate models
    'CandidateProfile', 'ContactInfo', 'Skill', 'SkillEvidence',
    'CareerProgression', 'Project', 'Education', 'Certification', 'Language',
    'RiskFlag', 'DerivedFields', 'ParsingMetadata',
    
    # Job models
    'JobDescription', 'ScoreBreakdown',
    
    # Assessment models
    'Assessment', 'MatchingScore',
    
    # Interview models
    'InterviewFeedback', 'DecisionResult',
    
    # Version models
    'CVVersion'
]