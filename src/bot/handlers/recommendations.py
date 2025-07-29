from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from ..states.user_states import UserStates
from ..keyboards.inline_keyboards import (
    get_main_menu_keyboard, get_programs_keyboard, 
    get_courses_keyboard, get_export_keyboard, get_profile_setup_keyboard,
    get_menu_button_keyboard
)
from ...services.recommendation_service import recommendation_service
from ...data.json_storage import storage
from ...utils.logger import logger
import re

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
    
    recommendations = f"""
🎯 *ПЕРСОНАЛЬНЫЕ РЕКОМЕНДАЦИИ*

👤 *Ваш профиль:*
• Образование: {user_profile.background or 'Не указано'}
• Интересы: {', '.join(user_profile.interests) if user_profile.interests else 'Не указаны'}
• Цели: {', '.join(user_profile.goals) if user_profile.goals else 'Не указаны'}

"""
    
    if has_tech_background and interested_in_ml:
        recommendations += """
🎯 *РЕКОМЕНДУЕМАЯ ПРОГРАММА:*
✅ **ИСКУССТВЕННЫЙ ИНТЕЛЛЕКТ**

🔍 *Почему подходит:*
• Соответствует вашему техническому образованию
• Развивает интересы в области машинного обучения
• Дает глубокие знания в ИИ-технологиях

📚 *Ключевые курсы:*
• Основы машинного обучения (6 кр.)
• Глубокое обучение (6 кр.)
• Компьютерное зрение (5 кр.)
• Математические методы в ИИ (4 кр.)

💼 *Карьерные треки:*
• ML Engineer: 200-350K ₽
• Data Scientist: 180-300K ₽
• AI Researcher: 220-400K ₽

"""
    
    if interested_in_products or not has_tech_background:
        recommendations += """
🎯 *АЛЬТЕРНАТИВНАЯ ПРОГРАММА:*
⚡ **УПРАВЛЕНИЕ ИИ-ПРОДУКТАМИ**

🔍 *Почему подходит:*
• Фокус на бизнес-применении ИИ
• Подходит для перехода в IT
• Развивает продуктовое мышление

📚 *Ключевые курсы:*
• Управление AI-продуктами (6 кр.)
• Data Science для продуктов (6 кр.)
• UX/UI для AI-продуктов (4 кр.)
• MLOps и инфраструктура (5 кр.)

💼 *Карьерные треки:*
• AI Product Manager: 250-450K ₽
• AI Product Owner: 200-350K ₽
• AI Consultant: 180-300K ₽

"""
    
    recommendations += """
🚀 *СЛЕДУЮЩИЕ ШАГИ:*
1️⃣ Изучите детали программ → "Выбрать программу"
2️⃣ Сравните программы между собой
3️⃣ Экспортируйте полную информацию о курсах
4️⃣ Задайте вопросы в режиме Q&A

💡 *Дополнительные возможности:*
• Стажировки в IT-компаниях
• Проектная работа с реальными задачами
• Менторская поддержка экспертов
• Возможность создания собственного стартапа

📞 *Нужна консультация?*
Обратитесь в приемную комиссию ИТМО для персональной консультации.
"""
    
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

def _escape_markdown(text: str) -> str:
    """Экранирует специальные символы Markdown"""
    if not text:
        return text
    
    # Экранируем специальные символы Markdown
    escape_chars = ['*', '_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def _format_description(description: str) -> str:
    """Форматирует описание программы, удаляя лишние пробелы и переносы"""
    if not description:
        return "Описание программы временно недоступно"
    
    # Удаляем лишние пробелы и переносы
    formatted = re.sub(r'\n\s+', ' ', description.strip())
    # Заменяем множественные пробелы на одинарные
    formatted = re.sub(r'\s+', ' ', formatted)
    
    return formatted

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
        
        # Подсчет статистики курсов
        mandatory_courses = [c for c in program.courses if not c.is_elective]
        elective_courses = [c for c in program.courses if c.is_elective]
        semesters = list(set(c.semester for c in program.courses))
        
        # Безопасное форматирование с экранированием Markdown
        program_name = _escape_markdown(program.name)
        program_desc = _format_description(program.description)
        program_url = program.url
        
        program_text = f"""
🎓 **{program_name}**

📋 **Описание:**
{program_desc}

📊 **Структура программы:**
• Всего курсов: {len(program.courses)}
• Обязательных: {len(mandatory_courses)} курсов  
• Выборочных: {len(elective_courses)} курса
• Общих кредитов: {program.total_credits}
• Семестров: {max(semesters) if semesters else 4}

🌐 **Официальная страница:** [Перейти на сайт]({program_url})

📚 **Курсы программы:**
        """
        
        await callback.message.edit_text(
            program_text.strip(),
            reply_markup=get_courses_keyboard(program.courses, page=0, program_id=program_id),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        
        await state.set_state(UserStates.VIEWING_COURSES)
        
    except Exception as e:
        logger.error("Failed to show program details", program_id=program_id, error=str(e))
        await callback.message.edit_text(
            "Ошибка при загрузке информации о программе.",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("courses_page_"))
async def navigate_courses(callback: CallbackQuery, state: FSMContext):
    try:
        parts = callback.data.split("_")
        page = int(parts[2])
        program_id = parts[3]
        
        programs = await storage.load_programs()
        program = next((p for p in programs if p.id == program_id), None)
        
        if not program:
            await callback.answer("Программа не найдена")
            return
        
        await callback.message.edit_reply_markup(
            reply_markup=get_courses_keyboard(program.courses, page=page, program_id=program_id)
        )
        
    except Exception as e:
        logger.error("Failed to navigate courses", error=str(e))
        await callback.answer("Ошибка навигации")
    
    await callback.answer()

@router.callback_query(F.data.startswith("export_program_"))
async def export_program(callback: CallbackQuery, state: FSMContext):
    try:
        program_id = callback.data.replace("export_program_", "")
        
        programs = await storage.load_programs()
        program = next((p for p in programs if p.id == program_id), None)
        
        if not program:
            await callback.answer("Программа не найдена")
            return
        
        # Формируем подробный экспорт программы
        export_text = f"""
📄 ПРОГРАММА ОБУЧЕНИЯ: {program.name.upper()}

🎯 ОПИСАНИЕ ПРОГРАММЫ:
{program.description}

📊 ОБЩАЯ ИНФОРМАЦИЯ:
• Официальная страница: {program.url}
• Общее количество кредитов: {program.total_credits}
• Продолжительность: {program.duration_semesters} семестров
• Всего курсов: {len(program.courses)}
• Обязательных курсов: {len([c for c in program.courses if not c.is_elective])}
• Выборочных курсов: {len([c for c in program.courses if c.is_elective])}

📚 УЧЕБНЫЙ ПЛАН:
"""
        
        # Группируем курсы по семестрам
        courses_by_semester = {}
        for course in program.courses:
            if course.semester not in courses_by_semester:
                courses_by_semester[course.semester] = []
            courses_by_semester[course.semester].append(course)
        
        for semester in sorted(courses_by_semester.keys()):
            export_text += f"\nСЕМЕСТР {semester}:\n"
            
            mandatory = [c for c in courses_by_semester[semester] if not c.is_elective]
            elective = [c for c in courses_by_semester[semester] if c.is_elective]
            
            if mandatory:
                export_text += "\nОбязательные курсы:\n"
                for course in mandatory:
                    export_text += f"• {course.name} ({course.credits} кр.)\n"
                    if course.description:
                        export_text += f"  {course.description}\n"
            
            if elective:
                export_text += "\nВыборочные курсы:\n"
                for course in elective:
                    export_text += f"• {course.name} ({course.credits} кр.)\n"
                    if course.description:
                        export_text += f"  {course.description}\n"
        
        export_text += f"\n\nДокумент создан: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        export_text += f"\nИсточник: AI Masters Bot ИТМО"
        
        # Отправляем как файл если текст слишком длинный
        if len(export_text) > 4000:
            from io import StringIO
            file_content = StringIO(export_text)
            
            await callback.message.answer_document(
                document=file_content,
                filename=f"program_{program_id}_{datetime.now().strftime('%Y%m%d')}.txt",
                caption=f"📥 Полная программа обучения: {program.name}",
                reply_markup=get_menu_button_keyboard()
            )
        else:
            await callback.message.answer(
                export_text,
                reply_markup=get_menu_button_keyboard()
            )
        
    except Exception as e:
        logger.error("Failed to export program", program_id=program_id, error=str(e))
        await callback.message.answer("Ошибка при экспорте программы.")
    
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
📘 **{course.name}**

📊 **Детали курса:**
• Кредиты: {course.credits}
• Семестр: {course.semester}
• Тип: {"📚 Выборочная дисциплина" if course.is_elective else "✅ Обязательная дисциплина"}

📝 **Описание:**
{course.description or 'Описание недоступно'}

🔗 **Пререквизиты:** 
{', '.join(course.prerequisites) if course.prerequisites else 'Отсутствуют'}
        """
        
        await callback.message.answer(
            course_text,
            reply_markup=get_menu_button_keyboard(),
            parse_mode="Markdown"
        )
        
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
            caption="📄 Ваши персональные рекомендации",
            reply_markup=get_menu_button_keyboard()
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
            await callback.message.answer(
                f"📋 **Ваши рекомендации:**\n\n{recommendation}",
                reply_markup=get_menu_button_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await callback.message.answer(
                "⚠️ Не удалось получить рекомендации.",
                reply_markup=get_menu_button_keyboard()
            )
        
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