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
    await callback.message.edit_text(
        "Расскажите о своем образовании и опыте работы:\n\n"
        "Например: 'Бакалавр информатики, работаю junior разработчиком'"
    )
    await state.set_state(UserStates.COLLECTING_BACKGROUND)
    await callback.answer()

@router.message(UserStates.COLLECTING_BACKGROUND)
async def process_background(message: Message, state: FSMContext):
    background = message.text.strip()
    
    if len(background) < 10:
        await message.answer("Пожалуйста, опишите ваше образование более подробно (минимум 10 символов).")
        return
    
    await state.update_data(background=background)
    
    await message.answer(
        "Спасибо! Теперь выберите ваши интересы:",
        reply_markup=get_interests_keyboard()
    )
    await state.set_state(UserStates.COLLECTING_INTERESTS)

@router.callback_query(F.data == "set_interests")
async def set_interests(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите ваши интересы (можно выбрать несколько):",
        reply_markup=get_interests_keyboard()
    )
    await state.set_state(UserStates.COLLECTING_INTERESTS)
    await callback.answer()

@router.callback_query(F.data.startswith("interest_"))
async def process_interest(callback: CallbackQuery, state: FSMContext):
    interest_key = callback.data.replace("interest_", "").replace("_", " ").title()
    
    data = await state.get_data()
    interests = data.get("interests", [])
    
    if interest_key not in interests:
        interests.append(interest_key)
        await state.update_data(interests=interests)
    
    interests_text = "Выбранные интересы:\n" + "\n".join(f"- {interest}" for interest in interests)
    
    await callback.message.edit_text(
        f"{interests_text}\n\nВыберите еще или нажмите 'Готово':",
        reply_markup=get_interests_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "interests_done")
async def interests_done(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Отлично! Теперь выберите ваши цели:",
        reply_markup=get_goals_keyboard()
    )
    await state.set_state(UserStates.COLLECTING_GOALS)
    await callback.answer()

@router.callback_query(F.data.startswith("goal_"))
async def process_goal(callback: CallbackQuery, state: FSMContext):
    goal_key = callback.data.replace("goal_", "").replace("_", " ").title()
    
    data = await state.get_data()
    goals = data.get("goals", [])
    
    if goal_key not in goals:
        goals.append(goal_key)
        await state.update_data(goals=goals)
    
    goals_text = "Выбранные цели:\n" + "\n".join(f"- {goal}" for goal in goals)
    
    await callback.message.edit_text(
        f"{goals_text}\n\nВыберите еще или нажмите 'Готово':",
        reply_markup=get_goals_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "goals_done")
async def goals_done(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    username = callback.from_user.username
    
    data = await state.get_data()
    
    user_profile = UserProfile(
        user_id=user_id,
        username=username,
        background=data.get("background", ""),
        interests=data.get("interests", []),
        goals=data.get("goals", []),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    await storage.save_user_profile(user_profile)
    
    await callback.message.edit_text(
        "Профиль создан! Теперь вы можете получить персональные рекомендации.",
        reply_markup=get_main_menu_keyboard()
    )
    
    await state.set_state(UserStates.MAIN_MENU)
    await callback.answer()
    
    logger.info("User profile created", user_id=user_id, interests_count=len(user_profile.interests))

@router.callback_query(F.data == "skip_profile")
async def skip_profile(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    username = callback.from_user.username
    
    user_profile = UserProfile(
        user_id=user_id,
        username=username,
        background="",
        interests=[],
        goals=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    await storage.save_user_profile(user_profile)
    
    await callback.message.edit_text(
        "Профиль создан с минимальными данными. Вы можете дополнить его позже.",
        reply_markup=get_main_menu_keyboard()
    )
    
    await state.set_state(UserStates.MAIN_MENU)
    await callback.answer() 