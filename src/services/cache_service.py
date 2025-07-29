import asyncio
from typing import Any, Optional, Dict, Tuple
from datetime import datetime, timedelta
from ..utils.logger import logger

class CacheService:
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._default_ttl = timedelta(hours=1)
    
    async def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expires_at = self._cache[key]
            if datetime.now() < expires_at:
                logger.debug("Cache hit", key=key)
                return value
            else:
                del self._cache[key]
                logger.debug("Cache expired", key=key)
        
        logger.debug("Cache miss", key=key)
        return None
    
    async def set(self, key: str, value: Any, ttl: timedelta = None) -> None:
        if ttl is None:
            ttl = self._default_ttl
        
        expires_at = datetime.now() + ttl
        self._cache[key] = (value, expires_at)
        logger.debug("Cache set", key=key, ttl_seconds=ttl.total_seconds())
    
    async def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]
            logger.debug("Cache deleted", key=key)
    
    async def clear(self) -> None:
        self._cache.clear()
        logger.info("Cache cleared")
    
    async def cleanup_expired(self) -> None:
        now = datetime.now()
        expired_keys = [
            key for key, (_, expires_at) in self._cache.items()
            if now >= expires_at
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info("Expired cache entries removed", count=len(expired_keys))

cache_service = CacheService() 