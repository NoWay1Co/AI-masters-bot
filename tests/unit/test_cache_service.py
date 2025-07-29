import pytest
import asyncio
from datetime import datetime, timedelta
from src.services.cache_service import CacheService


class TestCacheService:
    @pytest.fixture
    def cache(self):
        return CacheService()
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache):
        key = "test_key"
        value = {"data": "test_value"}
        
        await cache.set(key, value)
        result = await cache.get(key)
        
        assert result == value
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        result = await cache.get("nonexistent_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache):
        key = "expire_key"
        value = "expire_value"
        short_ttl = timedelta(milliseconds=1)
        
        await cache.set(key, value, short_ttl)
        
        # Wait for expiration
        await asyncio.sleep(0.002)
        
        result = await cache.get(key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, cache):
        key = "delete_key"
        value = "delete_value"
        
        await cache.set(key, value)
        await cache.delete(key)
        
        result = await cache.get(key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, cache):
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        await cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, cache):
        # Set items with very short TTL
        short_ttl = timedelta(milliseconds=1)
        await cache.set("key1", "value1", short_ttl)
        await cache.set("key2", "value2", timedelta(hours=1))
        
        # Wait for first item to expire
        await asyncio.sleep(0.002)
        
        await cache.cleanup_expired()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") == "value2"
    
    @pytest.mark.asyncio
    async def test_cache_with_custom_ttl(self, cache):
        key = "ttl_key"
        value = "ttl_value"
        custom_ttl = timedelta(seconds=1)
        
        await cache.set(key, value, custom_ttl)
        result = await cache.get(key)
        
        assert result == value 