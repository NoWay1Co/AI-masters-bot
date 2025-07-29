import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .utils.config import settings
from .utils.logger import setup_logging, logger
from .bot.handlers import start, program_selection, recommendations, qa
from .bot.middlewares.logging_middleware import LoggingMiddleware
from .services.llm_service import llm_service
from .services.parser_service import ITMOParser
from .data.json_storage import storage

async def on_startup():
    logger.info("Bot starting up...")
    
    # Проверяем подключение к Ollama
    ollama_available = await llm_service.check_connection()
    if not ollama_available:
        logger.warning("Ollama not available, some features may not work")
    
    # Парсим данные программ при старте
    try:
        parser = ITMOParser()
        programs = await parser.parse_all_programs()
        
        if programs:
            await storage.save_programs(programs)
            logger.info("Programs data updated", count=len(programs))
        else:
            logger.warning("No programs data obtained")
    
    except Exception as e:
        logger.error("Failed to parse programs on startup", error=str(e))
    
    logger.info("Bot startup completed")

async def on_shutdown():
    logger.info("Bot shutting down...")

async def create_bot() -> Bot:
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    return bot

async def create_dispatcher() -> Dispatcher:
    storage_fsm = MemoryStorage()
    dp = Dispatcher(storage=storage_fsm)
    
    # Добавляем middleware
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    # Регистрируем роутеры (порядок важен!)
    dp.include_router(program_selection.router)
    dp.include_router(recommendations.router)
    dp.include_router(qa.router)
    dp.include_router(start.router)
    
    # Регистрируем события
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    return dp

async def main():
    setup_logging()
    
    bot = await create_bot()
    dp = await create_dispatcher()
    
    logger.info("Starting bot polling...")
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Bot crashed", error=str(e))
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main()) 