"""Score retriever for latest and historical scores."""

import logging
from typing import Any, Dict, List, Optional

from src.cache import CacheClient, CacheKeys
from src.repository import ScoreRepository

logger = logging.getLogger(__name__)


class ScoreRetriever:
    """Retrieve score data with caching."""
    
    def __init__(
        self,
        cache_client: CacheClient,
        score_repository: ScoreRepository,
    ):
        """Initialize score retriever."""
        self.cache_client = cache_client
        self.score_repository = score_repository
    
    def get_latest_score(self, cv_id: str, jd_id: str) -> Optional[Dict[str, Any]]:
        """Get latest score for CV-JD pair."""
        cache_key = CacheKeys.score_latest(cv_id, jd_id)
        
        cached = self.cache_client.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for score {cv_id}:{jd_id}")
            return cached
        
        # Get from repository
        repo_key = f"{cv_id}:{jd_id}"
        score = self.score_repository.get(repo_key)
        
        if score:
            self.cache_client.set(
                cache_key,
                score,
                self.cache_client.config.SCORE_TTL,
            )
            logger.debug(f"Cached score {cv_id}:{jd_id}")
        
        return score
    
    def get_versioned_score(
        self,
        cv_id: str,
        cv_version: int,
        jd_id: str,
        jd_version: int,
    ) -> Optional[Dict[str, Any]]:
        """Get score at specific versions."""
        cache_key = CacheKeys.score_versioned(cv_id, cv_version, jd_id, jd_version)
        
        cached = self.cache_client.get(cache_key)
        if cached is not None:
            return cached
        
        # In real implementation, would look up from score history
        # For now, return latest
        return self.get_latest_score(cv_id, jd_id)
    
    def get_score_history(self, cv_id: str, jd_id: str) -> List[Dict[str, Any]]:
        """Get score history for CV-JD pair."""
        cache_key = CacheKeys.score_history(cv_id, jd_id)
        
        cached = self.cache_client.get(cache_key)
        if cached is not None:
            return cached
        
        repo_key = f"{cv_id}:{jd_id}"
        history = self.score_repository.get_history(repo_key)
        
        if history:
            self.cache_client.set(
                cache_key,
                history,
                self.cache_client.config.SCORE_HISTORY_TTL,
            )
        
        return history
    
    def get_all_scores_for_cv(self, cv_id: str) -> List[Dict[str, Any]]:
        """Get all scores for a CV."""
        return self.score_repository.get_scores_for_cv(cv_id)
    
    def get_all_scores_for_jd(self, jd_id: str) -> List[Dict[str, Any]]:
        """Get all scores for a JD."""
        return self.score_repository.get_scores_for_jd(jd_id)
    
    def invalidate_score_cache(self, cv_id: str = None, jd_id: str = None) -> int:
        """Invalidate score cache."""
        return self.cache_client.invalidate_scores(cv_id, jd_id)
