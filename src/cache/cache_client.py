"""Redis-based cache client with TTL and invalidation strategies."""

import hashlib
import json
import logging
import threading
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from functools import wraps

try:
    import redis
    from redis.exceptions import ConnectionError, TimeoutError
except ImportError:
    redis = None

from src.cache.cache_config import CacheConfig
from src.cache.cache_keys import CacheKeys


logger = logging.getLogger(__name__)

class CacheException(Exception):
    """Base exception for cache operations."""
    pass


class CachedValue:
    """Wrapper for cached values with metadata."""
    
    def __init__(self, value: Any, cache_hit: bool = True):
        self.value = value
        self.cache_hit = cache_hit
        self.timestamp = datetime.now(timezone.utc).isoformat()   
         
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "value": self.value,
            "cache_hit": self.cache_hit,
            "timestamp": self.timestamp,
        }


class CacheClient:
    """Redis cache client with stats and health checks."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize cache client."""
        self.config = config or CacheConfig()
        self.redis_client = None
        self._stats_lock = threading.Lock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "operations": 0,
        }
        self._connect()
    
    def _increment_stat(self, key: str):
        with self._stats_lock:
            self.stats[key] += 1
    
    def _connect(self):
        """Connect to Redis."""
        if not redis:
            logger.warning("Redis not installed. Cache operations will be skipped.")
            return
        
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis cache")
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        
        try:
            self._increment_stat("operations")
            value = self.redis_client.get(key)
            
            if value is None:
                self._increment_stat("misses")
                return None
            
            self._increment_stat("hits")
            return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._increment_stat("errors")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self.redis_client:
            return False
        
        try:
            self._increment_stat("operations")
            serialized = json.dumps(value, default=str)
            
            if ttl:
                self.redis_client.setex(key, ttl, serialized)
            else:
                self.redis_client.set(key, serialized)
            
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self._increment_stat("errors")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False
        
        try:
            self._increment_stat("operations")
            result = self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self._increment_stat("errors")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern using non-blocking SCAN.
        
        Iterates through keys via SCAN to avoid blocking Redis, and deletes
        keys in batches to avoid very large DEL argument lists.
        """
        if not self.redis_client:
            return 0
        
        try:
            self._increment_stat("operations")
            total_deleted = 0
            batch_size = 1000
            batch_keys = []
            
            # Use scan_iter for non-blocking iteration
            for key in self.redis_client.scan_iter(match=pattern):
                batch_keys.append(key)
                
                # Delete in batches to avoid overly large DEL commands
                if len(batch_keys) >= batch_size:
                    deleted = self.redis_client.delete(*batch_keys)
                    total_deleted += deleted
                    batch_keys.clear()
            
            # Delete remaining keys in final batch
            if batch_keys:
                deleted = self.redis_client.delete(*batch_keys)
                total_deleted += deleted
            
            return total_deleted
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            self._increment_stat("errors")
            return 0
    
    def invalidate_cv(self, cv_id: str) -> int:
        """Invalidate all cache entries for a CV."""
        pattern = CacheKeys.cv_pattern(cv_id)
        deleted = self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} cache entries for CV {cv_id}")
        return deleted
    
    def invalidate_jd(self, jd_id: str) -> int:
        """Invalidate all cache entries for a JD."""
        pattern = CacheKeys.jd_pattern(jd_id)
        deleted = self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} cache entries for JD {jd_id}")
        return deleted
    
    def invalidate_scores(self, cv_id: str = None, jd_id: str = None) -> int:
        """Invalidate score cache entries."""
        pattern = CacheKeys.score_pattern(cv_id, jd_id)
        deleted = self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} score cache entries (cv_id={cv_id}, jd_id={jd_id})")
        return deleted
    
    def health_check(self) -> Dict[str, Any]:
        """Check cache health."""
        if not self.redis_client:
            return {
                "status": "disconnected",
                "connected": False,
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "errors": self.stats["errors"],
            }
        
        try:
            self.redis_client.ping()
            info = self.redis_client.info("memory")
            
            total_ops = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_ops * 100) if total_ops > 0 else 0
            
            return {
                "status": "healthy",
                "connected": True,
                "memory_used_mb": info.get("used_memory_human", "unknown"),
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "hit_rate": f"{hit_rate:.2f}%",
                "errors": self.stats["errors"],
                "total_operations": self.stats["operations"],
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "connected": False,
                "error": str(e),
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._stats_lock:
            hits = self.stats["hits"]
            misses = self.stats["misses"]
            errors = self.stats["errors"]
            operations = self.stats["operations"]
        
        total_ops = hits + misses
        hit_rate = (hits / total_ops * 100) if total_ops > 0 else 0
        
        return {
            "hits": hits,
            "misses": misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "errors": errors,
            "total_operations": operations,
        }   
         
    def clear_all(self) -> bool:
        """Clear all cache."""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.info("Cleared all cache")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


def cache_result(ttl_seconds: Optional[int] = None):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, cache_client: Optional[CacheClient] = None, **kwargs):
            # Generate cache key from function name and arguments
            key_data = f"{func.__module__}.{func.__name__}:{repr(args)}:{repr(sorted(kwargs.items()))}"
            key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
            key = f"func:{func.__name__}:{key_hash}"
            
            if cache_client:
                cached = cache_client.get(key)
                if cached is not None:
                    return CachedValue(cached, cache_hit=True)
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            if cache_client:
                cache_client.set(key, result, ttl_seconds)
        
            return CachedValue(result, cache_hit=False)
        
        return wrapper
    
    return decorator
