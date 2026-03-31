"""Skill matching scorer."""

from typing import Any, Dict
from difflib import SequenceMatcher
import logging

from src.scoring.base_scorer import BaseScorer

logger = logging.getLogger(__name__)


class SkillScorer(BaseScorer):
    """Score based on skill matching between CV and JD."""
    
    def __init__(self, weight: float = 0.3):
        """Initialize skill scorer."""
        super().__init__("skill_matcher", weight)
    
    def score(self, cv_data: Dict[str, Any], jd_data: Dict[str, Any]) -> float:
        """Score based on skill overlap."""
        cv_skills = self._extract_skills(cv_data)
        jd_skills = self._extract_skills(jd_data)
        
        if not jd_skills:
            return self.validate_score(50)  # Default if no skills in JD        
        
        # Calculate skill match percentage
        matched_count = 0
        for jd_skill in jd_skills:
            for cv_skill in cv_skills:
                similarity = self._calculate_similarity(jd_skill.lower(), cv_skill.lower())
                if similarity > 0.7:  # 70% match threshold
                    matched_count += 1
                    break
        
        match_percentage = (matched_count / len(jd_skills)) * 100
        
        # Bonus for extra skills
        extra_skills = max(0, len(cv_skills) - matched_count)
        bonus = min(10, extra_skills * 2)
        
        score = match_percentage + bonus        
        
        return self.validate_score(score)
    
    def _extract_skills(self, data: Dict[str, Any]) -> list:
        """Extract skills from CV or JD data."""
        # Try multiple possible field names
        for field in ["skills", "technical_skills", "skill_set", "competencies"]:
            if field in data:
                skills = data[field]
                if isinstance(skills, list):
                    return skills
                elif isinstance(skills, str):
                    return [s.strip() for s in skills.split(",")]
        
        return []
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings."""
        return SequenceMatcher(None, str1, str2).ratio()
