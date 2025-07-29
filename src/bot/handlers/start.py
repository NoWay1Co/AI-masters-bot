from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from ...data.json_storage import storage
from ...data.models import UserProfile
from ...utils.logger import logger
from ..keyboards.inline_keyboards import create_main_menu_keyboard
from datetime import datetime

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    
    user_id = str(message.from_user.id)
    username = message.from_user.username
    
    # Проверяем существующий профиль
    existing_profile = await storage.load_user_profile(user_id)
    
    if existing_profile:
        welcome_text = f"Добро пожаловать обратно, {username or 'пользователь'}!"
    else:
        # Создаем базовый профиль
        new_profile = UserProfile(
            user_id=user_id,
            username=username,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        await storage.save_user_profile(new_profile)
        welcome_text = f"Добро пожаловать, {username or 'пользователь'}! Профиль создан."
        
        logger.info("New user registered", user_id=user_id, username=username)
    
    await message.reply(
        f"{welcome_text}\n\n"
        "Это бот-помощник для абитуриентов магистратуры ИТМО по направлениям ИИ.\n\n"
        "Выберите действие:",
        reply_markup=create_main_menu_keyboard()
    )

@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        "Главное меню:\n\n"
        "Выберите действие:",
        reply_markup=create_main_menu_keyboard()
    ) 