"""Interview repository for managing interview results."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.repository.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class InterviewRepository(BaseRepository):
    """Repository for interview data."""
    
    def __init__(self, storage_backend: Optional[Dict[str, Any]] = None):
        """Initialize interview repository."""
        super().__init__(storage_backend)
        self.interviews = {}  # cv_id -> [interview results]
    
    def get(self, key: str) -> Optional[Any]:
        """Get latest interview result for CV."""
        results = self.interviews.get(key, [])
        return results[-1] if results else None
    
    def set(self, key: str, value: Any) -> bool:
        """Store interview result."""
        try:
            if key not in self.interviews:
                self.interviews[key] = []
            
            entry = {
                **value,
                "recorded_at": datetime.utcnow().isoformat(),
                "sequence": len(self.interviews[key]) + 1,
            }
            
            self.interviews[key].append(entry)
            logger.info(f"Stored interview result for CV {key}")
            return True
        except Exception as e:
            logger.error(f"Error storing interview result for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete all interview results for CV."""
        try:
            if key in self.interviews:
                del self.interviews[key]
            logger.info(f"Deleted interview results for CV {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting interview results for {key}: {e}")
            return False
    
    def list_keys(self) -> List[str]:
        """List all CV IDs with interviews."""
        return list(self.interviews.keys())
    
    def get_all_interviews(self, cv_id: str) -> List[Dict[str, Any]]:
        """Get all interview results for CV."""
        return self.interviews.get(cv_id, [])
    
    def get_interview_by_sequence(self, cv_id: str, sequence: int) -> Optional[Dict[str, Any]]:
        """Get interview result by sequence number."""
        interviews = self.interviews.get(cv_id, [])
        if 0 < sequence <= len(interviews):
            return interviews[sequence - 1]
        return None
    
    def get_latest_scores(self, cv_id: str) -> Optional[Dict[str, float]]:
        """Get latest technical and soft skills scores."""
        interview = self.get(cv_id)
        if interview:
            return {
                "technical_score": interview.get("technical_score", 0),
                "soft_skills_score": interview.get("soft_skills_score", 0),
                "cultural_fit_score": interview.get("cultural_fit_score", 0),
            }
        return None
