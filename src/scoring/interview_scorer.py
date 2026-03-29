"""Interview scoring based on technical and soft skills."""

from typing import Any, Dict, Optional
import logging

from src.scoring.base_scorer import BaseScorer

logger = logging.getLogger(__name__)


class InterviewScorer(BaseScorer):
    """Score based on interview performance."""
    
    def __init__(self, weight: float = 0.15):
        """Initialize interview scorer."""
        super().__init__("interview_evaluator", weight)
    
    def score(self, cv_data: Dict[str, Any], jd_data: Dict[str, Any], interview_result: Optional[Dict[str, Any]] = None) -> float:
        """Score based on interview results."""
        if not interview_result:
            return 50  # No interview data
        
        technical_score = interview_result.get("technical_score", 0)
        soft_skills_score = interview_result.get("soft_skills_score", 0)
        cultural_fit_score = interview_result.get("cultural_fit_score", 0)
        
        # Weighted average of interview components
        score = (
            technical_score * 0.4 +
            soft_skills_score * 0.3 +
            cultural_fit_score * 0.3
        )
        
        return self.validate_score(score)
    
    def score_technical(self, interview_result: Dict[str, Any]) -> float:
        """Get technical score from interview."""
        return interview_result.get("technical_score", 0)
    
    def score_soft_skills(self, interview_result: Dict[str, Any]) -> float:
        """Get soft skills score from interview."""
        return interview_result.get("soft_skills_score", 0)
    
    def score_cultural_fit(self, interview_result: Dict[str, Any]) -> float:
        """Get cultural fit score from interview."""
        return interview_result.get("cultural_fit_score", 0)
    
    def has_interview_data(self, interview_result: Optional[Dict[str, Any]]) -> bool:
        """Check if interview data is available."""
        return interview_result is not None and len(interview_result) > 0
