import httpx
import asyncio
from typing import Optional, List, Dict
from ..utils.logger import logger
from ..utils.config import settings

class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = 10.0  # Уменьшаем для быстрого fallback
    
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> Optional[str]:
        try:
            full_prompt = self._build_prompt(prompt, context)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "max_tokens": 500
                        }
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                generated_text = result.get("response", "").strip()
                
                logger.info(
                    "LLM response generated",
                    model=self.model,
                    prompt_length=len(prompt),
                    response_length=len(generated_text)
                )
                
                return generated_text
        
        except httpx.TimeoutException:
            logger.error("LLM request timeout", timeout=self.timeout)
            return None
        except httpx.HTTPStatusError as e:
            logger.error("LLM HTTP error", status_code=e.response.status_code, error=str(e))
            return None
        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            return None
    
    async def generate_recommendations(self, user_profile: str, programs_data: str) -> Optional[str]:
        prompt = f"""
        Ты - консультант по образованию в области искусственного интеллекта.
        
        Профиль пользователя:
        {user_profile}
        
        Доступные программы обучения:
        {programs_data}
        
        Задача: Проанализируй профиль пользователя и рекомендуй подходящую программу обучения и выборочные дисциплины.
        
        Ответ должен быть структурированным и содержать:
        1. Рекомендуемую программу с обоснованием
        2. Конкретные выборочные дисциплины
        3. Краткий план развития
        
        Ответ:
        """
        
        return await self.generate_response(prompt)
    
    async def answer_question(self, question: str, context: str = None) -> Optional[str]:
        context_info = ""
        if context:
            context_info = f"""
            Контекст о программах обучения:
            {context}
            """
        
        prompt = f"""
        Ты - консультант по магистерским программам ИТМО в области искусственного интеллекта.
        
        {context_info}
        
        Вопрос пользователя: {question}
        
        Задачи:
        1. Отвечай только на вопросы о магистерских программах ИТМО по ИИ, курсах, поступлении и обучении
        2. Используй предоставленную информацию о программах для точных ответов
        3. Если вопрос не связан с темой, вежливо перенаправь к образовательным программам
        4. Давай структурированные и информативные ответы
        5. Если информации недостаточно, рекомендуй обратиться к приемной комиссии
        
        Ответ должен быть полезным, точным и не превышать 500 слов.
        
        Ответ:
        """
        
        return await self.generate_response(prompt)
    
    def _build_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        if context:
            return f"Контекст: {context}\n\nВопрос: {prompt}"
        return prompt
    
    async def check_connection(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                
                models = response.json().get("models", [])
                available_models = [model["name"] for model in models]
                
                if self.model not in available_models:
                    logger.warning(
                        "Configured model not available",
                        model=self.model,
                        available_models=available_models
                    )
                    return False
                
                logger.info("Ollama connection successful", model=self.model)
                return True
        
        except Exception as e:
            logger.error("Failed to connect to Ollama", error=str(e))
            return False

llm_service = OllamaService() 