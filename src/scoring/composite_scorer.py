"""Composite scorer combining all scoring components."""

from typing import Any, Dict, Optional, List
import logging

from src.scoring.skill_scorer import SkillScorer
from src.scoring.experience_scorer import ExperienceScorer
from src.scoring.education_scorer import EducationScorer
from src.scoring.interview_scorer import InterviewScorer

logger = logging.getLogger(__name__)


class CompositeScorer:
    """Orchestrate multiple scorers into a composite score."""
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
    ):
        """Initialize composite scorer."""
        default_weights = {
            "skill": 0.3,
            "experience": 0.35,
            "education": 0.2,
            "interview": 0.15,
        }
        
        self.weights = {**default_weights, **(weights or {})} 
        for key, value in self.weights.items():
            if value < 0:
                raise ValueError(f"Weight for '{key}' must be non-negative, got {value}")
        
        self.skill_scorer = SkillScorer(self.weights.get("skill", 0.3))
        self.experience_scorer = ExperienceScorer(self.weights.get("experience", 0.35))
        self.education_scorer = EducationScorer(self.weights.get("education", 0.2))
        self.interview_scorer = InterviewScorer(self.weights.get("interview", 0.15))
    
    def score(
        self,
        cv_data: Dict[str, Any],
        jd_data: Dict[str, Any],
        interview_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Calculate composite score from all components."""
        # Get individual scores
        skill_score = self.skill_scorer.score(cv_data, jd_data)
        experience_score = self.experience_scorer.score(cv_data, jd_data)
        education_score = self.education_scorer.score(cv_data, jd_data)
        interview_score = self.interview_scorer.score(cv_data, jd_data, interview_result)
        
        # Calculate weighted composite
        skill_weighted = skill_score * self.weights["skill"]
        experience_weighted = experience_score * self.weights["experience"]
        education_weighted = education_score * self.weights["education"]
        interview_weighted = interview_score * self.weights["interview"]
        
        composite_score = (
            skill_weighted +
            experience_weighted +
            education_weighted +
            interview_weighted
        )
        
        return {
            "skill_score": skill_score,
            "experience_score": experience_score,
            "education_score": education_score,
            "interview_score": interview_score,
            "composite_score": min(100, max(0, composite_score)),
            "breakdown": {
                "skill_weight": self.weights["skill"],
                "experience_weight": self.weights["experience"],
                "education_weight": self.weights["education"],
                "interview_weight": self.weights["interview"],
            },
            "has_interview": interview_result is not None,
        }
    
    def update_weights(self, weights: Dict[str, float]):
        """Update scoring weights."""
        default_weights = {
            "skill": 0.3,
            "experience": 0.35,
            "education": 0.2,
            "interview": 0.15,
        }

        self.weights = {**default_weights, **weights}
        
        for key, value in self.weights.items():
            if value < 0:
                raise ValueError(f"Weight for '{key}' must be non-negative, got {value}")
        
        self.skill_scorer.weight = self.weights["skill"]
        self.experience_scorer.weight = self.weights["experience"]
        self.education_scorer.weight = self.weights["education"]
        self.interview_scorer.weight = self.weights["interview"]
        
        logger.info(f"Updated scoring weights: {weights}")
    
    def get_weights(self) -> Dict[str, float]:
        """Get current scoring weights."""
        return self.weights
