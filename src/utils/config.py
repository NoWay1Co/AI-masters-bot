from decouple import config
from pathlib import Path

class Settings:
    TELEGRAM_TOKEN: str = config('TELEGRAM_TOKEN', default='')
    OLLAMA_BASE_URL: str = config('OLLAMA_BASE_URL', default='http://localhost:11434')
    OLLAMA_MODEL: str = config('OLLAMA_MODEL', default='llama3')
    DATA_DIR: Path = Path(config('DATA_DIR', default='data'))
    LOG_LEVEL: str = config('LOG_LEVEL', default='INFO')
    
settings = Settings() 