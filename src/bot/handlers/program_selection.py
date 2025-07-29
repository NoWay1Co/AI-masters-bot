from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime
from typing import List

from ..states.user_states import UserStates
from ..keyboards.inline_keyboards import (
    get_main_menu_keyboard, get_interests_keyboard, 
    get_goals_keyboard, get_profile_setup_keyboard
)
from ...data.models import UserProfile
from ...data.json_storage import storage
from ...utils.logger import logger

router = Router() 

@router.callback_query(F.data == "set_background")
async def set_background(callback: CallbackQuery, state: FSMContext):
    # Очистка только поля background из FSM состояния
    data = await state.get_data()
    data.pop("background", None)
    await state.set_data(data)
    
    await callback.message.edit_text(
        "Расскажите о своем образовании и опыте работы:\n\n"
        "Например: 'Бакалавр информатики, работаю junior разработчиком'"
    )
    await state.set_state(UserStates.COLLECTING_BACKGROUND)
    await callback.answer()

@router.message(UserStates.COLLECTING_BACKGROUND)
async def process_background(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    background = message.text.strip()
    
    logger.info("Processing background", user_id=user_id, background_length=len(background))
    
    if len(background) < 10:
        await message.answer("Пожалуйста, опишите ваше образование более подробно (минимум 10 символов).")
        return
    
    await state.update_data(background=background)
    logger.info("Background saved", user_id=user_id)
    
    await message.answer(
        "Спасибо! Теперь выберите ваши интересы:",
        reply_markup=get_interests_keyboard()
    )
    await state.set_state(UserStates.COLLECTING_INTERESTS)
    logger.info("State changed to COLLECTING_INTERESTS", user_id=user_id)

@router.callback_query(F.data == "set_interests")
async def set_interests(callback: CallbackQuery, state: FSMContext):
    # Очистка только поля interests из FSM состояния
    data = await state.get_data()
    data.pop("interests", None)
    await state.set_data(data)
    
    await callback.message.edit_text(
        "Выберите ваши интересы (можно выбрать несколько):",
        reply_markup=get_interests_keyboard()
    )
    await state.set_state(UserStates.COLLECTING_INTERESTS)
    await callback.answer()

@router.callback_query(F.data.startswith("int_"))
async def process_interest(callback: CallbackQuery, state: FSMContext):
    interest_code = callback.data.replace("int_", "")
    
    # Если это команда "done", обрабатываем отдельно
    if interest_code == "done":
        await interests_done(callback, state)
        return
    
    # Мапинг кодов на полные названия
    interest_mapping = {
        "ml": "Машинное обучение",
        "cv": "Компьютерное зрение", 
        "nlp": "NLP",
        "robotics": "Робототехника",
        "products": "Продукты",
        "data": "Данные",
        "research": "Исследования",
        "startup": "Стартапы",
        "web": "Веб-разработка",
        "mobile": "Мобильная разработка",
        "gamedev": "Игровая разработка",
        "security": "Кибербезопасность",
        "blockchain": "Блокчейн",
        "iot": "IoT",
        "arvr": "AR/VR",
        "devops": "DevOps",
        "design": "UI/UX дизайн",
        "bioinformatics": "Биоинформатика"
    }
    
    interest_name = interest_mapping.get(interest_code, interest_code)
    
    data = await state.get_data()
    interests = data.get("interests", [])
    
    # Добавляем интерес только если его еще нет
    if interest_name not in interests:
        interests.append(interest_name)
        await state.update_data(interests=interests)
        
        # Обновляем сообщение только если список изменился
        interests_text = "Выбранные интересы:\n" + "\n".join(f"- {interest}" for interest in interests)
        
        await callback.message.edit_text(
            f"{interests_text}\n\nВыберите еще или нажмите 'Готово':",
            reply_markup=get_interests_keyboard()
        )
    
    await callback.answer()

async def interests_done(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Отлично! Теперь выберите ваши цели:",
        reply_markup=get_goals_keyboard()
    )
    await state.set_state(UserStates.COLLECTING_GOALS)
    await callback.answer()

@router.callback_query(F.data == "set_goals")
async def set_goals(callback: CallbackQuery, state: FSMContext):
    # Очистка только поля goals из FSM состояния
    data = await state.get_data()
    data.pop("goals", None)
    await state.set_data(data)
    
    await callback.message.edit_text(
        "Выберите ваши цели (можно выбрать несколько):",
        reply_markup=get_goals_keyboard()
    )
    await state.set_state(UserStates.COLLECTING_GOALS)
    await callback.answer()

@router.callback_query(F.data.startswith("goal_"))
async def process_goal(callback: CallbackQuery, state: FSMContext):
    goal_code = callback.data.replace("goal_", "")
    
    # Если это команда "goal_done", обрабатываем отдельно
    if goal_code == "done":
        await goals_done(callback, state)
        return
    
    # Мапинг кодов на полные названия
    goal_mapping = {
        "career": "Карьера в IT",
        "science": "Научная деятельность", 
        "startup": "Создание стартапа",
        "change": "Смена профессии",
        "knowledge": "Углубить знания",
        "diploma": "Получить диплом"
    }
    
    goal_name = goal_mapping.get(goal_code, goal_code)
    
    data = await state.get_data()
    goals = data.get("goals", [])
    
    # Добавляем цель только если ее еще нет
    if goal_name not in goals:
        goals.append(goal_name)
        await state.update_data(goals=goals)
        
        # Обновляем сообщение только если список изменился
        goals_text = "Выбранные цели:\n" + "\n".join(f"- {goal}" for goal in goals)
        
        await callback.message.edit_text(
            f"{goals_text}\n\nВыберите еще или нажмите 'Готово':",
            reply_markup=get_goals_keyboard()
        )
    
    await callback.answer()

@router.callback_query(F.data == "goal_done")
async def goals_done(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    username = callback.from_user.username
    
    data = await state.get_data()
    existing_profile = await storage.load_user_profile(user_id)
    
    # Использовать только данные из FSM state, не fallback к существующему профилю
    user_profile = UserProfile(
        user_id=user_id,
        username=username,
        background=data.get("background", ""),  # Только из FSM state
        interests=data.get("interests", []),    # Только из FSM state  
        goals=data.get("goals", []),           # Только из FSM state
        created_at=existing_profile.created_at if existing_profile else datetime.now(),
        updated_at=datetime.now()
    )
    
    await storage.save_user_profile(user_profile)
    
    await callback.message.edit_text(
        "Профиль обновлен! Теперь вы можете получить персональные рекомендации.",
        reply_markup=get_main_menu_keyboard()
    )
    
    await state.set_state(UserStates.MAIN_MENU)
    await callback.answer()
    
    logger.info("User profile updated", user_id=user_id, interests_count=len(user_profile.interests))

@router.callback_query(F.data == "skip_profile")
async def skip_profile(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    username = callback.from_user.username
    
    # Проверяем есть ли уже данные в состоянии или существующий профиль
    data = await state.get_data()
    existing_profile = await storage.load_user_profile(user_id)
    
    # Используем существующие данные если они есть
    background = data.get("background", "") or (existing_profile.background if existing_profile else "")
    interests = data.get("interests", []) or (existing_profile.interests if existing_profile else [])
    goals = data.get("goals", []) or (existing_profile.goals if existing_profile else [])
    
    user_profile = UserProfile(
        user_id=user_id,
        username=username,
        background=background,
        interests=interests,
        goals=goals,
        created_at=existing_profile.created_at if existing_profile else datetime.now(),
        updated_at=datetime.now()
    )
    
    await storage.save_user_profile(user_profile)
    
    await callback.message.edit_text(
        "Профиль сохранен! Вы можете дополнить его позже.",
        reply_markup=get_main_menu_keyboard()
    )
    
    await state.set_state(UserStates.MAIN_MENU)
    await callback.answer() 