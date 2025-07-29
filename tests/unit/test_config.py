import pytest
from unittest.mock import patch
import os
from src.utils.config import settings, Settings

class TestConfig:
    
    def test_config_default_values(self):
        # Тестируем значения по умолчанию
        assert settings.OLLAMA_BASE_URL == 'http://localhost:11434'
        assert settings.OLLAMA_MODEL == 'llama3'
        assert settings.LOG_LEVEL == 'INFO'
        assert settings.TELEGRAM_TOKEN == ''
    
    def test_config_telegram_token_type(self):
        # Тестируем тип токена
        assert isinstance(settings.TELEGRAM_TOKEN, str)
    
    def test_config_ollama_url_type(self):
        # Тестируем тип URL
        assert isinstance(settings.OLLAMA_BASE_URL, str)
        assert settings.OLLAMA_BASE_URL.startswith('http')
    
    def test_config_data_dir_exists(self):
        # Тестируем путь к данным
        from pathlib import Path
        assert isinstance(settings.DATA_DIR, Path)
    
    def test_config_log_level_valid(self):
        # Тестируем валидность уровня логирования
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        assert settings.LOG_LEVEL in valid_levels
    
    def test_settings_class_attributes(self):
        # Тестируем наличие всех атрибутов в классе Settings
        config = Settings()
        
        assert hasattr(config, 'TELEGRAM_TOKEN')
        assert hasattr(config, 'OLLAMA_BASE_URL')
        assert hasattr(config, 'OLLAMA_MODEL')
        assert hasattr(config, 'DATA_DIR')
        assert hasattr(config, 'LOG_LEVEL') 