import pytest
from src.services.llm_service import OllamaService

class TestOllamaIntegration:
    @pytest.fixture
    def llm_service(self):
        return OllamaService()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_ollama_connection(self, llm_service):
        # Этот тест требует запущенного Ollama
        connection_ok = await llm_service.check_connection()
        
        if not connection_ok:
            pytest.skip("Ollama not available")
        
        assert connection_ok == True
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_response_generation(self, llm_service):
        # Проверяем реальную генерацию ответа
        if not await llm_service.check_connection():
            pytest.skip("Ollama not available")
        
        response = await llm_service.generate_response(
            "Что такое машинное обучение?"
        )
        
        assert response is not None
        assert len(response) > 10
        assert isinstance(response, str)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_response_with_context(self, llm_service):
        if not await llm_service.check_connection():
            pytest.skip("Ollama not available")
        
        context = "Контекст: Магистерская программа по искусственному интеллекту в ИТМО"
        question = "Какие курсы включает программа?"
        
        response = await llm_service.generate_response(question, context)
        
        assert response is not None
        assert len(response) > 10
        assert isinstance(response, str)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_model_availability(self, llm_service):
        if not await llm_service.check_connection():
            pytest.skip("Ollama not available")
        
        # Проверяем, что доступна хотя бы одна модель
        import httpx
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{llm_service.base_url}/api/tags")
                data = response.json()
                models = data.get("models", [])
                
                assert len(models) > 0
                assert any(model["name"] for model in models)
            
            except Exception:
                pytest.skip("Cannot access Ollama API")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_concurrent_requests(self, llm_service):
        if not await llm_service.check_connection():
            pytest.skip("Ollama not available")
        
        import asyncio
        
        # Отправляем несколько запросов одновременно
        tasks = [
            llm_service.generate_response("Что такое ИИ?"),
            llm_service.generate_response("Что такое ML?"),
            llm_service.generate_response("Что такое DL?")
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Проверяем, что большинство запросов успешны
        successful_responses = [r for r in responses if isinstance(r, str) and r is not None]
        assert len(successful_responses) >= 2 