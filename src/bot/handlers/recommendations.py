from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from ..states.user_states import UserStates
from ..keyboards.inline_keyboards import (
    get_main_menu_keyboard, get_programs_keyboard, 
    get_courses_keyboard, get_export_keyboard, get_profile_setup_keyboard
)
from ...services.recommendation_service import recommendation_service
from ...data.json_storage import storage
from ...utils.logger import logger

router = Router()

@router.callback_query(F.data == "get_recommendations")
async def get_recommendations(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    
    try:
        await callback.message.edit_text("Генерирую рекомендации... Пожалуйста, подождите.")
        
        user_profile = await storage.load_user_profile(user_id)
        
        if not user_profile:
            await callback.message.edit_text(
                "Для получения рекомендаций необходимо заполнить профиль.",
                reply_markup=get_profile_setup_keyboard()
            )
            await callback.answer()
            return
        
        # Используем fallback рекомендации если LLM недоступна
        recommendation = await recommendation_service.get_program_recommendations(user_profile)
        
        if not recommendation:
            # Fallback рекомендации
            recommendation = _generate_fallback_recommendations(user_profile)
        
        await callback.message.edit_text(
            f"Персональные рекомендации:\n\n{recommendation}",
            reply_markup=get_main_menu_keyboard()
        )
        
        await state.set_state(UserStates.GETTING_RECOMMENDATIONS)
        
    except Exception as e:
        logger.error("Failed to get recommendations", user_id=user_id, error=str(e))
        await callback.message.edit_text(
            "Произошла ошибка при получении рекомендаций.",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()

def _generate_fallback_recommendations(user_profile) -> str:
    """Fallback рекомендации когда LLM недоступна"""
    
    background = user_profile.background.lower() if user_profile.background else ""
    interests = [interest.lower() for interest in user_profile.interests]
    goals = [goal.lower() for goal in user_profile.goals]
    
    # Анализируем профиль
    has_tech_background = any(keyword in background for keyword in ['информатик', 'программ', 'it', 'техническ'])
    interested_in_ml = any(keyword in interest for interest in interests for keyword in ['машинное обучение', 'данные', 'ml'])
    interested_in_products = any(keyword in interest for interest in interests for keyword in ['продукт', 'стартап', 'бизнес'])
    wants_career = any(keyword in goal for goal in goals for keyword in ['карьер', 'it'])
    
    recommendations = "🎯 Рекомендации на основе вашего профиля:\n\n"
    
    if has_tech_background and interested_in_ml:
        recommendations += "✅ **Искусственный интеллект** - отлично подходит для вашего технического бэкграунда\n"
        recommendations += "• Курсы: Машинное обучение, Глубокое обучение, Компьютерное зрение\n"
        recommendations += "• Подходит для развития в ML Engineer, Data Scientist\n\n"
    
    if interested_in_products or not has_tech_background:
        recommendations += "✅ **Управление ИИ-продуктами** - для тех, кто хочет быть на стыке технологий и бизнеса\n"
        recommendations += "• Курсы: Управление AI-продуктами, Data Science для продуктов, UX/UI\n"
        recommendations += "• Подходит для развития в Product Manager, AI Product Owner\n\n"
    
    if wants_career:
        recommendations += "💼 **Карьерные возможности:**\n"
        recommendations += "• Зарплата Middle+ специалистов: 170-300 тыс. рублей\n"
        recommendations += "• Высокий спрос на AI-экспертов на рынке\n\n"
    
    recommendations += "📚 **Рекомендуемые первые шаги:**\n"
    recommendations += "1. Изучите детали программ в разделе 'Выбрать программу'\n"
    recommendations += "2. Сравните программы между собой\n"
    recommendations += "3. Задайте вопросы в режиме Q&A\n"
    
    return recommendations

@router.callback_query(F.data == "compare_programs")
async def compare_programs(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Сравниваю программы... Пожалуйста, подождите.")
    
    try:
        comparison = await recommendation_service.compare_programs()
        
        if comparison:
            # Разбиваем длинный текст на части, если необходимо
            if len(comparison) > 4000:
                parts = [comparison[i:i+4000] for i in range(0, len(comparison), 4000)]
                
                for i, part in enumerate(parts):
                    if i == 0:
                        await callback.message.edit_text(f"Сравнение программ (часть {i+1}):\n\n{part}")
                    else:
                        await callback.message.answer(f"Часть {i+1}:\n\n{part}")
                
                await callback.message.answer(
                    "Сравнение завершено.",
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                await callback.message.edit_text(
                    f"Сравнение программ:\n\n{comparison}",
                    reply_markup=get_main_menu_keyboard()
                )
        else:
            await callback.message.edit_text(
                "Не удалось выполнить сравнение программ.",
                reply_markup=get_main_menu_keyboard()
            )
        
        await state.set_state(UserStates.PROGRAM_COMPARISON)
        
    except Exception as e:
        logger.error("Failed to compare programs", error=str(e))
        await callback.message.edit_text(
            "Произошла ошибка при сравнении программ.",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()

@router.callback_query(F.data == "select_program")
async def select_program(callback: CallbackQuery, state: FSMContext):
    try:
        programs = await storage.load_programs()
        
        if not programs:
            await callback.message.edit_text(
                "Данные о программах временно недоступны.",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        await callback.message.edit_text(
            "Выберите программу для подробной информации:",
            reply_markup=get_programs_keyboard(programs)
        )
        
        await state.set_state(UserStates.PROGRAM_SELECTION)
        
    except Exception as e:
        logger.error("Failed to load programs", error=str(e))
        await callback.message.edit_text(
            "Ошибка загрузки программ.",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("program_"))
async def show_program_details(callback: CallbackQuery, state: FSMContext):
    program_id = callback.data.replace("program_", "")
    
    try:
        programs = await storage.load_programs()
        program = next((p for p in programs if p.id == program_id), None)
        
        if not program:
            await callback.message.edit_text(
                "Программа не найдена.",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        program_text = f"""
{program.name}

Описание: {program.description or 'Описание недоступно'}

Общая информация:
- Всего курсов: {len(program.courses)}
- Выборочных дисциплин: {len([c for c in program.courses if c.is_elective])}
- Общие кредиты: {program.total_credits}
- Продолжительность: {program.duration_semesters} семестров

Хотите посмотреть рекомендуемые курсы для вашего профиля?
        """
        
        from ...data.models import ProgramType
        program_type = ProgramType(program_id)
        
        user_id = str(callback.from_user.id)
        user_profile = await storage.load_user_profile(user_id)
        
        if user_profile:
            recommended_courses = await recommendation_service.get_course_recommendations(
                user_profile, program_type
            )
            
            if recommended_courses:
                await callback.message.edit_text(
                    program_text,
                    reply_markup=get_courses_keyboard(recommended_courses)
                )
            else:
                await callback.message.edit_text(
                    program_text + "\n\nРекомендации курсов недоступны.",
                    reply_markup=get_main_menu_keyboard()
                )
        else:
            await callback.message.edit_text(
                program_text + "\n\nДля получения персональных рекомендаций курсов заполните профиль.",
                reply_markup=get_main_menu_keyboard()
            )
        
        await state.set_state(UserStates.VIEWING_COURSES)
        
    except Exception as e:
        logger.error("Failed to show program details", program_id=program_id, error=str(e))
        await callback.message.edit_text(
            "Ошибка при загрузке информации о программе.",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("course_"))
async def show_course_details(callback: CallbackQuery):
    course_id = callback.data.replace("course_", "")
    
    try:
        programs = await storage.load_programs()
        course = None
        
        for program in programs:
            course = next((c for c in program.courses if c.id == course_id), None)
            if course:
                break
        
        if not course:
            await callback.answer("Курс не найден.")
            return
        
        course_text = f"""
{course.name}

Кредиты: {course.credits}
Семестр: {course.semester}
Тип: {"Выборочная дисциплина" if course.is_elective else "Обязательная дисциплина"}

{course.description or 'Описание недоступно'}

Пререквизиты: {', '.join(course.prerequisites) if course.prerequisites else 'Отсутствуют'}
        """
        
        await callback.message.answer(course_text)
        
    except Exception as e:
        logger.error("Failed to show course details", course_id=course_id, error=str(e))
        await callback.answer("Ошибка при загрузке информации о курсе.")
    
    await callback.answer()

@router.callback_query(F.data == "export_courses")
async def export_courses(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите формат экспорта:",
        reply_markup=get_export_keyboard()
    )
    await state.set_state(UserStates.EXPORT_FORMAT_SELECTION)
    await callback.answer()

@router.callback_query(F.data == "export_text")
async def export_as_text(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    
    try:
        user_profile = await storage.load_user_profile(user_id)
        if not user_profile:
            await callback.message.edit_text(
                "Профиль не найден.",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        # Генерируем текстовый отчет
        report = f"""
ПЕРСОНАЛЬНЫЕ РЕКОМЕНДАЦИИ ИТМО

Профиль пользователя:
- Образование: {user_profile.background or 'Не указано'}
- Интересы: {', '.join(user_profile.interests) if user_profile.interests else 'Не указаны'}
- Цели: {', '.join(user_profile.goals) if user_profile.goals else 'Не указаны'}

Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        # Отправляем как файл
        from aiogram.types import BufferedInputFile
        file_bytes = report.encode('utf-8')
        file = BufferedInputFile(file_bytes, filename=f"itmo_recommendations_{user_id}.txt")
        
        await callback.message.answer_document(
            document=file,
            caption="Ваши персональные рекомендации"
        )
        
        await callback.message.edit_text(
            "Рекомендации экспортированы!",
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error("Failed to export recommendations", user_id=user_id, error=str(e))
        await callback.message.edit_text(
            "Ошибка при экспорте рекомендаций.",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()

@router.callback_query(F.data == "export_message")
async def export_as_message(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    
    try:
        user_profile = await storage.load_user_profile(user_id)
        if not user_profile:
            await callback.message.edit_text(
                "Профиль не найден.",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        recommendation = await recommendation_service.get_program_recommendations(user_profile)
        
        if recommendation:
            await callback.message.answer(f"Ваши рекомендации:\n\n{recommendation}")
        else:
            await callback.message.answer("Не удалось получить рекомендации.")
        
        await callback.message.edit_text(
            "Готово!",
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error("Failed to export as message", user_id=user_id, error=str(e))
        await callback.message.edit_text(
            "Ошибка при экспорте.",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer() 