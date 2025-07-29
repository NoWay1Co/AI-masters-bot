import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User, Chat, CallbackQuery

from src.bot.handlers.start import start_command
from src.bot.states.user_states import UserStates
from src.data.models import UserProfile

class TestBotScenarios:
    @pytest.fixture
    def mock_message(self):
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=User)
        message.from_user.id = 123456
        message.from_user.username = "testuser"
        message.chat = MagicMock(spec=Chat)
        message.answer = AsyncMock()
        return message
    
    @pytest.fixture
    def mock_state(self):
        state = MagicMock(spec=FSMContext)
        state.set_state = AsyncMock()
        state.get_data = AsyncMock(return_value={})
        state.update_data = AsyncMock()
        return state
    
    @pytest.fixture
    def existing_user_profile(self):
        return UserProfile(
            user_id="123456",
            username="existing_user",
            background="Computer Science",
            interests=["Machine Learning", "Data Science"],
            goals=["career change"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_new_user_onboarding(self, mock_message, mock_state):
        # Тестируем процесс регистрации нового пользователя
        with patch('src.data.json_storage.storage.load_user_profile', return_value=None):
            await start_command(mock_message, mock_state)
            
            # Проверяем, что пользователь получил ответ
            mock_message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_returning_user_flow(self, mock_message, mock_state, existing_user_profile):
        # Тестируем возвращающегося пользователя
        with patch('src.data.json_storage.storage.load_user_profile', return_value=existing_user_profile):
            await start_command(mock_message, mock_state)
            
            # Проверяем, что пользователь получил ответ
            mock_message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multiple_user_sessions(self, mock_state):
        # Тестируем работу с несколькими пользователями
        users_data = [
            ("111111", "User One"),
            ("222222", "User Two"), 
            ("333333", "User Three")
        ]
        
        for user_id, username in users_data:
            # Создаем отдельное сообщение для каждого пользователя
            message = MagicMock(spec=Message)
            message.from_user = MagicMock(spec=User)
            message.from_user.id = int(user_id)
            message.answer = AsyncMock()
            
            profile = UserProfile(
                user_id=user_id,
                username=username,
                background="Test background",
                interests=["AI"],
                goals=["skill improvement"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            with patch('src.data.json_storage.storage.load_user_profile', return_value=profile):
                await start_command(message, mock_state)
                
                # Проверяем, что каждый пользователь получил ответ
                message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_exception(self, mock_message, mock_state):
        # Тестируем обработку исключений
        with patch('src.data.json_storage.storage.load_user_profile', side_effect=Exception("Database error")):
            # Не должно падать с исключением
            try:
                await start_command(mock_message, mock_state)
                # Если дошли сюда, значит исключение обработано
                assert True
            except Exception:
                # Если исключение не обработано, тест провален
                assert False, "Exception not handled properly" 