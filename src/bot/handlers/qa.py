from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import List

from ..states.user_states import UserStates
from ..keyboards.inline_keyboards import get_main_menu_keyboard, get_menu_button_keyboard
from ...services.llm_service import llm_service
from ...data.json_storage import storage
from ...utils.logger import logger

router = Router()

@router.callback_query(F.data == "qa_mode")
async def enter_qa_mode(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        """
Режим вопросов и ответов активирован!

Вы можете задать любой вопрос о магистерских программах ИТМО по ИИ.

Для выхода из режима используйте команду /menu
        """,
        reply_markup=None
    )
    
    await state.set_state(UserStates.QA_MODE)
    await callback.answer()

@router.message(UserStates.QA_MODE)
async def process_question(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    question = message.text.strip()
    
    if question.lower() in ['/menu', 'меню', 'назад']:
        await message.answer(
            "Возвращаемся в главное меню.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.set_state(UserStates.MAIN_MENU)
        return
    
    if len(question) < 5:
        await message.answer(
            "Пожалуйста, задайте более развернутый вопрос.",
            reply_markup=get_menu_button_keyboard()
        )
        return
    
    # Проверяем релевантность вопроса
    if not _is_relevant_question(question):
        await message.answer(
            "Я отвечаю только на вопросы о магистерских программах ИТМО по ИИ.\n\n"
            "Попробуйте переформулировать вопрос или задайте другой.",
            reply_markup=get_menu_button_keyboard()
        )
        logger.info("Irrelevant question filtered", user_id=user_id, question=question[:50])
        return
    
    # Показываем индикатор печати
    processing_msg = await message.answer(
        "Генерация ответа... Пожалуйста, подождите.",
        reply_markup=get_menu_button_keyboard()
    )
    
    try:
        # Загружаем профиль пользователя и программы
        user_profile = await storage.load_user_profile(user_id)
        programs = await storage.load_programs()
        
        # Строим персонализированный контекст
        context = _build_personalized_context(programs, user_profile)
        
        # Генерируем ответ через LLM
        answer = await llm_service.answer_question(question, context)
        
        if answer:
            # Ограничиваем длину ответа
            if len(answer) > 4000:
                answer = answer[:4000] + "...\n\nДля получения полной информации обратитесь к консультанту."
            
            # Удаляем сообщение "Поиск ответа..."
            await processing_msg.delete()
            
            await message.answer(
                f"💡 **Ответ на ваш вопрос:**\n\n{answer}\n\n"
                "❓ Есть еще вопросы? Задавайте!",
                reply_markup=get_menu_button_keyboard(),
                parse_mode="Markdown"
            )
            
            logger.info("Question answered via LLM", user_id=user_id, question_length=len(question))
        else:
            # Удаляем сообщение "Поиск ответа..."
            await processing_msg.delete()
            
            # Используем персонализированный fallback ответ
            fallback_answer = _generate_personalized_fallback_answer(question, programs, user_profile)
            await message.answer(
                fallback_answer,
                reply_markup=get_menu_button_keyboard(),
                parse_mode="Markdown"
            )
            
            logger.warning("Used fallback answer", user_id=user_id, question=question[:50])
    
    except Exception as e:
        logger.error("Error in Q&A processing", user_id=user_id, error=str(e))
        
        # Удаляем сообщение "Поиск ответа..." если оно есть
        try:
            await processing_msg.delete()
        except:
            pass
            
        await message.answer(
            "⚠️ Произошла ошибка при обработке вопроса. Попробуйте позже.",
            reply_markup=get_menu_button_keyboard()
        )

def _filter_relevant_courses(programs, user_profile):
    """Фильтрует курсы на основе интересов пользователя"""
    if not user_profile or not user_profile.interests:
        return programs
    
    user_interests = [interest.lower() for interest in user_profile.interests]
    
    filtered_programs = []
    for program in programs:
        relevant_courses = []
        
        # Добавляем обязательные курсы
        mandatory_courses = [course for course in program.courses if not course.is_elective]
        relevant_courses.extend(mandatory_courses)
        
        # Фильтруем выборочные курсы по интересам
        elective_courses = [course for course in program.courses if course.is_elective]
        for course in elective_courses:
            course_name_lower = course.name.lower()
            for interest in user_interests:
                # Проверяем совпадение по ключевым словам
                interest_words = interest.split()
                if any(word in course_name_lower for word in interest_words if len(word) > 2):
                    relevant_courses.append(course)
                    break
        
        # Если релевантных выборочных курсов мало, добавляем еще несколько
        if len([c for c in relevant_courses if c.is_elective]) < 3:
            remaining_electives = [c for c in elective_courses if c not in relevant_courses][:3]
            relevant_courses.extend(remaining_electives)
        
        # Создаем копию программы с отфильтрованными курсами
        filtered_program = program.model_copy()
        filtered_program.courses = relevant_courses
        filtered_programs.append(filtered_program)
    
    return filtered_programs

def _build_personalized_context(programs, user_profile):
    """Строит персонализированный контекст на основе профиля пользователя"""
    if not programs:
        return "Информация о программах временно недоступна."
    
    # Фильтруем релевантные курсы
    relevant_programs = _filter_relevant_courses(programs, user_profile)
    
    context = ""
    
    # Добавляем информацию о профиле пользователя
    if user_profile:
        context += "Профиль пользователя:\n"
        if user_profile.background:
            context += f"Образование/опыт: {user_profile.background}\n"
        if user_profile.interests:
            context += f"Интересы: {', '.join(user_profile.interests)}\n"
        if user_profile.goals:
            context += f"Цели: {', '.join(user_profile.goals)}\n"
        context += "\n"
    
    context += "Доступные магистерские программы ИТМО:\n\n"
    
    for program in relevant_programs:
        context += f"Программа: {program.name}\n"
        context += f"Описание: {program.description or 'Инновационная программа по ИИ'}\n"
        
        # Группируем курсы по типу
        mandatory_courses = [c for c in program.courses if not c.is_elective]
        elective_courses = [c for c in program.courses if c.is_elective]
        
        if mandatory_courses:
            context += f"\nОсновные курсы ({len(mandatory_courses)}):\n"
            for course in mandatory_courses[:8]:  # Ограничиваем количество
                context += f"- {course.name} ({course.credits} кредитов, {course.semester} семестр)\n"
        
        if elective_courses:
            context += f"\nВыборочные курсы (релевантные для пользователя, {len(elective_courses)}):\n"
            for course in elective_courses[:10]:  # Ограничиваем количество
                context += f"- {course.name} ({course.credits} кредитов, {course.semester} семестр)\n"
        
        context += f"\nВсего курсов в программе: {len(program.courses)}, кредитов: {program.total_credits}\n\n"
    
    return context

def _is_relevant_question(question: str) -> bool:
    question_lower = question.lower()
    
    # Ключевые слова, связанные с образованием и программами
    relevant_keywords = [
        'магистр', 'обучение', 'курс', 'дисциплин', 'семестр', 'кредит',
        'поступление', 'программа', 'итмо', 'ии', 'искусственный интеллект',
        'машинное обучение', 'нейронные сети', 'data science', 'анализ данных',
        'учебный план', 'практика', 'диплом', 'экзамен', 'зачет',
        'преподаватель', 'лекция', 'лабораторная', 'проект', 'исследование'
    ]
    
    # Нерелевантные темы
    irrelevant_keywords = [
        'погода', 'новости', 'спорт', 'политика', 'развлечения',
        'фильм', 'музыка', 'игра', 'готовка', 'путешествие'
    ]
    
    # Проверяем наличие нерелевантных ключевых слов
    for keyword in irrelevant_keywords:
        if keyword in question_lower:
            return False
    
    # Проверяем наличие релевантных ключевых слов
    for keyword in relevant_keywords:
        if keyword in question_lower:
            return True
    
    # Если нет явных маркеров, считаем вопрос потенциально релевантным
    return True

def _build_context_from_programs(programs) -> str:
    if not programs:
        return "Информация о программах временно недоступна."
    
    context = "Доступные магистерские программы ИТМО:\n\n"
    
    for program in programs:
        context += f"Программа: {program.name}\n"
        context += f"Описание: {program.description or 'Описание недоступно'}\n"
        context += f"Количество курсов: {len(program.courses)}\n"
        context += f"Общие кредиты: {program.total_credits}\n"
        context += f"Продолжительность: {program.duration_semesters} семестров\n"
        
        # Добавляем информацию о ключевых курсах
        key_courses = [course for course in program.courses if not course.is_elective][:5]
        if key_courses:
            context += "Основные курсы:\n"
            for course in key_courses:
                context += f"- {course.name} ({course.credits} кредитов)\n"
        
        context += "\n"
    
    return context 

def _generate_personalized_fallback_answer(question: str, programs: list, user_profile) -> str:
    """Генерирует персонализированный fallback ответ на основе профиля пользователя"""
    if not user_profile:
        return """
😊 Привет! Чтобы дать тебе персональную рекомендацию, мне нужно знать твой профиль.
        
Вернись в главное меню и создай профиль - тогда я смогу подобрать курсы и программы именно под твои интересы!
        """
    
    # Получаем релевантные программы
    relevant_programs = _filter_relevant_courses(programs, user_profile)
    
    return f"""
😊 **Персональная рекомендация для тебя:**

На основе твоего профиля:
• **Образование:** {user_profile.background or 'Не указано'}
• **Интересы:** {', '.join(user_profile.interests) if user_profile.interests else 'Не указаны'}
• **Цели:** {', '.join(user_profile.goals) if user_profile.goals else 'Не указаны'}

{_get_personalized_programs_summary(relevant_programs, user_profile)}

💡 **Рекомендую:**
• Изучить детали выбранных курсов
• Обратиться к координатору программы для консультации
• Подготовить портфолио проектов по твоим интересам

❓ Попробуй переформулировать вопрос более конкретно, я постараюсь помочь!
    """.strip()

def _get_personalized_programs_summary(programs: list, user_profile) -> str:
    """Создает персонализированную сводку о программах"""
    if not programs:
        return "К сожалению, информация о программах временно недоступна."
    
    summary = "**Рекомендуемые программы для тебя:**\n\n"
    for program in programs:
        summary += f"**{program.name}**\n"
        summary += f"• {program.description or 'Инновационная программа по ИИ'}\n"
        
        # Показываем релевантные курсы
        relevant_electives = [c for c in program.courses if c.is_elective][:3]
        if relevant_electives:
            summary += f"• **Подходящие курсы:** {', '.join([c.name for c in relevant_electives])}\n"
        
        summary += f"• **Всего:** {len(program.courses)} курсов, {program.total_credits} кредитов\n\n"
    
    return summary

def _get_programs_summary(programs: list) -> str:
    """Создает краткую сводку о доступных программах"""
    if not programs:
        return "К сожалению, информация о программах временно недоступна."
    
    summary = "Доступные программы:\n"
    for program in programs:
        summary += f"• **{program.name}** - {program.description or 'Инновационная программа по ИИ'}\n"
        summary += f"  └ {len(program.courses)} курсов, {program.total_credits} кредитов\n"
    
    return summary 