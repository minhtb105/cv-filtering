"""Cache configuration with TTL policies."""

from typing import Dict
from dataclasses import dataclass


@dataclass
class CacheConfig:
    """Cache configuration with TTL policies."""
    
    # Redis connection settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = None
    
    # TTL policies (in seconds) by data type
    CV_EXTRACTION_TTL: int = 48 * 3600  # 48 hours
    CV_METADATA_TTL: int = 24 * 3600    # 24 hours
    SCORE_TTL: int = 24 * 3600          # 24 hours
    JD_EXTRACTION_TTL: int = 7 * 24 * 3600  # 7 days
    JD_METADATA_TTL: int = 7 * 24 * 3600    # 7 days
    INTERVIEW_RESULT_TTL: int = 30 * 24 * 3600  # 30 days
    SCORE_HISTORY_TTL: int = 30 * 24 * 3600     # 30 days
    COMPARISON_TTL: int = 1 * 3600      # 1 hour
    RANKING_TTL: int = 1 * 3600         # 1 hour
    
    # Cache warmup configuration
    ENABLE_CACHE_WARMER: bool = True
    CACHE_WARM_BATCH_SIZE: int = 100
    CACHE_WARM_DELAY_SECONDS: int = 5
    
    # Health check configuration
    HEALTH_CHECK_INTERVAL: int = 60  # seconds
    HEALTH_CHECK_TIMEOUT: int = 5    # seconds
    
    def get_ttl(self, cache_type: str) -> int:
        """Get TTL for a specific cache type."""
        ttl_map = {
            "cv_extraction": self.CV_EXTRACTION_TTL,
            "cv_metadata": self.CV_METADATA_TTL,
            "score": self.SCORE_TTL,
            "jd_extraction": self.JD_EXTRACTION_TTL,
            "jd_metadata": self.JD_METADATA_TTL,
            "interview": self.INTERVIEW_RESULT_TTL,
            "score_history": self.SCORE_HISTORY_TTL,
            "comparison": self.COMPARISON_TTL,
            "ranking": self.RANKING_TTL,
        }
        return ttl_map.get(cache_type, self.SCORE_TTL)
