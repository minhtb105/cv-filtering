"""Education scoring based on degree alignment and certifications."""

from typing import Any, Dict
import logging

from src.scoring.base_scorer import BaseScorer

logger = logging.getLogger(__name__)


class EducationScorer(BaseScorer):
    """Score based on education alignment."""
    
    def __init__(self, weight: float = 0.2):
        """Initialize education scorer."""
        super().__init__("education_aligner", weight)
    
    def score(self, cv_data: Dict[str, Any], jd_data: Dict[str, Any]) -> float:
        """Score based on education fit."""
        cv_degrees = self._extract_degrees(cv_data)
        cv_certs = self._extract_certifications(cv_data)
        
        jd_required_degree = self._extract_required_degree(jd_data)
        jd_preferred_certs = self._extract_preferred_certs(jd_data)
        
        # Score components
        degree_score = self._score_degrees(cv_degrees, jd_required_degree)
        cert_score = self._score_certifications(cv_certs, jd_preferred_certs)
        
        # Weighted average
        score = (degree_score * 0.7 + cert_score * 0.3)
        
        return self.validate_score(score)
    
    def _extract_degrees(self, cv_data: Dict[str, Any]) -> list:
        """Extract education degrees from CV."""
        education = cv_data.get("education", [])
        if isinstance(education, dict):
            degrees = education.get("degrees", [])
        else:
            degrees = education if isinstance(education, list) else []
        
        degree_list = []
        for edu in degrees:
            if isinstance(edu, dict):
                degree_list.append(edu.get("degree_type", "").lower())
            else:
                degree_list.append(str(edu).lower())
        
        return degree_list
    
    def _extract_certifications(self, cv_data: Dict[str, Any]) -> list:
        """Extract certifications from CV."""
        certs = cv_data.get("certifications", [])
        if isinstance(certs, list):
            return [c.lower() if isinstance(c, str) else c.get("name", "").lower() for c in certs]
        return []
    
    def _extract_required_degree(self, jd_data: Dict[str, Any]) -> str:
        """Extract required degree from JD."""
        degree = jd_data.get("required_degree", "")
        
        return degree.lower() if isinstance(degree, str) else ""    
    
    def _extract_preferred_certs(self, jd_data: Dict[str, Any]) -> list:
        """Extract preferred certifications from JD."""
        certs = jd_data.get("preferred_certifications", [])
        if isinstance(certs, list):
            return [c.lower() for c in certs if isinstance(c, str)]
        
        return []

    def _normalize_degree(self, degree: str) -> str:
        """Normalize degree string to hierarchy key."""
        degree = degree.lower().strip()
        
        if any(x in degree for x in ["phd", "ph.d", "doctorate"]):
            return "phd"
        
        if any(x in degree for x in ["master", "mba", "ms ", "m.s."]):
            return "master"
        
        if any(x in degree for x in ["bachelor", "bs ", "b.s.", "ba ", "b.a."]):
            return "bachelors"
        
        if "associate" in degree:
            return "associate"
        
        if "high school" in degree or "ged" in degree:
            return "high school"
        
        return degree
    
    def _score_degrees(self, cv_degrees: list, jd_required: str) -> float:
        """Score based on degree match."""
        degree_hierarchy = {
            "phd": 4,
            "master": 3,
            "bachelors": 2,
            "associate": 1,
            "high school": 0,
        }
        
        if not jd_required:
            return 70  # No specific requirement
        
        jd_level = degree_hierarchy.get(self._normalize_degree(jd_required), 0)
        
        # Check if CV has required degree or higher
        for cv_degree in cv_degrees:
            cv_level = degree_hierarchy.get(self._normalize_degree(cv_degree), 0)
            if cv_level >= jd_level:
                return 100 if cv_level == jd_level else 95
        
        # Partial credit if close
        if cv_degrees:
            best_match = max(degree_hierarchy.get(self._normalize_degree(d), 0) for d in cv_degrees)
            if best_match == jd_level - 1:
                return 70
        
        return 30
    
    def _score_certifications(self, cv_certs: list, jd_preferred: list) -> float:
        """Score based on certification match."""
        if not jd_preferred:
            if cv_certs:
                return 60  # Bonus for having certs when not required
            return 50
        
        matched = 0
        for preferred in jd_preferred:
            if any(preferred in cv_cert for cv_cert in cv_certs):
                matched += 1
        
        match_percentage = (matched / len(jd_preferred)) * 100
        return match_percentage
