"""Base scorer for composable scoring system."""

from abc import ABC, abstractmethod
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class BaseScorer(ABC):
    """Abstract base class for all scorers."""
    
    def __init__(self, name: str, weight: float = 1.0):
        """Initialize scorer."""
        self.name = name
        self.weight = weight
    
    @abstractmethod
    def score(self, cv_data: Dict[str, Any], jd_data: Dict[str, Any]) -> float:
        """Score CV against JD. Returns 0-100."""
        pass
    
    def validate_score(self, score: float) -> float:
        """Ensure score is between 0-100."""
        return max(0, min(100, score))
    
    def get_detailed_score(self, cv_data: Dict[str, Any], jd_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed scoring breakdown."""
        base_score = self.score(cv_data, jd_data)
        return {
            "scorer": self.name,
            "score": base_score,
            "weighted_score": base_score * self.weight,
            "weight": self.weight,
        }
