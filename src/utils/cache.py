"""
In-memory caching system for CG Spins Bot
Provides fast access to frequently used data with TTL support
"""

import time
import threading
from typing import Dict, Any, Optional, Callable
from collections import OrderedDict
import json

class TTLCache:
    """Thread-safe TTL cache with LRU eviction"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.RLock()
    
    def _is_expired(self, key: str) -> bool:
        """Check if a key has expired"""
        if key not in self.timestamps:
            return True
        
        expiry_time = self.timestamps[key]
        return time.time() > expiry_time
    
    def _evict_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, expiry_time in self.timestamps.items()
            if current_time > expiry_time
        ]
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if self.cache:
            # Remove the oldest entry (first in OrderedDict)
            key, _ = self.cache.popitem(last=False)
            self.timestamps.pop(key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache and not self._is_expired(key):
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            else:
                # Remove expired entry
                self.cache.pop(key, None)
                self.timestamps.pop(key, None)
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        with self.lock:
            # Remove if already exists
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
            
            # Evict expired entries first
            self._evict_expired()
            
            # Evict LRU if at capacity
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Add new entry
            self.cache[key] = value
            ttl = ttl or self.default_ttl
            self.timestamps[key] = time.time() + ttl
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self.lock:
            existed = key in self.cache
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
            return existed
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        with self.lock:
            self._evict_expired()
            return len(self.cache)
    
    def keys(self) -> list:
        """Get all non-expired keys"""
        with self.lock:
            self._evict_expired()
            return list(self.cache.keys())

class CacheManager:
    """Centralized cache management for the bot"""
    
    def __init__(self):
        # User data cache (5 minutes TTL)
        self.user_cache = TTLCache(max_size=500, default_ttl=300)
        
        # Package data cache (1 hour TTL - rarely changes)
        self.package_cache = TTLCache(max_size=50, default_ttl=3600)
        
        # TON API response cache (30 seconds TTL)
        self.ton_api_cache = TTLCache(max_size=200, default_ttl=30)
        
        # Payment status cache (2 minutes TTL)
        self.payment_cache = TTLCache(max_size=100, default_ttl=120)
        
        # Statistics cache (1 minute TTL)
        self.stats_cache = TTLCache(max_size=50, default_ttl=60)
    
    def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user data"""
        return self.user_cache.get(f"user_{user_id}")
    
    def set_user_data(self, user_id: int, data: Dict[str, Any], ttl: int = 300) -> None:
        """Cache user data"""
        self.user_cache.set(f"user_{user_id}", data, ttl)
    
    def invalidate_user_data(self, user_id: int) -> None:
        """Invalidate user data cache"""
        self.user_cache.delete(f"user_{user_id}")
    
    def get_package_data(self, package_key: str) -> Optional[Dict[str, Any]]:
        """Get cached package data"""
        return self.package_cache.get(f"package_{package_key}")
    
    def set_package_data(self, package_key: str, data: Dict[str, Any]) -> None:
        """Cache package data"""
        self.package_cache.set(f"package_{package_key}", data)
    
    def get_ton_api_data(self, endpoint: str, params: str = "") -> Optional[Dict[str, Any]]:
        """Get cached TON API response"""
        cache_key = f"ton_api_{endpoint}_{hash(params)}"
        return self.ton_api_cache.get(cache_key)
    
    def set_ton_api_data(self, endpoint: str, params: str, data: Dict[str, Any]) -> None:
        """Cache TON API response"""
        cache_key = f"ton_api_{endpoint}_{hash(params)}"
        self.ton_api_cache.set(cache_key, data)
    
    def get_payment_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached payment status"""
        return self.payment_cache.get(f"payment_{user_id}")
    
    def set_payment_status(self, user_id: int, status: Dict[str, Any]) -> None:
        """Cache payment status"""
        self.payment_cache.set(f"payment_{user_id}", status)
    
    def invalidate_payment_status(self, user_id: int) -> None:
        """Invalidate payment status cache"""
        self.payment_cache.delete(f"payment_{user_id}")
    
    def get_stats(self, stats_type: str) -> Optional[Dict[str, Any]]:
        """Get cached statistics"""
        return self.stats_cache.get(f"stats_{stats_type}")
    
    def set_stats(self, stats_type: str, data: Dict[str, Any]) -> None:
        """Cache statistics"""
        self.stats_cache.set(f"stats_{stats_type}", data)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return {
            "user_cache": {
                "size": self.user_cache.size(),
                "max_size": self.user_cache.max_size
            },
            "package_cache": {
                "size": self.package_cache.size(),
                "max_size": self.package_cache.max_size
            },
            "ton_api_cache": {
                "size": self.ton_api_cache.size(),
                "max_size": self.ton_api_cache.max_size
            },
            "payment_cache": {
                "size": self.payment_cache.size(),
                "max_size": self.payment_cache.max_size
            },
            "stats_cache": {
                "size": self.stats_cache.size(),
                "max_size": self.stats_cache.max_size
            }
        }
    
    def clear_all_caches(self) -> None:
        """Clear all caches"""
        self.user_cache.clear()
        self.package_cache.clear()
        self.ton_api_cache.clear()
        self.payment_cache.clear()
        self.stats_cache.clear()

# Global cache manager instance
cache_manager = CacheManager()

def cached(ttl: int = 300, cache_type: str = "user"):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            if cache_type == "user":
                cached_result = cache_manager.user_cache.get(cache_key)
            elif cache_type == "package":
                cached_result = cache_manager.package_cache.get(cache_key)
            elif cache_type == "ton_api":
                cached_result = cache_manager.ton_api_cache.get(cache_key)
            elif cache_type == "payment":
                cached_result = cache_manager.payment_cache.get(cache_key)
            elif cache_type == "stats":
                cached_result = cache_manager.stats_cache.get(cache_key)
            else:
                cached_result = None
            
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            if cache_type == "user":
                cache_manager.user_cache.set(cache_key, result, ttl)
            elif cache_type == "package":
                cache_manager.package_cache.set(cache_key, result, ttl)
            elif cache_type == "ton_api":
                cache_manager.ton_api_cache.set(cache_key, result, ttl)
            elif cache_type == "payment":
                cache_manager.payment_cache.set(cache_key, result, ttl)
            elif cache_type == "stats":
                cache_manager.stats_cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
