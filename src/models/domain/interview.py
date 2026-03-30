"""
Interview Models

Models for interview feedback and decision results in the CV Intelligence Platform.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from src.models.domain.assessment import MatchingScore
from src.models.validation.enums import InterviewRound, InterviewDecision


class InterviewFeedback(BaseModel):
    """Interview feedback"""
    interview_id: str = Field(..., description="Interview ID")
    assessment_id: str = Field(..., description="Assessment ID")
    round: InterviewRound = Field(..., description="Interview round")
    interviewer: str = Field(..., description="Interviewer name")
    decision: InterviewDecision = Field(..., description="Pass/fail decision")
    technical_score: Optional[float] = Field(None, ge=0, le=1, description="Technical score")
    communication_score: Optional[float] = Field(None, ge=0, le=1, description="Communication score")
    culture_fit_score: Optional[float] = Field(None, ge=0, le=1, description="Culture fit")
    strengths: List[str] = Field(default_factory=list, description="Strengths observed")
    weaknesses: List[str] = Field(default_factory=list, description="Areas for improvement")
    notes: Optional[str] = Field(None, description="Additional notes")
    conducted_at: datetime = Field(default_factory=datetime.utcnow, description="Interview date")
    
    class Config:
        frozen = False


class DecisionResult(BaseModel):
    """Decision result with reasoning"""
    decision: str = Field(..., description="Final decision")
    reasoning: str = Field(..., description="Decision reasoning")
    score_breakdown: Optional['MatchingScore'] = Field(None, description="Score details")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    next_steps: List[str] = Field(default_factory=list, description="Suggested next steps")
    
    class Config:
        frozen = False
