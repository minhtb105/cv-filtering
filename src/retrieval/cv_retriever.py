"""CV retriever with cache-first access pattern."""

import logging
from typing import Any, Dict, List, Optional

from src.cache import CacheClient, CacheKeys
from src.repository import CVRepository

logger = logging.getLogger(__name__)


class CVRetriever:
    """Retrieve CV data with cache-first pattern."""
    
    def __init__(
        self,
        cache_client: CacheClient,
        cv_repository: CVRepository,
    ):
        """Initialize CV retriever."""
        self.cache_client = cache_client
        self.cv_repository = cv_repository
    
    def get_cv(self, cv_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get CV data (cache-first)."""
        # Try cache first
        cache_key = (
            CacheKeys.cv_extraction(cv_id)
            if version is None
            else CacheKeys.cv_extraction(f"{cv_id}_v{version}")
        )
        
        cached = self.cache_client.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for CV {cv_id}")
            return cached
        
        # Fall back to repository
        if version:
            cv_data = self.cv_repository.get_cv_by_version(cv_id, version)
        else:
            cv_data = self.cv_repository.get(cv_id)
        
        if cv_data:
            # Store in cache
            self.cache_client.set(
                cache_key,
                cv_data,
                self.cache_client.config.CV_EXTRACTION_TTL,
            )
            logger.debug(f"Cached CV {cv_id}")
        
        return cv_data
    
    def get_cv_metadata(self, cv_id: str) -> Optional[Dict[str, Any]]:
        """Get CV metadata."""
        cache_key = CacheKeys.cv_metadata(cv_id)
        
        cached = self.cache_client.get(cache_key)
        if cached is not None:
            return cached
        
        cv_data = self.cv_repository.get(cv_id)
        if cv_data:
            self.cache_client.set(
                cache_key,
                cv_data,
                self.cache_client.config.CV_METADATA_TTL,
            )
        
        return cv_data
    
    def get_cv_versions(self, cv_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a CV."""
        return self.cv_repository.get_versions(cv_id)
    
    def invalidate_cv_cache(self, cv_id: str) -> int:
        """Invalidate cache for a CV."""
        return self.cache_client.invalidate_cv(cv_id)
