import pytest
from src.utils.config import settings

def test_config_defaults():
    """Test that configuration loads with default values"""
    assert settings.LOG_LEVEL == 'INFO'
    assert settings.OLLAMA_BASE_URL == 'http://localhost:11434'
    assert settings.OLLAMA_MODEL == 'llama3'
    assert str(settings.DATA_DIR) == 'data'

def test_telegram_token_default():
    """Test that TELEGRAM_TOKEN has default empty value"""
    assert isinstance(settings.TELEGRAM_TOKEN, str) 