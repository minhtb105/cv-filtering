"""CV repository for managing CV metadata and versions."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.repository.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CVRepository(BaseRepository):
    """Repository for CV data."""
    
    def __init__(self, storage_backend: Optional[Dict[str, Any]] = None):
        """Initialize CV repository."""
        super().__init__(storage_backend)
        self.cv_versions = {}  # cv_id -> [versions]
        self.cv_metadata = {}   # cv_id -> metadata
    
    def get(self, key: str) -> Optional[Any]:
        """Get CV by ID."""
        return self.cv_metadata.get(key)
    
    def set(self, key: str, value: Any) -> bool:
        """Store CV data."""
        try:
            self.cv_metadata[key] = {
                **value,
                "updated_at": datetime.now(datetime.timezone.utc).isoformat(),
            }
            self._track_version(key, value)
            logger.info(f"Stored CV metadata for {key}.")
            return True
        except Exception as e:
            logger.error(f"Error storing CV {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete CV data."""
        try:
            if key in self.cv_metadata:
                del self.cv_metadata[key]
            if key in self.cv_versions:
                del self.cv_versions[key]
            logger.info(f"Deleted CV {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting CV {key}: {e}")
            return False
    
    def list_keys(self) -> List[str]:
        """List all CV IDs."""
        return list(self.cv_metadata.keys())
    
    def get_versions(self, cv_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a CV."""
        return self.cv_versions.get(cv_id, [])
    
    def get_latest_version(self, cv_id: str) -> Optional[int]:
        """Get latest version number for CV."""
        versions = self.get_versions(cv_id)
        if versions:
            return versions[-1].get("version", 0)
        return 0
    
    def _track_version(self, cv_id: str, value: Dict[str, Any]):
        """Track CV version."""
        if cv_id not in self.cv_versions:
            self.cv_versions[cv_id] = []
        
        latest = self.get_latest_version(cv_id)
        
        self.cv_versions[cv_id].append({
            "version": latest + 1,
            "timestamp": datetime.now(datetime.timezone.utc).isoformat(),
            "checksum": hash(str(value)),
            "size": len(str(value)),
        })
    
    def get_cv_by_version(self, cv_id: str, version: int) -> Optional[Dict[str, Any]]:
        """Get CV at specific version."""
        versions = self.get_versions(cv_id)
        if version <= len(versions):
            return {
                **self.cv_metadata.get(cv_id, {}),
                "version": version,
                "version_info": versions[version - 1],
            }
        return None
