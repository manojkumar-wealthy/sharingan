"""
Cache Service for agent response caching.

Provides Redis-based caching for expensive agent operations
to improve response times and reduce API calls.
"""

import hashlib
import json
from typing import Any, Optional
from functools import lru_cache

from pydantic import BaseModel

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    Agent response caching service.
    
    Uses Redis for caching agent outputs to:
    - Reduce redundant computations
    - Improve response times
    - Lower external API usage
    """

    def __init__(self):
        self.settings = get_settings()
        self._redis = None
        self._enabled = self.settings.ENABLE_CACHING

    @property
    def redis(self):
        """Lazy initialization of Redis client."""
        if self._redis is None and self._enabled:
            try:
                import redis
                self._redis = redis.from_url(
                    self.settings.REDIS_URL,
                    decode_responses=True,
                )
                # Test connection
                self._redis.ping()
                logger.info("redis_connected")
            except Exception as e:
                logger.warning(
                    "redis_connection_failed",
                    error=str(e),
                )
                self._enabled = False
        return self._redis

    def _generate_cache_key(
        self,
        agent_name: str,
        input_data: BaseModel,
    ) -> str:
        """
        Generate a unique cache key from agent name and input.
        
        Args:
            agent_name: Name of the agent
            input_data: Pydantic model input
        
        Returns:
            Cache key string
        """
        # Serialize input to JSON with sorted keys for consistency
        data_json = json.dumps(
            input_data.model_dump(),
            sort_keys=True,
            default=str,
        )
        # Create hash
        data_hash = hashlib.md5(data_json.encode()).hexdigest()
        return f"agent:{agent_name}:{data_hash}"

    async def get(
        self,
        agent_name: str,
        input_data: BaseModel,
    ) -> Optional[dict]:
        """
        Get cached result for an agent.
        
        Args:
            agent_name: Name of the agent
            input_data: Input data used for the agent
        
        Returns:
            Cached result dict or None
        """
        if not self._enabled or not self.redis:
            return None

        try:
            key = self._generate_cache_key(agent_name, input_data)
            cached = self.redis.get(key)
            
            if cached:
                logger.debug(
                    "cache_hit",
                    agent=agent_name,
                    key=key[:50],
                )
                return json.loads(cached)
            
            logger.debug(
                "cache_miss",
                agent=agent_name,
                key=key[:50],
            )
            return None

        except Exception as e:
            logger.warning(
                "cache_get_failed",
                agent=agent_name,
                error=str(e),
            )
            return None

    async def set(
        self,
        agent_name: str,
        input_data: BaseModel,
        output_data: BaseModel,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Cache an agent result.
        
        Args:
            agent_name: Name of the agent
            input_data: Input data used
            output_data: Output to cache
            ttl_seconds: Optional TTL override
        
        Returns:
            True if cached successfully
        """
        if not self._enabled or not self.redis:
            return False

        try:
            key = self._generate_cache_key(agent_name, input_data)
            ttl = ttl_seconds or self.settings.CACHE_TTL_SECONDS
            
            value = json.dumps(
                output_data.model_dump(),
                default=str,
            )
            
            self.redis.setex(key, ttl, value)
            
            logger.debug(
                "cache_set",
                agent=agent_name,
                key=key[:50],
                ttl=ttl,
            )
            return True

        except Exception as e:
            logger.warning(
                "cache_set_failed",
                agent=agent_name,
                error=str(e),
            )
            return False

    async def invalidate(
        self,
        agent_name: str,
        input_data: Optional[BaseModel] = None,
    ) -> bool:
        """
        Invalidate cache entries.
        
        Args:
            agent_name: Name of the agent
            input_data: Optional specific input to invalidate
        
        Returns:
            True if invalidation succeeded
        """
        if not self._enabled or not self.redis:
            return False

        try:
            if input_data:
                # Invalidate specific key
                key = self._generate_cache_key(agent_name, input_data)
                self.redis.delete(key)
            else:
                # Invalidate all keys for agent
                pattern = f"agent:{agent_name}:*"
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
            
            logger.info(
                "cache_invalidated",
                agent=agent_name,
            )
            return True

        except Exception as e:
            logger.warning(
                "cache_invalidation_failed",
                agent=agent_name,
                error=str(e),
            )
            return False

    def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self._enabled or not self.redis:
            return {"enabled": False}

        try:
            info = self.redis.info()
            return {
                "enabled": True,
                "connected": True,
                "used_memory": info.get("used_memory_human"),
                "total_keys": self.redis.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            return {
                "enabled": True,
                "connected": False,
                "error": str(e),
            }


# Global cache service instance
_cache_service: Optional[CacheService] = None


@lru_cache()
def get_cache_service() -> CacheService:
    """Get the global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
