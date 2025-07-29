import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from src.services.cache_service import CacheService


class TestCacheService:
    @pytest.fixture
    def cache_service(self):
        return CacheService()
    
    @pytest.mark.asyncio
    async def test_set_and_get_cache(self, cache_service):
        key = "test_key"
        value = {"test": "data"}
        
        await cache_service.set(key, value, 3600)
        result = await cache_service.get(key)
        
        assert result == value
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache_service):
        result = await cache_service.get("nonexistent_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache_service):
        key = "test_key"
        value = {"test": "data"}
        
        # Set cache with very short TTL
        await cache_service.set(key, value, 0.001)
        
        # Wait for expiration
        import asyncio
        await asyncio.sleep(0.002)
        
        result = await cache_service.get(key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_invalidate_cache(self, cache_service):
        key = "test_key"
        value = {"test": "data"}
        
        await cache_service.set(key, value, 3600)
        await cache_service.invalidate(key)
        
        result = await cache_service.get(key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, cache_service):
        await cache_service.set("user_123_profile", {"id": 123}, 3600)
        await cache_service.set("user_456_profile", {"id": 456}, 3600)
        await cache_service.set("program_data", {"name": "AI"}, 3600)
        
        await cache_service.invalidate_pattern("user_*")
        
        assert await cache_service.get("user_123_profile") is None
        assert await cache_service.get("user_456_profile") is None
        assert await cache_service.get("program_data") is not None
    
    @pytest.mark.asyncio
    async def test_clear_all_cache(self, cache_service):
        await cache_service.set("key1", "value1", 3600)
        await cache_service.set("key2", "value2", 3600)
        
        await cache_service.clear()
        
        assert await cache_service.get("key1") is None
        assert await cache_service.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_cache_with_complex_data(self, cache_service):
        complex_data = {
            "list": [1, 2, 3],
            "nested": {"inner": "value"},
            "datetime": datetime.now().isoformat()
        }
        
        await cache_service.set("complex_key", complex_data, 3600)
        result = await cache_service.get("complex_key")
        
        assert result == complex_data
    
    def test_is_expired(self, cache_service):
        # Test expired entry
        expired_time = datetime.now() - timedelta(hours=1)
        assert cache_service._is_expired(expired_time)
        
        # Test valid entry
        valid_time = datetime.now() + timedelta(hours=1)
        assert not cache_service._is_expired(valid_time) 