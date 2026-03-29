"""
Raw CV Data Storage
Stores original extracted CV data before normalization/translation
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from src.storage.db_manager import db_manager
from src.schemas import CVVersion


class RawStorage:
    """Storage for RAW CV data"""

    COLLECTION_NAME = "cvs_raw"

    def __init__(self):
        self.collection = db_manager.get_db()[self.COLLECTION_NAME]

    def insert(self, cv_id: str, version: CVVersion) -> str:
        """Insert raw CV data"""
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
        }
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def find_by_cv_id(self, cv_id: str) -> List[Dict[str, Any]]:
        """Find all raw CV versions by cv_id"""
        cursor = self.collection.find({"cv_id": cv_id}).sort("extracted_at", -1)
        return list(cursor)

    def find_latest(self, cv_id: str) -> Optional[Dict[str, Any]]:
        """Find latest raw CV version"""
        return self.collection.find_one(
            {"cv_id": cv_id},
            sort=[("extracted_at", -1)]
        )

    def update_translation_status(self, cv_id: str, version: str, status: str):
        """Update translation status"""
        self.collection.update_one(
            {"cv_id": cv_id, "version": version},
            {"$set": {"translation_status": status}}
        )

    def delete(self, cv_id: str) -> int:
        """Delete all versions of a CV"""
        result = self.collection.delete_many({"cv_id": cv_id})
        return result.deleted_count


__all__ = ["RawStorage"]
