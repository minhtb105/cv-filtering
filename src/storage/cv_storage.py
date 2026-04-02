"""
CV Storage - Unified storage interface
Combines RAW and NORMALIZED storage
"""

from typing import Optional, List, Dict, Any
import logging
from src.storage.raw_storage import RawStorage
from src.storage.normalized_storage import NormalizedStorage
from src.schemas import CVVersion


logger = logging.getLogger(__name__)

class CVStorage:
    """Unified CV storage interface"""

    def __init__(self):
        self.raw = RawStorage()
        self.normalized = NormalizedStorage()

    def save_raw(self, cv_id: str, version: CVVersion) -> str:
        """Save raw CV version"""
        return self.raw.insert(cv_id, version)

    def save_normalized(self, cv_id: str, version: CVVersion) -> str:
        """Save normalized CV version"""
        return self.normalized.insert(cv_id, version)

    def get_cv(self, cv_id: str, normalized: bool = False) -> Optional[Dict[str, Any]]:
        """Get CV by ID"""
        if normalized:
            return self.normalized.find_latest(cv_id)
        return self.raw.find_latest(cv_id)

    def get_all_versions(self, cv_id: str, normalized: bool = False) -> List[Dict[str, Any]]:
        """Get all versions of a CV"""
        if normalized:
            return self.normalized.find_by_cv_id(cv_id)
        return self.raw.find_by_cv_id(cv_id)

    def search_by_skill(self, skill: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search CVs by skill (uses normalized data)"""
        return self.normalized.search_by_skill(skill, limit)

    def search_by_text(self, text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search CVs by text (uses normalized data)"""
        return self.normalized.search_by_text(text, limit)

    def delete_cv(self, cv_id: str) -> int:
        """Delete CV from both storage.
        
        Note: Deletion is not atomic. If one storage fails, partial deletion may occur.
        """
        raw_count = 0
        norm_count = 0
        try:
            raw_count = self.raw.delete(cv_id)
        except Exception as e:
            logger.error("Failed to delete cv_id=%s from raw storage: %s", cv_id, e)
            
        try:
            norm_count = self.normalized.delete(cv_id)
        except Exception as e:
            logger.error("Failed to delete cv_id=%s from normalized storage: %s", cv_id, e)
            
        return raw_count + norm_count

    def list_all_cvs(self, normalized: bool = False, limit: int = 100) -> List[str]:
        """List all unique CV IDs"""
        collection = self.normalized.collection if normalized else self.raw.collection
        cv_ids = collection.distinct("cv_id")
        return cv_ids[:limit]


__all__ = ["CVStorage"]
