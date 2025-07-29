from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Optional

from ...services.recommendation_service import recommendation_service
from ...data.json_storage import storage
from ...data.models import UserProfile, ProgramType
from ...utils.logger import logger
from ..keyboards.inline_keyboards import create_program_selection_keyboard, create_back_keyboard

router = Router()

@router.callback_query(F.data == "get_recommendations")
async def get_recommendations_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    user_profile = await storage.load_user_profile(str(callback.from_user.id))
    
    if not user_profile:
        await callback.message.edit_text(
            "Для получения рекомендаций необходимо заполнить профиль. "
            "Используйте команду /start для начала.",
            reply_markup=create_back_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "Генерирую персональные рекомендации на основе вашего профиля...",
        reply_markup=None
    )
    
    try:
        recommendation = await recommendation_service.get_program_recommendations(user_profile)
        
        if recommendation:
            await callback.message.edit_text(
                f"Рекомендации для вас:\n\n{recommendation}",
                reply_markup=create_back_keyboard()
            )
        else:
            await callback.message.edit_text(
                "К сожалению, не удалось сгенерировать рекомендации. "
                "Попробуйте позже или обратитесь к консультанту.",
                reply_markup=create_back_keyboard()
            )
            
    except Exception as e:
        logger.error("Failed to get recommendations", user_id=callback.from_user.id, error=str(e))
        await callback.message.edit_text(
            "Произошла ошибка при генерации рекомендаций. Попробуйте позже.",
            reply_markup=create_back_keyboard()
        )

@router.callback_query(F.data == "compare_programs")
async def compare_programs_handler(callback: CallbackQuery):
    await callback.answer()
    
    await callback.message.edit_text(
        "Подготавливаю сравнение программ...",
        reply_markup=None
    )
    
    try:
        comparison = await recommendation_service.compare_programs()
        
        if comparison:
            await callback.message.edit_text(
                f"Сравнение программ:\n\n{comparison}",
                reply_markup=create_back_keyboard()
            )
        else:
            await callback.message.edit_text(
                "Не удалось выполнить сравнение программ. Попробуйте позже.",
                reply_markup=create_back_keyboard()
            )
            
    except Exception as e:
        logger.error("Failed to compare programs", user_id=callback.from_user.id, error=str(e))
        await callback.message.edit_text(
            "Произошла ошибка при сравнении программ. Попробуйте позже.",
            reply_markup=create_back_keyboard()
        )

@router.callback_query(F.data.startswith("electives_"))
async def get_electives_handler(callback: CallbackQuery):
    await callback.answer()
    
    program_type_str = callback.data.split("_")[1]
    program_type = ProgramType(program_type_str)
    
    user_profile = await storage.load_user_profile(str(callback.from_user.id))
    
    if not user_profile:
        await callback.message.edit_text(
            "Для получения рекомендаций по курсам необходимо заполнить профиль.",
            reply_markup=create_back_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "Подбираю выборочные дисциплины на основе ваших интересов...",
        reply_markup=None
    )
    
    try:
        recommended_courses = await recommendation_service.get_course_recommendations(
            user_profile, program_type
        )
        
        if recommended_courses:
            courses_text = "\n".join([
                f"• {course.name} ({course.credits} кредитов)"
                for course in recommended_courses
            ])
            
            await callback.message.edit_text(
                f"Рекомендуемые выборочные дисциплины:\n\n{courses_text}",
                reply_markup=create_back_keyboard()
            )
        else:
            await callback.message.edit_text(
                "Не найдено подходящих выборочных дисциплин.",
                reply_markup=create_back_keyboard()
            )
            
    except Exception as e:
        logger.error("Failed to get course recommendations", user_id=callback.from_user.id, error=str(e))
        await callback.message.edit_text(
            "Произошла ошибка при подборе дисциплин. Попробуйте позже.",
            reply_markup=create_back_keyboard()
        ) 