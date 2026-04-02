"""Experience scoring based on years, seniority, and progression."""

from typing import Any, Dict
import logging

from src.scoring.base_scorer import BaseScorer

logger = logging.getLogger(__name__)


class ExperienceScorer(BaseScorer):
    """Score based on experience: years, seniority, progression."""
    
    def __init__(self, weight: float = 0.35):
        """Initialize experience scorer."""
        super().__init__("experience_evaluator", weight)
    
    def score(self, cv_data: Dict[str, Any], jd_data: Dict[str, Any]) -> float:
        """Score based on experience fit."""
        cv_years = self._extract_years(cv_data)
        cv_seniority = self._extract_seniority(cv_data)
        
        jd_min_years = self._extract_min_years(jd_data)
        jd_seniority = self._extract_required_seniority(jd_data)
        
        # Score components
        years_score = self._score_years(cv_years, jd_min_years)
        seniority_score = self._score_seniority(cv_seniority, jd_seniority)
        progression_score = self._score_progression(cv_data)
        
        # Weighted average
        score = (years_score * 0.4 + seniority_score * 0.4 + progression_score * 0.2)
        
        return self.validate_score(score)
    
    def _extract_years(self, cv_data: Dict[str, Any]) -> float:
        """Extract total years of experience from CV."""
        years = cv_data.get("total_experience_years", 0)
        if years is None:
            return 0.0
        
        try:
            return float(years)
        except (TypeError, ValueError):
            return 0.0    
        
    def _extract_seniority(self, cv_data: Dict[str, Any]) -> str:
        """Extract seniority level from CV."""
        seniority = cv_data.get("seniority_level") or "mid"
        
        return seniority.lower()
    
    def _extract_min_years(self, jd_data: Dict[str, Any]) -> float:
        """Extract minimum years required from JD."""
        years = jd_data.get("min_experience_years", 0)
        if isinstance(years, str):
            try:
                return float(years)
            except ValueError:
                return 0
        return float(years)
    
    def _extract_required_seniority(self, jd_data: Dict[str, Any]) -> str:
        """Extract required seniority from JD."""
        seniority = jd_data.get("required_seniority", "mid")
        return seniority.lower()
    
    def _score_years(self, cv_years: float, jd_min_years: float) -> float:
        """Score based on years of experience."""
        cv_years = max(0, cv_years)
        jd_min_years = max(0, jd_min_years)
        
        if jd_min_years == 0:
            return 50  # No requirement
        
        if cv_years < jd_min_years:
            return (cv_years / jd_min_years) * 70  # Partial credit
        elif cv_years == jd_min_years:
            return 80
        else:
            # Bonus for extra experience, but cap at 100
            excess = min(cv_years - jd_min_years, 10)
            return min(100, 80 + (excess / 10) * 20)
    
    def _score_seniority(self, cv_seniority: str, jd_seniority: str) -> float:
        """Score based on seniority level."""
        level_map = {
            "junior": 1,
            "mid": 2,
            "senior": 3,
            "lead": 4,
            "manager": 5,
        }
        
        cv_level = level_map.get(cv_seniority, 2)
        jd_level = level_map.get(jd_seniority, 2)
        
        if cv_level < jd_level:
            return (cv_level / jd_level) * 70
        elif cv_level == jd_level:
            return 85
        else:
            excess = min(cv_level - jd_level, 3)
            return min(100, 85 + (excess / 3) * 15)
    def _score_progression(self, cv_data: Dict[str, Any]) -> float:
        """Score based on career progression."""
        # Check for increasing responsibility
        progression = cv_data.get("career_progression", 0)
        if not isinstance(progression, (int, float)):
            try:
                progression = float(progression) if progression else 0
            except (TypeError, ValueError):
                progression = 0
        
        if progression > 0:
            return min(100, 50 + (progression * 10))
        
        return 50 
