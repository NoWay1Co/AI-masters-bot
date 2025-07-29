import httpx
import asyncio
from typing import Optional, List, Dict
from ..utils.logger import logger
from ..utils.config import settings

class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = 15.0  # Увеличиваем таймаут для более стабильной работы
        self._available_models = []
    
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> Optional[str]:
        try:
            # Проверяем доступность модели и автоматически выбираем доступную
            if not await self._ensure_model_available():
                logger.warning("No suitable model available for generation")
                return None
                
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
                            "max_tokens": 1500,  # Увеличиваем для более подробных ответов
                            "stop": ["Human:", "Assistant:", "User:"]
                        }
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                generated_text = result.get("response", "").strip()
                
                if generated_text:
                    logger.info(
                        "LLM response generated successfully",
                        model=self.model,
                        prompt_length=len(prompt),
                        response_length=len(generated_text)
                    )
                    return generated_text
                else:
                    logger.warning("LLM returned empty response")
                    return None
        
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
Ты мой друг-консультант по магистерским программам ИТМО по ИИ. Отвечай тепло и дружелюбно, как будто общаемся лично.

{context_info}

Вопрос друга: {question}

ВАЖНО:
🎯 Отвечай ТОЛЬКО на основе предоставленных данных о программах
🎯 НЕ добавляй общую информацию - только конкретные рекомендации
🎯 Говори простым, дружеским тоном
🎯 Обращайся на "ты" и используй эмодзи для теплоты

СТРУКТУРА ОТВЕТА:
1. Прямой ответ на вопрос с конкретными данными
2. Персональная рекомендация (если применимо)
3. Следующие шаги

СТИЛЬ: Дружеский, теплый, как разговор с приятелем. Избегай формальности.

Ответ:
"""
        
        return await self.generate_response(prompt)
    
    def _build_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        if context:
            return f"Контекст: {context}\n\nВопрос: {prompt}"
        return prompt
    
    async def _ensure_model_available(self) -> bool:
        """Проверяет доступность модели и автоматически выбирает подходящую"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                
                models = response.json().get("models", [])
                self._available_models = [model["name"] for model in models]
                
                # Проверяем, доступна ли настроенная модель
                if self.model in self._available_models:
                    return True
                
                # Пытаемся найти подходящую модель
                preferred_models = [
                    "llama3:latest", "llama3", "llama2:latest", "llama2",
                    "codellama:latest", "codellama", "mistral:latest", "mistral"
                ]
                
                for preferred in preferred_models:
                    if preferred in self._available_models:
                        old_model = self.model
                        self.model = preferred
                        logger.info(
                            "Auto-selected available model",
                            old_model=old_model,
                            new_model=self.model,
                            available_models=self._available_models
                        )
                        return True
                
                logger.warning(
                    "No suitable model found",
                    configured_model=self.model,
                    available_models=self._available_models
                )
                return False
                
        except Exception as e:
            logger.error("Failed to check model availability", error=str(e))
            return False

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
                    # Пытаемся автоматически выбрать доступную модель
                    return await self._ensure_model_available()
                
                logger.info("Ollama connection successful", model=self.model)
                return True
        
        except Exception as e:
            logger.error("Failed to connect to Ollama", error=str(e))
            return False

llm_service = OllamaService() 