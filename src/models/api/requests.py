"""
API Request Models

Pydantic models for API request payloads in the CV Intelligence Platform.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ExtractCVRequest(BaseModel):
    """Request to extract CV"""
    file_path: Optional[str] = Field(None, description="Path to CV file")
    file_content: Optional[bytes] = Field(None, description="CV file content (base64)")
    file_url: Optional[str] = Field(None, description="URL to CV file")
    translate: bool = Field(default=True, description="Translate to English")

    class Config:
        frozen = False


class NormalizeJDRequest(BaseModel):
    """Request to normalize JD"""
    jd_text: Optional[str] = Field(None, description="JD text content")
    jd_id: Optional[str] = Field(None, description="Existing JD ID")

    class Config:
        frozen = False


class AssessRequest(BaseModel):
    """Request to assess CV against JD"""
    cv_id: str = Field(..., description="CV ID to assess")
    jd_id: str = Field(..., description="JD ID to assess against")
    force_reassess: bool = Field(default=False, description="Force reassessment")

    class Config:
        frozen = False


class SearchReuseRequest(BaseModel):
    """Request to search for reusable CVs"""
    jd_id: str = Field(..., description="JD ID to match")
    min_score: float = Field(default=0.7, ge=0, le=1, description="Minimum match score")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")

    class Config:
        frozen = False


class MatchCandidateRequest(BaseModel):
    """Request to match candidate with job"""
    candidate_id: str = Field(..., description="Candidate ID")
    job_id: str = Field(..., description="Job ID")
    use_cached: bool = Field(default=True, description="Use cached results if available")
    
    class Config:
        frozen = False
        