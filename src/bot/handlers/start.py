from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from datetime import datetime

from ..states.user_states import UserStates
from ..keyboards.inline_keyboards import get_main_menu_keyboard, get_profile_setup_keyboard
from ...data.models import UserProfile
from ...data.json_storage import storage
from ...utils.logger import logger

router = Router()

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    
    logger.info("User started bot", user_id=user_id, username=username)
    
    # Проверяем, есть ли уже профиль пользователя
    user_profile = await storage.load_user_profile(user_id)
    
    if user_profile:
        welcome_text = f"С возвращением, {username or 'студент'}! Чем могу помочь?"
        await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())
        await state.set_state(UserStates.MAIN_MENU)
    else:
        welcome_text = """
Добро пожаловать в бот-консультант по магистерским программам ИТМО!

Я помогу вам:
- Выбрать подходящую программу обучения
- Получить рекомендации по выборочным дисциплинам
- Сравнить программы между собой
- Ответить на вопросы об обучении

Для начала давайте создадим ваш профиль.
        """
        
        await message.answer(welcome_text, reply_markup=get_profile_setup_keyboard())
        await state.set_state(UserStates.COLLECTING_BACKGROUND)

@router.message(Command("help"))
async def help_command(message: Message):
    help_text = """
Доступные команды:

/start - Начать работу с ботом
/help - Показать это сообщение
/profile - Просмотреть ваш профиль
/reset - Сбросить профиль и начать заново

Возможности бота:
- Выбор программы обучения
- Персональные рекомендации
- Сравнение программ
- Ответы на вопросы
- Экспорт рекомендаций

Для навигации используйте кнопки в сообщениях.
    """
    
    await message.answer(help_text)

@router.message(Command("profile"))
async def profile_command(message: Message):
    user_id = str(message.from_user.id)
    user_profile = await storage.load_user_profile(user_id)
    
    if not user_profile:
        await message.answer(
            "У вас пока нет профиля. Используйте /start для его создания.",
            reply_markup=get_profile_setup_keyboard()
        )
        return
    
    profile_text = f"""
Ваш профиль:

Образование: {user_profile.background or 'Не указано'}
Интересы: {', '.join(user_profile.interests) if user_profile.interests else 'Не указаны'}
Цели: {', '.join(user_profile.goals) if user_profile.goals else 'Не указаны'}
Предпочитаемая программа: {user_profile.preferred_program.value if user_profile.preferred_program else 'Не выбрана'}

Профиль создан: {user_profile.created_at.strftime('%d.%m.%Y %H:%M')}
Последнее обновление: {user_profile.updated_at.strftime('%d.%m.%Y %H:%M')}
    """
    
    await message.answer(profile_text, reply_markup=get_main_menu_keyboard())

@router.message(Command("reset"))
async def reset_command(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    
    # Удаляем профиль пользователя
    user_file = storage.users_dir / f"{user_id}.json"
    if user_file.exists():
        user_file.unlink()
    
    await state.clear()
    
    await message.answer(
        "Ваш профиль был сброшен. Используйте /start для создания нового.",
        reply_markup=get_profile_setup_keyboard()
    )
    
    logger.info("User profile reset", user_id=user_id)

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    try:
        # Пытаемся отредактировать сообщение (работает для текстовых сообщений)
        await callback.message.edit_text(
            "Главное меню",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception:
        # Если не получается отредактировать (например, сообщение с файлом),
        # отправляем новое сообщение
        await callback.message.answer(
            "Главное меню",
            reply_markup=get_main_menu_keyboard()
        )
    
    await state.set_state(UserStates.MAIN_MENU)
    await callback.answer()

@router.callback_query(F.data == "view_profile")
async def view_profile_callback(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    user_profile = await storage.load_user_profile(user_id)
    
    if not user_profile:
        await callback.message.edit_text(
            "Профиль не найден. Пожалуйста, создайте профиль.",
            reply_markup=get_profile_setup_keyboard()
        )
        await callback.answer()
        return
    
    profile_text = f"""
Ваш профиль:

Образование: {user_profile.background or 'Не указано'}
Интересы: {', '.join(user_profile.interests) if user_profile.interests else 'Не указаны'}
Цели: {', '.join(user_profile.goals) if user_profile.goals else 'Не указаны'}

Хотите изменить профиль?
    """
    
    await callback.message.edit_text(profile_text, reply_markup=get_profile_setup_keyboard())
    await callback.answer()

@router.message(UserStates.MAIN_MENU)
async def main_menu_message(message: Message, state: FSMContext):
    await message.answer(
        "Я не понимаю это сообщение. Используйте кнопки для навигации.",
        reply_markup=get_main_menu_keyboard()
    )

@router.message()
async def unknown_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer(
            "Привет! Используйте /start для начала работы с ботом.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # Для неизвестных состояний просто игнорируем
        pass 