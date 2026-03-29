"""Tests for cache layer."""

import pytest
from src.cache import (
    CacheClient,
    CacheConfig,
    CacheKeys,
    CacheWarmer,
)


class TestCacheConfig:
    """Test cache configuration."""
    
    def test_default_config(self):
        """Test default cache config."""
        config = CacheConfig()
        
        assert config.redis_host == "localhost"
        assert config.redis_port == 6379
        assert config.CV_EXTRACTION_TTL == 48 * 3600
        assert config.SCORE_TTL == 24 * 3600
    
    def test_get_ttl(self):
        """Test getting TTL by cache type."""
        config = CacheConfig()
        
        assert config.get_ttl("cv_extraction") == 48 * 3600
        assert config.get_ttl("score") == 24 * 3600
        assert config.get_ttl("jd_extraction") == 7 * 24 * 3600


class TestCacheKeys:
    """Test cache key generation."""
    
    def test_cv_extraction_key(self):
        """Test CV extraction key."""
        key = CacheKeys.cv_extraction("123")
        assert key == "cvai:extraction:cv:123"
    
    def test_score_latest_key(self):
        """Test latest score key."""
        key = CacheKeys.score_latest("cv1", "jd1")
        assert key == "cvai:score:latest:cv1:jd1"
    
    def test_score_versioned_key(self):
        """Test versioned score key."""
        key = CacheKeys.score_versioned("cv1", 1, "jd1", 2)
        assert key == "cvai:score:v1:cv1:jdv2:jd1"
    
    def test_cv_pattern(self):
        """Test CV pattern for deletion."""
        pattern = CacheKeys.cv_pattern("cv1")
        assert pattern == "cvai:*:cv1*"
    
    def test_jd_pattern(self):
        """Test JD pattern for deletion."""
        pattern = CacheKeys.jd_pattern("jd1")
        assert pattern == "cvai:*:jd1*"


class TestCacheClient:
    """Test cache client (without Redis)."""
    
    def test_cache_client_init(self):
        """Test cache client initialization."""
        client = CacheClient()
        
        assert client.stats["hits"] == 0
        assert client.stats["misses"] == 0
        assert client.stats["errors"] == 0
    
    def test_cache_get_stats(self):
        """Test cache statistics."""
        client = CacheClient()
        
        stats = client.get_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
    
    def test_cache_health_check(self):
        """Test cache health check."""
        client = CacheClient()
        
        health = client.health_check()
        assert "status" in health
        assert "connected" in health


class TestCachedValue:
    """Test cached value wrapper."""
    
    def test_cached_value_to_dict(self):
        """Test converting cached value to dict."""
        from src.cache import CachedValue
        
        cached = CachedValue({"test": "value"}, cache_hit=True)
        data = cached.to_dict()
        
        assert data["value"] == {"test": "value"}
        assert data["cache_hit"] is True
        assert "timestamp" in data
