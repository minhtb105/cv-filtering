"""Cache key generation strategies."""

from typing import List, Optional


class CacheKeys:
    """Generate consistent cache keys across the system."""
    
    PREFIX = "cvai"
    
    @staticmethod
    def cv_extraction(cv_id: str) -> str:
        """Key for CV extraction data."""
        return f"{CacheKeys.PREFIX}:extraction:cv:{cv_id}"
    
    @staticmethod
    def cv_metadata(cv_id: str) -> str:
        """Key for CV metadata."""
        return f"{CacheKeys.PREFIX}:cv:metadata:{cv_id}"
    
    @staticmethod
    def score_latest(cv_id: str, jd_id: str) -> str:
        """Key for latest score."""
        return f"{CacheKeys.PREFIX}:score:latest:{cv_id}:{jd_id}"
    
    @staticmethod
    def score_versioned(cv_id: str, cv_version: int, jd_id: str, jd_version: int) -> str:
        """Key for versioned score."""
        return f"{CacheKeys.PREFIX}:score:v{cv_version}:{cv_id}:jdv{jd_version}:{jd_id}"
    
    @staticmethod
    def score_history(cv_id: str, jd_id: str) -> str:
        """Key for score history."""
        return f"{CacheKeys.PREFIX}:score:history:{cv_id}:{jd_id}"
    
    @staticmethod
    def jd_extraction(jd_id: str) -> str:
        """Key for JD extraction data."""
        return f"{CacheKeys.PREFIX}:extraction:jd:{jd_id}"
    
    @staticmethod
    def jd_metadata(jd_id: str) -> str:
        """Key for JD metadata."""
        return f"{CacheKeys.PREFIX}:jd:metadata:{jd_id}"
    
    @staticmethod
    def interview_result(cv_id: str) -> str:
        """Key for interview result."""
        return f"{CacheKeys.PREFIX}:interview:{cv_id}"
    
    @staticmethod
    def comparison(cv_id: str, jd_id: str) -> str:
        """Key for comparison result."""
        return f"{CacheKeys.PREFIX}:comparison:{cv_id}:{jd_id}"
    
    @staticmethod
    def ranking(jd_id: str) -> str:
        """Key for ranking list."""
        return f"{CacheKeys.PREFIX}:ranking:{jd_id}"
    
    @staticmethod
    def cv_pattern(cv_id: str) -> str:
        """Pattern for all CV-related keys."""
        return f"{CacheKeys.PREFIX}:*:{cv_id}*"
    
    @staticmethod
    def jd_pattern(jd_id: str) -> str:
        """Pattern for all JD-related keys."""
        return f"{CacheKeys.PREFIX}:*:{jd_id}*"
    
    @staticmethod
    def score_pattern(cv_id: str = None, jd_id: str = None) -> str:
        """Pattern for score-related keys."""
        if cv_id and jd_id:
            return f"{CacheKeys.PREFIX}:score:*:{cv_id}:{jd_id}"
        elif cv_id:
            return f"{CacheKeys.PREFIX}:score:*:{cv_id}:*"
        elif jd_id:
            return f"{CacheKeys.PREFIX}:score:*:*:{jd_id}"
        return f"{CacheKeys.PREFIX}:score:*"
