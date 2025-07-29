import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.llm_service import OllamaService

@pytest.fixture
def llm_service():
    return OllamaService()

@pytest.mark.asyncio
async def test_generate_response_success(llm_service):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Test LLM response"}
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await llm_service.generate_response("Test prompt")
        
        assert result == "Test LLM response"
        mock_client.return_value.__aenter__.return_value.post.assert_called_once()

@pytest.mark.asyncio
async def test_generate_response_with_context(llm_service):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Contextual response"}
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await llm_service.generate_response("Test prompt", "Test context")
        
        assert result == "Contextual response"

@pytest.mark.asyncio
async def test_generate_response_timeout(llm_service):
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )
        
        result = await llm_service.generate_response("Test prompt")
        
        assert result is None

@pytest.mark.asyncio
async def test_generate_response_http_error(llm_service):
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.HTTPStatusError("HTTP Error", request=None, response=mock_response)
        )
        
        result = await llm_service.generate_response("Test prompt")
        
        assert result is None

@pytest.mark.asyncio
async def test_check_connection_success(llm_service):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "models": [{"name": "llama3"}, {"name": "other_model"}]
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await llm_service.check_connection()
        
        assert result is True

@pytest.mark.asyncio
async def test_check_connection_model_not_available(llm_service):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "models": [{"name": "other_model"}]
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await llm_service.check_connection()
        
        assert result is False

@pytest.mark.asyncio
async def test_check_connection_failure(llm_service):
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection failed")
        )
        
        result = await llm_service.check_connection()
        
        assert result is False

@pytest.mark.asyncio
async def test_generate_recommendations(llm_service):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "AI program recommendation"}
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await llm_service.generate_recommendations(
            "User profile", "Programs data"
        )
        
        assert result == "AI program recommendation"

@pytest.mark.asyncio
async def test_answer_question(llm_service):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Answer to question"}
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await llm_service.answer_question("Test question", "Context")
        
        assert result == "Answer to question"

def test_build_prompt_with_context(llm_service):
    result = llm_service._build_prompt("Test prompt", "Test context")
    assert "Контекст: Test context" in result
    assert "Вопрос: Test prompt" in result

def test_build_prompt_without_context(llm_service):
    result = llm_service._build_prompt("Test prompt")
    assert result == "Test prompt" 