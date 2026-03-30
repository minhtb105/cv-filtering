"""
Job Description Models

Models for job descriptions and score breakdowns used in the CV Intelligence Platform.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from src.models.domain.candidate import LocationFormat
from src.models.validation.enums import SeniorityLevel


class JobDescription(BaseModel):
    """Job description schema"""
    jd_id: Optional[str] = Field(None, description="Job ID")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: str = Field(..., description="Full job description")
    requirements: List[str] = Field(default_factory=list, description="Job requirements")
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities")
    required_skills: List[str] = Field(default_factory=list, description="Required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred skills")
    seniority_level: Optional[SeniorityLevel] = Field(None, description="Expected seniority")
    experience_years_min: Optional[int] = Field(None, ge=0, description="Minimum years experience")
    experience_years_max: Optional[int] = Field(None, ge=0, description="Maximum years (if junior)")
    location: Optional['LocationFormat'] = Field(None, description="Job location")
    salary_range: Optional[str] = Field(None, description="Salary range")
    languages_required: List[str] = Field(default_factory=list, description="Required languages")
    remote_eligible: bool = Field(default=False, description="Remote/hybrid eligible")
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc), description="Created timestamp")
    
    class Config:
        frozen = False


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown"""
    skill_match: float = Field(default=0.0, ge=0, le=1, description="Skill match")
    experience_match: float = Field(default=0.0, ge=0, le=1, description="Experience match")
    project_relevance: float = Field(default=0.0, ge=0, le=1, description="Project relevance")
    seniority_fit: float = Field(default=0.0, ge=0, le=1, description="Seniority fit")
    overall_score: float = Field(default=0.0, ge=0, le=1, description="Overall score")
    
    class Config:
        frozen = False