"""
LRU Cache Service for AI Response Caching
- Caches responses based on confidence ranges
- LRU eviction policy
- Hit/Miss metrics tracking
"""
import time
import logging
from collections import OrderedDict
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class LRUCache:
    """
    LRU Cache for AI responses
    Key: confidence_range bucket (e.g., "excellent", "good", etc.)
    Value: {response, timestamp, hit_count}
    """
    
    def __init__(self, capacity: int = 20):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.hits = 0
        self.misses = 0
        self.total_requests = 0
    
    def _get_confidence_bucket(self, confidence: float) -> str:
        """
        Map confidence to bucket (based on detection threshold of 0.4)
        
        Buckets:
        - excellent: 90-100% (far above threshold)
        - good: 75-90% (well above threshold)
        - moderate: 60-75% (above threshold)
        - acceptable: 45-60% (near threshold)
        - threshold: 40-45% (CRITICAL - at detection limit)
        - rejected: <40% (below threshold - not detected)
        """
        if confidence >= 0.90:
            return "excellent"
        elif confidence >= 0.75:
            return "good"
        elif confidence >= 0.60:
            return "moderate"
        elif confidence >= 0.45:
            return "acceptable"
        elif confidence >= 0.40:
            return "threshold"
        else:
            return "rejected"
    
    def get(self, avg_confidence: float) -> Optional[str]:
        """Get cached response for confidence level"""
        self.total_requests += 1
        bucket = self._get_confidence_bucket(avg_confidence)
        
        if bucket in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(bucket)
            self.hits += 1
            
            # Update hit count
            cached_data = self.cache[bucket]
            cached_data['hit_count'] += 1
            cached_data['last_used'] = time.time()
            
            logger.info(f"✅ Cache HIT for '{bucket}' (confidence: {avg_confidence:.2f})")
            return cached_data['response']
        
        self.misses += 1
        logger.info(f"❌ Cache MISS for '{bucket}' (confidence: {avg_confidence:.2f})")
        return None
    
    def put(self, avg_confidence: float, response: str):
        """Cache response with LRU eviction"""
        bucket = self._get_confidence_bucket(avg_confidence)
        
        if bucket in self.cache:
            # Update existing
            self.cache.move_to_end(bucket)
            self.cache[bucket]['response'] = response
            self.cache[bucket]['updated_at'] = time.time()
            logger.info(f"🔄 Updated cache for '{bucket}'")
        else:
            # Add new
            if len(self.cache) >= self.capacity:
                # Evict LRU (least recently used)
                evicted_key, evicted_val = self.cache.popitem(last=False)
                logger.info(
                    f"🗑️  Evicted LRU: '{evicted_key}' "
                    f"(hit_count: {evicted_val['hit_count']}, "
                    f"age: {time.time() - evicted_val['created_at']:.1f}s)"
                )
            
            self.cache[bucket] = {
                'response': response,
                'created_at': time.time(),
                'last_used': time.time(),
                'updated_at': time.time(),
                'hit_count': 0
            }
            logger.info(f"💾 Cached new response for '{bucket}'")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        hit_rate = (self.hits / self.total_requests * 100) if self.total_requests > 0 else 0
        
        # Get bucket usage stats
        bucket_stats = {}
        for bucket, data in self.cache.items():
            bucket_stats[bucket] = {
                'hit_count': data['hit_count'],
                'age_seconds': round(time.time() - data['created_at'], 1),
                'last_used_ago': round(time.time() - data['last_used'], 1)
            }
        
        return {
            'capacity': self.capacity,
            'current_size': len(self.cache),
            'total_requests': self.total_requests,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate_percentage': round(hit_rate, 2),
            'buckets': list(self.cache.keys()),
            'bucket_stats': bucket_stats
        }
    
    def clear(self):
        """Clear all cached entries"""
        cleared_count = len(self.cache)
        self.cache.clear()
        logger.info(f"🧹 Cleared {cleared_count} cached entries")
        return cleared_count
