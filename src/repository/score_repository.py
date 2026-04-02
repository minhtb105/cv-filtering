"""Score repository for managing scores and history."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from src.repository.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ScoreRepository(BaseRepository):
    """Repository for score data and history."""
    
    def __init__(self, storage_backend: Optional[Dict[str, Any]] = None):
        """Initialize score repository."""
        super().__init__(storage_backend)
        self.scores = {}           # {cv_id: jd_id} -> latest score
        self.score_history = {}    # {cv_id: jd_id} -> [scores]
        self.score_metadata = {}   # {cv_id: jd_id} -> metadata
    
    def get(self, key: str) -> Optional[Any]:
        """Get latest score by key."""
        return self.scores.get(key)
    
    def set(self, key: str, value: Dict[str, Any]) -> bool:
        """Store score."""
        try:
            self.scores[key] = {
                **value,
                "stored_at": datetime.now(timezone.utc).isoformat(),
            }
            self._track_history(key, value)
            logger.info(f"Stored score for {key}")
            return True
        except Exception as e:
            logger.error(f"Error storing score for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete score."""
        try:
            if key in self.scores:
                del self.scores[key]
            if key in self.score_history:
                del self.score_history[key]
            if key in self.score_metadata:
                del self.score_metadata[key]
            logger.info(f"Deleted score for {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting score for {key}: {e}")
            return False
    
    def list_keys(self) -> List[str]:
        """List all score keys."""
        return list(self.scores.keys())
    
    def get_history(self, key: str) -> List[Dict[str, Any]]:
        """Get score history for key."""
        return self.score_history.get(key, [])
    
    def _track_history(self, key: str, score: Dict[str, Any]):
        """Track score in history."""
        if key not in self.score_history:
            self.score_history[key] = []
        
        history_entry = {
            **score,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "sequence": len(self.score_history[key]) + 1,
        }
        
        self.score_history[key].append(history_entry)
        
        # Update metadata
        if key not in self.score_metadata:
            self.score_metadata[key] = {
                "first_scored": history_entry["recorded_at"],
                "score_count": 0,
            }
        
        self.score_metadata[key]["last_scored"] = history_entry["recorded_at"]
        self.score_metadata[key]["score_count"] += 1
    
    def invalidate_scores_for_cv(self, cv_id: str) -> int:
        """Invalidate all scores for a CV."""
        keys_to_delete = [k for k in self.scores.keys() if k.startswith(f"{cv_id}:")]
        count = 0
        
        for key in keys_to_delete:
            if self.delete(key):
                count += 1
        
        logger.info(f"Invalidated {count} scores for CV {cv_id}")
        return count
    
    def invalidate_scores_for_jd(self, jd_id: str) -> int:
        """Invalidate all scores for a JD."""
        keys_to_delete = [k for k in self.scores.keys() if k.endswith(f":{jd_id}")]
        count = 0
        
        for key in keys_to_delete:
            if self.delete(key):
                count += 1
        
        logger.info(f"Invalidated {count} scores for JD {jd_id}")
        return count
    
    def get_scores_for_cv(self, cv_id: str) -> List[Dict[str, Any]]:
        """Get all scores for a CV."""
        return [
            self.scores[k] for k in self.scores.keys()
            if k.startswith(f"{cv_id}:")
        ]
    
    def get_scores_for_jd(self, jd_id: str) -> List[Dict[str, Any]]:
        """Get all scores for a JD."""
        return [
            self.scores[k] for k in self.scores.keys()
            if k.endswith(f":{jd_id}")
        ]
