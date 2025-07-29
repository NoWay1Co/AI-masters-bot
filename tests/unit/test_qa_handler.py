import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User, Chat, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.bot.handlers.qa import process_question, enter_qa_mode
from src.bot.states.user_states import UserStates
from src.data.models import UserProfile, ProgramType

class TestQAHandler:
    @pytest.fixture
    def mock_message(self):
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=User)
        message.from_user.id = 123456
        message.from_user.username = "testuser"
        message.chat = MagicMock(spec=Chat)
        message.text = "Что такое машинное обучение?"
        message.answer = AsyncMock()
        return message
    
    @pytest.fixture
    def mock_callback_query(self):
        callback_query = MagicMock(spec=CallbackQuery)
        callback_query.from_user = MagicMock(spec=User)
        callback_query.from_user.id = 123456
        callback_query.data = "qa_mode"
        callback_query.message = MagicMock(spec=Message)
        callback_query.message.edit_text = AsyncMock()
        callback_query.answer = AsyncMock()
        return callback_query
    
    @pytest.fixture
    def mock_state(self):
        state = MagicMock(spec=FSMContext)
        state.set_state = AsyncMock()
        state.get_data = AsyncMock(return_value={})
        state.update_data = AsyncMock()
        return state
    
    @pytest.mark.asyncio
    async def test_enter_qa_mode(self, mock_callback_query, mock_state):
        # Тестируем вход в режим QA
        await enter_qa_mode(mock_callback_query, mock_state)
        
        mock_callback_query.message.edit_text.assert_called_once()
        mock_state.set_state.assert_called_once()
        mock_callback_query.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_question_success(self, mock_message, mock_state):
        # Тестируем успешную обработку вопроса
        with patch('src.bot.handlers.qa.storage.load_programs', return_value=[]), \
             patch('src.bot.handlers.qa.llm_service.answer_question', return_value="Тестовый ответ"):
            
            await process_question(mock_message, mock_state)
            
            # Проверяем, что ответ был отправлен
            assert mock_message.answer.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_process_question_menu_command(self, mock_message, mock_state):
        # Тестируем команду возврата в меню
        mock_message.text = "/menu"
        
        await process_question(mock_message, mock_state)
        
        mock_message.answer.assert_called_once()
        mock_state.set_state.assert_called_once_with(UserStates.MAIN_MENU)
    
    @pytest.mark.asyncio
    async def test_process_question_short_text(self, mock_message, mock_state):
        # Тестируем короткий вопрос
        mock_message.text = "Что"
        
        await process_question(mock_message, mock_state)
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "развернутый" in call_args
    
    @pytest.mark.asyncio
    async def test_process_question_irrelevant(self, mock_message, mock_state):
        # Тестируем нерелевантный вопрос
        mock_message.text = "Какая сегодня погода?"
        
        await process_question(mock_message, mock_state)
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "только на вопросы" in call_args
    
    @pytest.mark.asyncio
    async def test_process_question_llm_failure(self, mock_message, mock_state):
        # Тестируем ошибку LLM
        with patch('src.bot.handlers.qa.storage.load_programs', return_value=[]), \
             patch('src.bot.handlers.qa.llm_service.answer_question', return_value=None):
            
            await process_question(mock_message, mock_state)
            
            # Проверяем, что было отправлено сообщение об ошибке
            assert mock_message.answer.call_count >= 1 