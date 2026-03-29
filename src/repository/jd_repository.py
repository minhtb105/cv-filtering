"""Job Description repository for managing JD versions."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.repository.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class JDRepository(BaseRepository):
    """Repository for job description data."""
    
    def __init__(self, storage_backend: Optional[Dict[str, Any]] = None):
        """Initialize JD repository."""
        super().__init__(storage_backend)
        self.jd_current = {}     # jd_id -> current JD
        self.jd_versions = {}    # jd_id -> [versions]
        self.jd_metadata = {}    # jd_id -> metadata
    
    def get(self, key: str) -> Optional[Any]:
        """Get current JD by ID."""
        return self.jd_current.get(key)
    
    def set(self, key: str, value: Any) -> bool:
        """Store JD data."""
        try:
            self.jd_current[key] = {
                **value,
                "updated_at": datetime.utcnow().isoformat(),
            }
            self._track_version(key, value)
            logger.info(f"Stored JD for {key}")
            return True
        except Exception as e:
            logger.error(f"Error storing JD {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete JD data."""
        try:
            if key in self.jd_current:
                del self.jd_current[key]
            if key in self.jd_versions:
                del self.jd_versions[key]
            if key in self.jd_metadata:
                del self.jd_metadata[key]
            logger.info(f"Deleted JD {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting JD {key}: {e}")
            return False
    
    def list_keys(self) -> List[str]:
        """List all JD IDs."""
        return list(self.jd_current.keys())
    
    def get_versions(self, jd_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a JD."""
        return self.jd_versions.get(jd_id, [])
    
    def get_latest_version(self, jd_id: str) -> Optional[int]:
        """Get latest version number for JD."""
        versions = self.get_versions(jd_id)
        if versions:
            return versions[-1].get("version", 0)
        return 0
    
    def _track_version(self, jd_id: str, value: Dict[str, Any]):
        """Track JD version."""
        if jd_id not in self.jd_versions:
            self.jd_versions[jd_id] = []
        
        latest = self.get_latest_version(jd_id)
        
        self.jd_versions[jd_id].append({
            "version": latest + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "checksum": hash(str(value)),
            "size": len(str(value)),
        })
    
    def get_jd_by_version(self, jd_id: str, version: int) -> Optional[Dict[str, Any]]:
        """Get JD at specific version."""
        versions = self.get_versions(jd_id)
        if version <= len(versions):
            return {
                **self.jd_current.get(jd_id, {}),
                "version": version,
                "version_info": versions[version - 1],
            }
        return None
