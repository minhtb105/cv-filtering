"""
Task 7: Performance Optimization Layer - Caching, batching, and async extraction
Optimizes CV extraction pipeline for speed and resource efficiency
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import asyncio
from functools import lru_cache


@dataclass
class CacheEntry:
    """Single cache entry with metadata"""
    value: Any
    timestamp: datetime
    ttl_seconds: int = 3600
    hit_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() - self.timestamp > timedelta(seconds=self.ttl_seconds)
    
    def mark_hit(self):
        """Record cache hit"""
        self.hit_count += 1


class ExtractionCache:
    """Thread-safe cache for extraction results"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """Initialize cache"""
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    def _make_key(self, cv_text: str, field_name: str) -> str:
        """Generate cache key from CV and field"""
        content = f"{cv_text}:{field_name}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, cv_text: str, field_name: str) -> Optional[Any]:
        """Retrieve from cache"""
        key = self._make_key(cv_text, field_name)
        
        if key in self.cache:
            entry = self.cache[key]
            if not entry.is_expired():
                entry.mark_hit()
                self.hits += 1
                return entry.value
            else:
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, cv_text: str, field_name: str, value: Any, ttl: Optional[int] = None):
        """Store in cache"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            self._evict_oldest()
        
        key = self._make_key(cv_text, field_name)
        ttl = ttl or self.default_ttl
        
        self.cache[key] = CacheEntry(
            value=value,
            timestamp=datetime.now(),
            ttl_seconds=ttl
        )
    
    def _evict_oldest(self):
        """Remove least recently used entry"""
        if self.cache:
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].timestamp
            )
            del self.cache[oldest_key]
    
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0


class BatchExtractor:
    """Batch extraction for multiple CVs"""
    
    def __init__(self, batch_size: int = 10):
        """Initialize batch extractor"""
        self.batch_size = batch_size
        self.batch_queue: List[Dict[str, Any]] = []
    
    def add_to_batch(self, cv_text: str, fields: List[str]) -> int:
        """Add CV to batch queue, return batch ID"""
        batch_item = {
            'cv_text': cv_text,
            'fields': fields,
            'timestamp': datetime.now()
        }
        self.batch_queue.append(batch_item)
        return len(self.batch_queue) - 1
    
    def get_batch_size(self) -> int:
        """Get current batch size"""
        return len(self.batch_queue)
    
    def should_process_batch(self) -> bool:
        """Check if batch should be processed"""
        # Process if full or if waiting too long
        if len(self.batch_queue) >= self.batch_size:
            return True
        
        if len(self.batch_queue) > 0:
            oldest = self.batch_queue[0]['timestamp']
            if datetime.now() - oldest > timedelta(seconds=5):
                return True
        
        return False
    
    def process_batch(self, extractor_func: Callable) -> List[Dict[str, Any]]:
        """Process current batch using extractor function"""
        results = []
        
        for item in self.batch_queue:
            result = extractor_func(item['cv_text'], item['fields'])
            results.append(result)
        
        self.batch_queue.clear()
        return results
    
    def get_batch_efficiency(self) -> float:
        """Calculate batch processing efficiency"""
        if self.batch_size == 0:
            return 0.0
        return len(self.batch_queue) / self.batch_size


class FieldLevelCache:
    """Cache individual field extractions"""
    
    def __init__(self):
        """Initialize field caches"""
        self.field_caches: Dict[str, ExtractionCache] = {}
    
    def get_cache(self, field_name: str) -> ExtractionCache:
        """Get cache for specific field"""
        if field_name not in self.field_caches:
            self.field_caches[field_name] = ExtractionCache()
        return self.field_caches[field_name]
    
    def get_field(self, cv_text: str, field_name: str) -> Optional[Any]:
        """Get field value from cache"""
        return self.get_cache(field_name).get(cv_text, field_name)
    
    def set_field(self, cv_text: str, field_name: str, value: Any):
        """Cache field value"""
        self.get_cache(field_name).set(cv_text, field_name, value)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics across all fields"""
        stats = {
            'total_fields': len(self.field_caches),
            'fields': {}
        }
        
        for field_name, cache in self.field_caches.items():
            stats['fields'][field_name] = {
                'hits': cache.hits,
                'misses': cache.misses,
                'hit_rate': cache.get_hit_rate(),
                'size': len(cache.cache)
            }
        
        return stats


class AsyncExtractor:
    """Async extraction for non-blocking operations"""
    
    def __init__(self, max_concurrent: int = 5):
        """Initialize async extractor"""
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def extract_field_async(
        self,
        cv_text: str,
        field_name: str,
        extractor_func: Callable
    ) -> Dict[str, Any]:
        """Extract field asynchronously"""
        async with self.semaphore:
            # Run blocking extractor in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                extractor_func,
                cv_text,
                field_name
            )
    
    async def extract_multiple_fields_async(
        self,
        cv_text: str,
        fields: List[str],
        extractor_func: Callable
    ) -> Dict[str, Any]:
        """Extract multiple fields concurrently"""
        tasks = [
            self.extract_field_async(cv_text, field, extractor_func)
            for field in fields
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {
            field: result
            for field, result in zip(fields, results)
        }


class PerformanceMonitor:
    """Monitor extraction performance"""
    
    def __init__(self):
        """Initialize performance monitor"""
        self.extraction_times: Dict[str, List[float]] = {}
        self.memory_usage: List[float] = []
        self.extraction_counts: Dict[str, int] = {}
    
    def log_extraction_time(self, field_name: str, time_ms: float):
        """Log extraction time for a field"""
        if field_name not in self.extraction_times:
            self.extraction_times[field_name] = []
        self.extraction_times[field_name].append(time_ms)
    
    def log_extraction(self, field_name: str):
        """Log extraction count"""
        self.extraction_counts[field_name] = self.extraction_counts.get(field_name, 0) + 1
    
    def get_average_time(self, field_name: str) -> float:
        """Get average extraction time for field"""
        times = self.extraction_times.get(field_name, [])
        return sum(times) / len(times) if times else 0.0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        report = {
            'fields': {},
            'summary': {}
        }
        
        all_times = []
        for field_name, times in self.extraction_times.items():
            if times:
                avg_time = sum(times) / len(times)
                all_times.extend(times)
                
                report['fields'][field_name] = {
                    'count': self.extraction_counts.get(field_name, 0),
                    'avg_time_ms': avg_time,
                    'min_time_ms': min(times),
                    'max_time_ms': max(times),
                    'total_executions': len(times)
                }
        
        if all_times:
            report['summary'] = {
                'total_extractions': sum(self.extraction_counts.values()),
                'avg_time_ms': sum(all_times) / len(all_times),
                'total_time_ms': sum(all_times),
                'slowest_field': max(
                    self.extraction_times.items(),
                    key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0
                )[0] if self.extraction_times else None
            }
        
        return report


class PipelineOptimizer:
    """Optimize extraction pipeline"""
    
    def __init__(self):
        """Initialize pipeline optimizer"""
        self.cache = FieldLevelCache()
        self.batch_extractor = BatchExtractor(batch_size=10)
        self.performance_monitor = PerformanceMonitor()
    
    def optimize_extraction_order(self, fields: List[str]) -> List[str]:
        """Order fields by extraction time for efficiency"""
        avg_times = [
            (field, self.performance_monitor.get_average_time(field))
            for field in fields
        ]
        
        # Sort by average time (fast to slow)
        return [field for field, _ in sorted(avg_times, key=lambda x: x[1])]
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        return {
            'cache_stats': self.cache.get_stats(),
            'batch_efficiency': self.batch_extractor.get_batch_efficiency(),
            'performance': self.performance_monitor.get_performance_report()
        }


# Decorator for cached extraction
def cached_extraction(ttl: int = 3600):
    """Decorator to cache extraction results"""
    def decorator(func: Callable) -> Callable:
        cache = ExtractionCache(default_ttl=ttl)
        
        def wrapper(cv_text: str, field_name: str, *args, **kwargs):
            # Try cache first
            cached_value = cache.get(cv_text, field_name)
            if cached_value is not None:
                return cached_value
            
            # Call extraction function
            result = func(cv_text, field_name, *args, **kwargs)
            
            # Cache result
            cache.set(cv_text, field_name, result)
            
            return result
        
        wrapper.cache = cache
        return wrapper
    
    return decorator


# LRU cache for computation-heavy operations
@lru_cache(maxsize=256)
def cached_similarity_calculation(text1: str, text2: str) -> float:
    """LRU cached string similarity"""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, text1, text2).ratio()
