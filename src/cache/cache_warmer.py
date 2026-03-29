"""Cache warming strategies for pre-loading frequently accessed data."""

import logging
from typing import List, Optional, Callable, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.cache.cache_client import CacheClient
from src.cache.cache_config import CacheConfig

logger = logging.getLogger(__name__)


class CacheWarmer:
    """Handles cache warming and preloading."""
    
    def __init__(self, cache_client: CacheClient, config: Optional[CacheConfig] = None):
        """Initialize cache warmer."""
        self.cache_client = cache_client
        self.config = config or CacheConfig()
    
    def warm_cv_data(self, cv_ids: List[str], fetch_fn: Callable) -> Dict[str, bool]:
        """Warm cache with CV data."""
        logger.info(f"Starting cache warming for {len(cv_ids)} CVs")
        results = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._warm_single_cv, cv_id, fetch_fn): cv_id
                for cv_id in cv_ids
            }
            
            for future in as_completed(futures):
                cv_id = futures[future]
                try:
                    results[cv_id] = future.result()
                except Exception as e:
                    logger.error(f"Error warming CV {cv_id}: {e}")
                    results[cv_id] = False
        
        logger.info(f"Cache warming completed: {sum(results.values())}/{len(cv_ids)} successful")
        return results
    
    def _warm_single_cv(self, cv_id: str, fetch_fn: Callable) -> bool:
        """Warm cache for a single CV."""
        try:
            data = fetch_fn(cv_id)
            if data:
                # Store in cache with appropriate TTL
                self.cache_client.set(
                    f"cvai:extraction:cv:{cv_id}",
                    data,
                    self.config.CV_EXTRACTION_TTL
                )
                return True
        except Exception as e:
            logger.error(f"Error warming single CV {cv_id}: {e}")
        
        return False
    
    def warm_jd_data(self, jd_ids: List[str], fetch_fn: Callable) -> Dict[str, bool]:
        """Warm cache with JD data."""
        logger.info(f"Starting cache warming for {len(jd_ids)} JDs")
        results = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._warm_single_jd, jd_id, fetch_fn): jd_id
                for jd_id in jd_ids
            }
            
            for future in as_completed(futures):
                jd_id = futures[future]
                try:
                    results[jd_id] = future.result()
                except Exception as e:
                    logger.error(f"Error warming JD {jd_id}: {e}")
                    results[jd_id] = False
        
        logger.info(f"Cache warming completed: {sum(results.values())}/{len(jd_ids)} successful")
        return results
    
    def _warm_single_jd(self, jd_id: str, fetch_fn: Callable) -> bool:
        """Warm cache for a single JD."""
        try:
            data = fetch_fn(jd_id)
            if data:
                self.cache_client.set(
                    f"cvai:extraction:jd:{jd_id}",
                    data,
                    self.config.JD_EXTRACTION_TTL
                )
                return True
        except Exception as e:
            logger.error(f"Error warming single JD {jd_id}: {e}")
        
        return False
