"""
Assessment Models

Models for assessment results, matching scores, and decision outcomes in the CV Intelligence Platform.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from src.models.domain.candidate import CandidateProfile, RiskFlag
from src.models.domain.job import JobDescription, ScoreBreakdown
from src.models.validation.enums import DecisionType


class MatchingScore(BaseModel):
    """Detailed matching score between candidate and job"""
    candidate_id: str = Field(..., description="Candidate ID")
    job_id: str = Field(..., description="Job ID")
    
    # Component scores (0-1)
    skill_match: float = Field(default=0.0, ge=0, le=1, description="Required skills match %")
    skill_match_required: float = Field(default=0.0, ge=0, le=1, description="Required skills coverage")
    skill_match_preferred: float = Field(default=0.0, ge=0, le=1, description="Preferred skills match")
    
    experience_match: float = Field(default=0.0, ge=0, le=1, description="Experience level match")
    experience_years_match: float = Field(default=0.0, ge=0, le=1, description="Years of experience match")
    seniority_fit: float = Field(default=0.0, ge=0, le=1, description="Seniority level fit")
    
    project_relevance: float = Field(default=0.0, ge=0, le=1, description="Project relevance score")
    education_fit: float = Field(default=0.0, ge=0, le=1, description="Education requirements fit")
    
    location_fit: float = Field(default=0.5, ge=0, le=1, description="Location/remote fit")
    language_fit: float = Field(default=0.5, ge=0, le=1, description="Language requirements fit")
    
    # Gaps
    missing_required_skills: List[str] = Field(default_factory=list, description="Required skills missing")
    missing_preferred_skills: List[str] = Field(default_factory=list, description="Preferred skills missing")
    experience_gap_months: int = Field(default=0, description="Experience deficit in months")
    
    # Overall
    overall_score: float = Field(default=0.0, ge=0, le=1, description="Weighted overall match")
    match_percentage: float = Field(default=0.0, ge=0, le=100, description="Match percentage (0-100)")
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow, description="When calculated")
    matching_model_version: str = Field(default="1.0", description="Matching model version")
    
    class Config:
        frozen = False
    
    def compute_overall_score(
        self,
        skill_weight: float = 0.35,
        experience_weight: float = 0.35,
        education_weight: float = 0.20,
        location_weight: float = 0.05,
        language_weight: float = 0.05
    ) -> float:
        """
        Compute weighted overall score
        Default weights: skills 35%, experience 35%, education 20%, location 5%, language 5%
        """
        self.overall_score = (
            self.skill_match * skill_weight +
            self.experience_match * experience_weight +
            self.education_fit * education_weight +
            self.location_fit * location_weight +
            self.language_fit * language_weight
        )
        self.match_percentage = round(self.overall_score * 100, 1)
        return self.overall_score


class Assessment(BaseModel):
    """Assessment result"""
    assessment_id: str = Field(..., description="Unique assessment ID")
    candidate_id: str = Field(..., description="Candidate ID")
    job_id: str = Field(..., description="Job ID")
    profile: 'CandidateProfile' = Field(..., description="Candidate profile")
    job: 'JobDescription' = Field(..., description="Job description")
    matching_score: Optional[MatchingScore] = Field(None, description="Detailed matching score")
    scores: 'ScoreBreakdown' = Field(default_factory=lambda: ScoreBreakdown(), description="Score breakdown")
    decision: DecisionType = Field(..., description="Assessment decision")
    decision_reasoning: str = Field(..., description="Why this decision was made")
    risk_flags: List['RiskFlag'] = Field(default_factory=list, description="Identified risks")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    assessed_at: datetime = Field(default_factory=datetime.utcnow, description="Assessment timestamp")
    model_version: str = Field(..., description="Model version used")
    
    class Config:
        frozen = False
