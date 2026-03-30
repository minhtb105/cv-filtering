"""
API Request/Response Models

Contains Pydantic models for API requests and responses used throughout the CV
Intelligence Platform.
"""

from .requests import (
    ExtractCVRequest,
    NormalizeJDRequest,
    AssessRequest,
    SearchReuseRequest,
    MatchCandidateRequest
)

from .responses import (
    ExtractCVResponse,
    NormalizeJDResponse,
    AssessResponse,
    SearchReuseResponse,
    HealthCheckResponse,
    MatchCandidateResponse
)

__all__ = [
    'ExtractCVRequest', 'NormalizeJDRequest', 'AssessRequest', 'SearchReuseRequest',
    'MatchCandidateRequest',
    'ExtractCVResponse', 'NormalizeJDResponse', 'AssessResponse', 'SearchReuseResponse',
    'HealthCheckResponse', 'MatchCandidateResponse'
]