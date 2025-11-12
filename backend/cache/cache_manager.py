"""
Cache Manager for Project AEGIS
Comprehensive caching system with Redis backend and intelligent cache strategies
"""

import os
import json
import pickle
import logging
import hashlib
from typing import Any, Optional, Union, List, Dict, Callable
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass, asdict
from enum import Enum

import redis
import redis.asyncio as aioredis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    REFRESH_AHEAD = "refresh_ahead"

class CacheLevel(Enum):
    """Cache levels with different TTLs"""
    INSTANT = 60  # 1 minute
    SHORT = 300   # 5 minutes
    MEDIUM = 900  # 15 minutes
    LONG = 3600   # 1 hour
    EXTENDED = 86400  # 24 hours

@dataclass
class CacheConfig:
    """Cache configuration"""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_max_connections: int = 100
    default_ttl: int = 300
    key_prefix: str = "aegis:"
    enable_compression: bool = True
    compression_threshold: int = 1024
    enable_serialization: bool = True
    max_key_length: int = 250
    enable_cluster: bool = False
    cluster_nodes: List[str] = None

@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    evictions: int = 0
    memory_usage: int = 0
    key_count: int = 0
    avg_response_time: float = 0.0
    hit_rate: float = 0.0

class CacheSerializer:
    """Cache data serialization and compression"""

    def __init__(self, enable_compression: bool = True, compression_threshold: int = 1024):
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold

        try:
            import zlib
            self.compressor = zlib
        except ImportError:
            logger.warning("zlib not available, compression disabled")
            self.enable_compression = False
            self.compressor = None

    def serialize(self, data: Any) -> bytes:
        """Serialize data for caching"""
        try:
            # Convert to bytes
            if isinstance(data, bytes):
                serialized = data
            elif isinstance(data, str):
                serialized = data.encode('utf-8')
            else:
                serialized = pickle.dumps(data)

            # Apply compression if enabled and data is large enough
            if (self.enable_compression and
                self.compressor and
                len(serialized) > self.compression_threshold):

                compressed = self.compressor.compress(serialized)
                # Only use compression if it actually reduces size
                if len(compressed) < len(serialized):
                    return b"COMP:" + compressed

            return serialized

        except Exception as e:
            logger.error(f"Cache serialization error: {e}")
            raise

    def deserialize(self, data: bytes) -> Any:
        """Deserialize cached data"""
        try:
            # Check if data is compressed
            if data.startswith(b"COMP:"):
                if self.compressor:
                    decompressed = self.compressor.decompress(data[5:])
                    data = decompressed
                else:
                    logger.warning("Compressed data found but compression not available")

            # Try different deserialization methods
            try:
                # Try pickle first
                return pickle.loads(data)
            except (pickle.PickleError, UnicodeDecodeError):
                try:
                    # Try UTF-8 string
                    return data.decode('utf-8')
                except UnicodeDecodeError:
                    # Return raw bytes
                    return data

        except Exception as e:
            logger.error(f"Cache deserialization error: {e}")
            raise

class CacheManager:
    """
    Advanced cache manager with Redis backend
    Supports multiple caching strategies, intelligent invalidation, and performance monitoring
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.serializer = CacheSerializer(
            enable_compression=self.config.enable_compression,
            compression_threshold=self.config.compression_threshold
        )

        # Redis connections
        self.redis_client: Optional[redis.Redis] = None
        self.async_redis_client: Optional[aioredis.Redis] = None

        # Statistics
        self.stats = CacheStats()
        self._last_stats_update = datetime.utcnow()

        # Initialize connections
        self._initialize_connections()

        logger.info("Cache manager initialized successfully")

    def _initialize_connections(self):
        """Initialize Redis connections"""
        try:
            # Synchronous Redis client
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=self.config.redis_max_connections
            )

            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    async def _initialize_async_connections(self):
        """Initialize async Redis connections"""
        try:
            # Asynchronous Redis client
            self.async_redis_client = aioredis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=self.config.redis_max_connections
            )

            # Test connection
            await self.async_redis_client.ping()
            logger.info("Async Redis connection established")

        except Exception as e:
            logger.error(f"Failed to connect to async Redis: {e}")
            self.async_redis_client = None

    def _generate_key(self, key: str, namespace: str = None) -> str:
        """Generate cache key with namespace and prefix"""
        if namespace:
            key = f"{namespace}:{key}"

        full_key = f"{self.config.key_prefix}{key}"

        # Ensure key doesn't exceed Redis limit
        if len(full_key) > self.config.max_key_length:
            # Hash long keys
            key_hash = hashlib.md5(full_key.encode()).hexdigest()
            full_key = f"{self.config.key_prefix}{key_hash}"

        return full_key

    def _serialize_value(self, value: Any, ttl: Optional[int] = None) -> bytes:
        """Serialize value with metadata"""
        metadata = {
            'created_at': datetime.utcnow().isoformat(),
            'ttl': ttl or self.config.default_ttl,
            'size': 0
        }

        # Serialize the actual value
        serialized_value = self.serializer.serialize(value)
        metadata['size'] = len(serialized_value)

        # Combine metadata and value
        cache_data = {
            'metadata': metadata,
            'value': serialized_value
        }

        return self.serializer.serialize(cache_data)

    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize cached value with metadata validation"""
        try:
            cache_data = self.serializer.deserialize(data)

            if not isinstance(cache_data, dict) or 'value' not in cache_data:
                logger.warning("Invalid cache data format")
                return None

            # Check TTL if present
            metadata = cache_data.get('metadata', {})
            if metadata.get('ttl'):
                created_at = datetime.fromisoformat(metadata['created_at'])
                ttl = timedelta(seconds=metadata['ttl'])

                if datetime.utcnow() > created_at + ttl:
                    logger.debug("Cache entry expired")
                    return None

            # Deserialize the actual value
            value = self.serializer.deserialize(cache_data['value'])
            return value

        except Exception as e:
            logger.error(f"Cache deserialization error: {e}")
            return None

    def get(self, key: str, namespace: str = None) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            logger.warning("Redis client not available")
            self.stats.misses += 1
            return None

        start_time = datetime.utcnow()

        try:
            cache_key = self._generate_key(key, namespace)
            data = self.redis_client.get(cache_key)

            if data is None:
                self.stats.misses += 1
                return None

            # Deserialize and validate
            value = self._deserialize_value(data)

            if value is None:
                # Remove expired entry
                self.delete(key, namespace)
                self.stats.misses += 1
                return None

            self.stats.hits += 1

            # Update response time
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_response_time(response_time)

            return value

        except RedisError as e:
            logger.error(f"Cache get error: {e}")
            self.stats.errors += 1
            self.stats.misses += 1
            return None

    async def get_async(self, key: str, namespace: str = None) -> Optional[Any]:
        """Get value from cache asynchronously"""
        if not self.async_redis_client:
            await self._initialize_async_connections()

        if not self.async_redis_client:
            logger.warning("Async Redis client not available")
            self.stats.misses += 1
            return None

        start_time = datetime.utcnow()

        try:
            cache_key = self._generate_key(key, namespace)
            data = await self.async_redis_client.get(cache_key)

            if data is None:
                self.stats.misses += 1
                return None

            value = self._deserialize_value(data)

            if value is None:
                await self.delete_async(key, namespace)
                self.stats.misses += 1
                return None

            self.stats.hits += 1

            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_response_time(response_time)

            return value

        except RedisError as e:
            logger.error(f"Async cache get error: {e}")
            self.stats.errors += 1
            self.stats.misses += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None, namespace: str = None) -> bool:
        """Set value in cache"""
        if not self.redis_client:
            logger.warning("Redis client not available")
            return False

        try:
            cache_key = self._generate_key(key, namespace)
            ttl = ttl or self.config.default_ttl

            # Serialize value
            data = self._serialize_value(value, ttl)

            # Set in Redis with TTL
            result = self.redis_client.setex(cache_key, ttl, data)

            if result:
                self.stats.sets += 1
                return True
            else:
                self.stats.errors += 1
                return False

        except RedisError as e:
            logger.error(f"Cache set error: {e}")
            self.stats.errors += 1
            return False

    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None, namespace: str = None) -> bool:
        """Set value in cache asynchronously"""
        if not self.async_redis_client:
            await self._initialize_async_connections()

        if not self.async_redis_client:
            logger.warning("Async Redis client not available")
            return False

        try:
            cache_key = self._generate_key(key, namespace)
            ttl = ttl or self.config.default_ttl

            data = self._serialize_value(value, ttl)

            result = await self.async_redis_client.setex(cache_key, ttl, data)

            if result:
                self.stats.sets += 1
                return True
            else:
                self.stats.errors += 1
                return False

        except RedisError as e:
            logger.error(f"Async cache set error: {e}")
            self.stats.errors += 1
            return False

    def delete(self, key: str, namespace: str = None) -> bool:
        """Delete value from cache"""
        if not self.redis_client:
            return False

        try:
            cache_key = self._generate_key(key, namespace)
            result = self.redis_client.delete(cache_key)

            if result > 0:
                self.stats.deletes += 1
                return True
            return False

        except RedisError as e:
            logger.error(f"Cache delete error: {e}")
            self.stats.errors += 1
            return False

    async def delete_async(self, key: str, namespace: str = None) -> bool:
        """Delete value from cache asynchronously"""
        if not self.async_redis_client:
            await self._initialize_async_connections()

        if not self.async_redis_client:
            return False

        try:
            cache_key = self._generate_key(key, namespace)
            result = await self.async_redis_client.delete(cache_key)

            if result > 0:
                self.stats.deletes += 1
                return True
            return False

        except RedisError as e:
            logger.error(f"Async cache delete error: {e}")
            self.stats.errors += 1
            return False

    def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace"""
        if not self.redis_client:
            return 0

        try:
            pattern = f"{self.config.key_prefix}{namespace}:*"
            keys = self.redis_client.keys(pattern)

            if keys:
                deleted = self.redis_client.delete(*keys)
                self.stats.deletes += deleted
                return deleted

            return 0

        except RedisError as e:
            logger.error(f"Cache clear namespace error: {e}")
            self.stats.errors += 1
            return 0

    async def clear_namespace_async(self, namespace: str) -> int:
        """Clear all keys in a namespace asynchronously"""
        if not self.async_redis_client:
            await self._initialize_async_connections()

        if not self.async_redis_client:
            return 0

        try:
            pattern = f"{self.config.key_prefix}{namespace}:*"
            keys = await self.async_redis_client.keys(pattern)

            if keys:
                deleted = await self.async_redis_client.delete(*keys)
                self.stats.deletes += deleted
                return deleted

            return 0

        except RedisError as e:
            logger.error(f"Async cache clear namespace error: {e}")
            self.stats.errors += 1
            return 0

    def exists(self, key: str, namespace: str = None) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False

        try:
            cache_key = self._generate_key(key, namespace)
            return bool(self.redis_client.exists(cache_key))

        except RedisError as e:
            logger.error(f"Cache exists error: {e}")
            self.stats.errors += 1
            return False

    def increment(self, key: str, amount: int = 1, namespace: str = None) -> Optional[int]:
        """Increment numeric value in cache"""
        if not self.redis_client:
            return None

        try:
            cache_key = self._generate_key(key, namespace)
            return self.redis_client.incrby(cache_key, amount)

        except RedisError as e:
            logger.error(f"Cache increment error: {e}")
            self.stats.errors += 1
            return None

    def get_ttl(self, key: str, namespace: str = None) -> int:
        """Get remaining TTL for key"""
        if not self.redis_client:
            return -1

        try:
            cache_key = self._generate_key(key, namespace)
            return self.redis_client.ttl(cache_key)

        except RedisError as e:
            logger.error(f"Cache TTL error: {e}")
            self.stats.errors += 1
            return -1

    def _update_response_time(self, response_time: float):
        """Update average response time"""
        if self.stats.hits + self.stats.misses == 1:
            self.stats.avg_response_time = response_time
        else:
            self.stats.avg_response_time = (
                (self.stats.avg_response_time * (self.stats.hits + self.stats.misses - 1) + response_time) /
                (self.stats.hits + self.stats.misses)
            )

    def update_stats(self):
        """Update cache statistics from Redis"""
        if not self.redis_client:
            return

        try:
            # Get Redis info
            info = self.redis_client.info()

            self.stats.memory_usage = info.get('used_memory', 0)
            self.stats.evictions = info.get('evicted_keys', 0)
            self.stats.key_count = info.get('db0', {}).get('keys', 0)

            # Calculate hit rate
            total_requests = self.stats.hits + self.stats.misses
            if total_requests > 0:
                self.stats.hit_rate = (self.stats.hits / total_requests) * 100

            self._last_stats_update = datetime.utcnow()

        except RedisError as e:
            logger.error(f"Cache stats update error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self.update_stats()
        return asdict(self.stats)

    def reset_stats(self):
        """Reset cache statistics"""
        self.stats = CacheStats()
        self._last_stats_update = datetime.utcnow()

    def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        health = {
            'status': 'healthy',
            'redis_connected': False,
            'last_stats_update': self._last_stats_update.isoformat(),
            'issues': []
        }

        try:
            if self.redis_client:
                # Test Redis connection
                self.redis_client.ping()
                health['redis_connected'] = True

                # Check memory usage
                if self.stats.memory_usage > 0:
                    memory_mb = self.stats.memory_usage / (1024 * 1024)
                    if memory_mb > 1000:  # More than 1GB
                        health['issues'].append(f'High memory usage: {memory_mb:.1f}MB')

                # Check hit rate
                if self.stats.hit_rate < 50 and (self.stats.hits + self.stats.misses) > 100:
                    health['issues'].append(f'Low hit rate: {self.stats.hit_rate:.1f}%')

                # Check error rate
                total_ops = self.stats.hits + self.stats.misses + self.stats.sets + self.stats.deletes
                if total_ops > 0:
                    error_rate = (self.stats.errors / total_ops) * 100
                    if error_rate > 5:
                        health['issues'].append(f'High error rate: {error_rate:.1f}%')

            else:
                health['status'] = 'unhealthy'
                health['issues'].append('Redis client not connected')

        except Exception as e:
            health['status'] = 'unhealthy'
            health['issues'].append(f'Health check failed: {e}')

        return health

    def close(self):
        """Close Redis connections"""
        if self.redis_client:
            self.redis_client.close()

        if self.async_redis_client:
            # Close async connection (should be awaited)
            try:
                import asyncio
                asyncio.create_task(self.async_redis_client.close())
            except:
                pass

        logger.info("Cache manager connections closed")

# Global cache manager instance
cache_manager = CacheManager()

# Decorator for caching function results
def cached(ttl: int = 300, namespace: str = None, key_func: Callable = None):
    """
    Decorator for caching function results

    Args:
        ttl: Time to live in seconds
        namespace: Cache namespace
        key_func: Function to generate cache key from arguments
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()

            # Try to get from cache
            cached_result = cache_manager.get(cache_key, namespace)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl, namespace)

            return result

        return wrapper
    return decorator

# Async version of cached decorator
def async_cached(ttl: int = 300, namespace: str = None, key_func: Callable = None):
    """
    Decorator for caching async function results
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()

            # Try to get from cache
            cached_result = await cache_manager.get_async(cache_key, namespace)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set_async(cache_key, result, ttl, namespace)

            return result

        return wrapper
    return decorator

# Utility functions for common caching patterns
def cache_user_data(user_id: str, data: Any, ttl: int = 900):
    """Cache user-specific data"""
    cache_manager.set(f"user:{user_id}", data, ttl, "users")

def get_cached_user_data(user_id: str) -> Optional[Any]:
    """Get cached user data"""
    return cache_manager.get(f"user:{user_id}", "users")

def cache_complaint_data(complaint_id: str, data: Any, ttl: int = 1800):
    """Cache complaint-specific data"""
    cache_manager.set(f"complaint:{complaint_id}", data, ttl, "complaints")

def get_cached_complaint_data(complaint_id: str) -> Optional[Any]:
    """Get cached complaint data"""
    return cache_manager.get(f"complaint:{complaint_id}", "complaints")

def cache_prediction_data(location_id: int, data: Any, ttl: int = 600):
    """Cache prediction data"""
    cache_manager.set(f"location:{location_id}", data, ttl, "predictions")

def get_cached_prediction_data(location_id: int) -> Optional[Any]:
    """Get cached prediction data"""
    return cache_manager.get(f"location:{location_id}", "predictions")

def invalidate_user_cache(user_id: str):
    """Invalidate all cached data for a user"""
    cache_manager.delete(f"user:{user_id}", "users")

def invalidate_complaint_cache(complaint_id: str):
    """Invalidate all cached data for a complaint"""
    cache_manager.delete(f"complaint:{complaint_id}", "complaints")

def clear_expired_cache():
    """Clear expired cache entries (handled by Redis TTL automatically)"""
    logger.info("Expired cache entries cleared by Redis TTL")

# Export cache manager and utilities
__all__ = [
    'CacheManager',
    'CacheConfig',
    'CacheStats',
    'CacheStrategy',
    'CacheLevel',
    'cache_manager',
    'cached',
    'async_cached',
    'cache_user_data',
    'get_cached_user_data',
    'cache_complaint_data',
    'get_cached_complaint_data',
    'cache_prediction_data',
    'get_cached_prediction_data',
    'invalidate_user_cache',
    'invalidate_complaint_cache',
    'clear_expired_cache'
]