"""
API Response Models

Pydantic models for API response payloads in the CV Intelligence Platform.
"""

from typing import List
from pydantic import BaseModel, Field

from src.models.domain.assessment import Assessment, MatchingScore
from src.models.domain.candidate import CandidateProfile
from src.models.domain.interview import DecisionResult
from src.models.domain.job import JobDescription


class ExtractCVResponse(BaseModel):
    """Response from CV extraction"""
    cv_id: str = Field(..., description="Extracted CV ID")
    profile: 'CandidateProfile' = Field(..., description="Candidate profile")
    raw_text: str = Field(..., description="Raw extracted text")
    normalized_text: str = Field(..., description="Normalized markdown")
    language: str = Field(..., description="Detected language")
    extraction_confidence: float = Field(..., description="Extraction confidence")

    class Config:
        frozen = False


class NormalizeJDResponse(BaseModel):
    """Response from JD normalization"""
    jd_id: str = Field(..., description="JD ID")
    job: 'JobDescription' = Field(..., description="Normalized job description")
    normalization_confidence: float = Field(..., description="Normalization confidence")

    class Config:
        frozen = False


class AssessResponse(BaseModel):
    """Response from assessment"""
    assessment: 'Assessment' = Field(..., description="Assessment result")
    decision: 'DecisionResult' = Field(..., description="Decision result")

    class Config:
        frozen = False


class SearchReuseResponse(BaseModel):
    """Response from search"""
    matches: List['Assessment'] = Field(default_factory=list, description="Matched assessments")
    total: int = Field(default=0, description="Total matches")

    class Config:
        frozen = False


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    mongodb: bool = Field(..., description="MongoDB connection status")
    ollama: bool = Field(..., description="Ollama service status")
    version: str = Field(..., description="API version")

    class Config:
        frozen = False


class MatchCandidateResponse(BaseModel):
    """Response from matching"""
    matching_score: 'MatchingScore' = Field(..., description="Detailed matching score")
    recommendation: str = Field(..., description="Whether to proceed")
    
    class Config:
        frozen = False