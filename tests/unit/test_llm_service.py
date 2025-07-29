import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.llm_service import OllamaService

class TestOllamaService:
    @pytest.fixture
    def llm_service(self):
        return OllamaService()
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, llm_service):
        mock_response_data = {
            "response": "Это тестовый ответ от LLM",
            "done": True
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await llm_service.generate_response("Тестовый вопрос")
            
            assert result == "Это тестовый ответ от LLM"
    
    @pytest.mark.asyncio
    async def test_generate_response_timeout(self, llm_service):
        import httpx
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.TimeoutException("Timeout")
            
            result = await llm_service.generate_response("Тестовый вопрос")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_check_connection_success(self, llm_service):
        mock_response_data = {
            "models": [
                {"name": "llama2"},
                {"name": "mistral"}
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await llm_service.check_connection()
            
            assert result == True
    
    def test_build_prompt_with_context(self, llm_service):
        prompt = "Тестовый вопрос"
        context = "Тестовый контекст"
        
        result = llm_service._build_prompt(prompt, context)
        
        assert "Контекст: Тестовый контекст" in result
        assert "Вопрос: Тестовый вопрос" in result
    
    def test_build_prompt_without_context(self, llm_service):
        prompt = "Тестовый вопрос"
        
        result = llm_service._build_prompt(prompt)
        
        assert "Вопрос: Тестовый вопрос" in result
        assert "Контекст:" not in result
    
    @pytest.mark.asyncio
    async def test_generate_response_network_error(self, llm_service):
        import httpx
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.NetworkError("Network error")
            
            result = await llm_service.generate_response("Тестовый вопрос")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_check_connection_failure(self, llm_service):
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Connection failed")
            
            result = await llm_service.check_connection()
            
            assert result == False 