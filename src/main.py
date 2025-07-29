import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.utils.logger import setup_logging, logger
from src.utils.config import settings
from src.services.llm_service import llm_service
from src.bot.handlers import start, recommendations, qa, program_selection
from src.bot.middlewares.logging_middleware import LoggingMiddleware

async def main():
    setup_logging()
    logger.info("Starting AI Masters Bot", version="1.0.0")
    
    if not settings.TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN is not set. Please check your .env file")
        return
    
    # Проверяем подключение к Ollama
    logger.info("Checking Ollama connection...")
    ollama_available = await llm_service.check_connection()
    if ollama_available:
        logger.info("Ollama connection successful")
    else:
        logger.warning("Ollama connection failed - using fallback mode")
    
    # Создаем бота и диспетчер
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Подключаем middleware
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    # Подключаем роутеры
    dp.include_router(start.router)
    dp.include_router(recommendations.router)
    dp.include_router(qa.router)
    dp.include_router(program_selection.router)
    
    logger.info("Bot configuration loaded", 
                ollama_url=settings.OLLAMA_BASE_URL,
                ollama_model=settings.OLLAMA_MODEL,
                data_dir=str(settings.DATA_DIR))
    
    try:
        logger.info("Bot started successfully")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Bot crashed", error=str(e))
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main()) 