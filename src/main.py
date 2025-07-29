import asyncio
from src.utils.logger import setup_logging, logger
from src.utils.config import settings

async def main():
    setup_logging()
    logger.info("Starting AI Masters Bot", version="1.0.0")
    
    if not settings.TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN is not set. Please check your .env file")
        return
    
    logger.info("Bot configuration loaded", 
                ollama_url=settings.OLLAMA_BASE_URL,
                data_dir=str(settings.DATA_DIR))
    
    logger.info("Bot started successfully")

if __name__ == "__main__":
    asyncio.run(main()) 