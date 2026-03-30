"""
Validation Utilities and Enumerations

Contains validation classes, utility functions, and enumerations used throughout
the CV Intelligence Platform for data validation, normalization, and type safety.
"""

from .enums import (
    CEFRLEVEL,
    SeniorityLevel,
    ExtractionMethod,
    RiskFlagType,
    RiskLevel,
    DecisionType,
    InterviewRound,
    InterviewDecision
)

from .validators import (
    PhoneValidator,
    DateValidator
)

__all__ = [
    'CEFRLEVEL', 'SeniorityLevel', 'ExtractionMethod', 'RiskFlagType',
    'RiskLevel', 'DecisionType', 'InterviewRound', 'InterviewDecision',
    'PhoneValidator', 'DateValidator'
]