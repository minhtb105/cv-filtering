"""
Normalized CV Data Storage
Stores translated and normalized CV data
"""

import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from src.storage.db_manager import db_manager
from src.schemas import CVVersion


class NormalizedStorage:
    """Storage for NORMALIZED CV data"""

    COLLECTION_NAME = "cvs_normalized"
    MAX_QUERY_LEN = 100  # limit input length to prevent abuse

    def __init__(self):
        self.collection = db_manager.get_db()[self.COLLECTION_NAME]
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create indexes for better query performance"""
        self.collection.create_index("cv_id")
        self.collection.create_index("extracted_at")
        self.collection.create_index("profile.skills.name")
        self.collection.create_index("normalized_text")
        self.collection.create_index("profile.summary")

    def _sanitize_query(self, text: str) -> Optional[str]:
        """
        Sanitize user input for safe regex usage:
        - strip whitespace
        - limit length
        - escape regex chars
        """
        if not text:
            return None

        text = text.strip()
        if not text:
            return None

        if len(text) > self.MAX_QUERY_LEN:
            text = text[:self.MAX_QUERY_LEN]

        return re.escape(text)

    def insert(self, cv_id: str, version: CVVersion) -> str:
        """Insert normalized CV data"""
        doc = {
            "cv_id": cv_id,
            "version": version.version,
            "source_type": version.source_type,
            "raw_text": version.raw_text,
            "normalized_text": version.normalized_text,
            "profile": version.profile.model_dump() if version.profile else None,
            "language": version.language,
            "translation_status": version.translation_status,
            "extraction_confidence": version.extraction_confidence,
            "extracted_at": version.extracted_at,
            "translated_at": datetime.now(timezone.utc),
        }
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def find_by_cv_id(self, cv_id: str) -> List[Dict[str, Any]]:
        """Find all normalized CV versions by cv_id"""
        cursor = self.collection.find({"cv_id": cv_id}).sort("extracted_at", -1)
        return list(cursor)

    def find_latest(self, cv_id: str) -> Optional[Dict[str, Any]]:
        """Find latest normalized CV version"""
        return self.collection.find_one(
            {"cv_id": cv_id},
            sort=[("extracted_at", -1)]
        )

    def search_by_skill(self, skill: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search CVs by skill (safe regex)"""
        escaped_skill = self._sanitize_query(skill)
        if not escaped_skill:
            return []

        cursor = self.collection.find(
            {"profile.skills.name": {"$regex": escaped_skill, "$options": "i"}}
        ).limit(limit)

        return list(cursor)

    def search_by_text(self, text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search CVs by text content (safe regex)"""
        escaped_text = self._sanitize_query(text)
        if not escaped_text:
            return []

        cursor = self.collection.find(
            {"$or": [
                {"normalized_text": {"$regex": escaped_text, "$options": "i"}},
                {"profile.summary": {"$regex": escaped_text, "$options": "i"}},
            ]}
        ).limit(limit)

        return list(cursor)

    def delete(self, cv_id: str) -> int:
        """Delete all normalized versions of a CV"""
        result = self.collection.delete_many({"cv_id": cv_id})
        return result.deleted_count


__all__ = ["NormalizedStorage"]
