"""Pydantic models for API requests and responses."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class DetailedScoreRequest(BaseModel):
    """Request to score a CV against a JD."""
    cv_id: str = Field(..., description="CV ID")
    jd_id: str = Field(..., description="Job Description ID")
    include_history: bool = Field(False, description="Include score history")


class BatchScoreRequest(BaseModel):
    """Request to score multiple CVs."""
    cv_jd_pairs: List[tuple] = Field(..., description="List of (cv_id, jd_id) tuples")


class InterviewResultRequest(BaseModel):
    """Request to add interview result."""
    cv_id: str = Field(..., description="CV ID")
    technical_score: float = Field(..., ge=0, le=100, description="Technical skills score")
    soft_skills_score: float = Field(..., ge=0, le=100, description="Soft skills score")
    cultural_fit_score: float = Field(..., ge=0, le=100, description="Cultural fit score")
    notes: Optional[str] = Field(None, description="Interview notes")


class RescoringRequest(BaseModel):
    """Request to trigger rescoring."""
    trigger: str = Field(..., description="Trigger type: CV_UPDATE, INTERVIEW_RESULT, JD_UPDATE, MANUAL")
    cv_ids: Optional[List[str]] = Field(None, description="CV IDs to rescore")
    jd_id: Optional[str] = Field(None, description="JD ID")
    reason: str = Field("", description="Reason for rescoring")
    priority: int = Field(5, ge=0, le=10, description="Priority (0-10)")


class NewCVVersionRequest(BaseModel):
    """Request to register a new CV version."""
    cv_id: str = Field(..., description="CV ID")
    reason: Optional[str] = Field(None, description="Reason for update")


class UpdateJDRequest(BaseModel):
    """Request to update a job description."""
    jd_id: str = Field(..., description="JD ID")
    jd_data: Dict[str, Any] = Field(..., description="Job description data")
    reason: Optional[str] = Field(None, description="Reason for update")


class ComparisonRequest(BaseModel):
    """Request to compare CV vs JD."""
    cv_id: str = Field(..., description="CV ID")
    jd_id: str = Field(..., description="JD ID")
    include_detailed: bool = Field(True, description="Include detailed breakdown")


class RankingRequest(BaseModel):
    """Request to rank CVs for a JD."""
    jd_id: str = Field(..., description="JD ID")
    cv_ids: List[str] = Field(..., description="CV IDs to rank")
    limit: Optional[int] = Field(None, description="Limit results")


# Response Models

class ScoreBreakdown(BaseModel):
    """Score breakdown by component."""
    skill_weight: float
    experience_weight: float
    education_weight: float
    interview_weight: Optional[float] = None


class ScoreResult(BaseModel):
    """Score result for a CV-JD pair."""
    cv_id: str
    jd_id: str
    cv_version: int = Field(0, description="CV version number")
    jd_version: int = Field(0, description="JD version number")
    skill_score: float = Field(..., ge=0, le=100)
    experience_score: float = Field(..., ge=0, le=100)
    education_score: float = Field(..., ge=0, le=100)
    interview_score: Optional[float] = Field(None, ge=0, le=100)
    composite_score: float = Field(..., ge=0, le=100)
    breakdown: ScoreBreakdown
    timestamp: datetime
    cached: bool = False
    cache_hit: bool = False


class ScoreHistoryResponse(BaseModel):
    """Score history response."""
    cv_id: str
    jd_id: str
    history: List[ScoreResult]
    total_scores: int


class BatchScoreResponse(BaseModel):
    """Batch scoring response."""
    results: List[ScoreResult]
    total: int
    successful: int
    failed: int


class ComparisonResult(BaseModel):
    """Detailed comparison result."""
    cv_id: str
    jd_id: str
    composite_score: float
    skill_gaps: List[str]
    experience_fit: str
    education_fit: str
    strengths: List[str]
    weaknesses: List[str]


class RankingResult(BaseModel):
    """Ranking result for multiple CVs."""
    jd_id: str
    rankings: List[tuple]  # [(cv_id, score), ...]
    total_ranked: int


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    cache_status: str
    database_status: str
    api_version: str


class MetricsResponse(BaseModel):
    """System metrics response."""
    cache_hit_rate: float
    avg_scoring_time: float
    rescore_queue_length: int
    total_scores_computed: int
    uptime_seconds: float


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
