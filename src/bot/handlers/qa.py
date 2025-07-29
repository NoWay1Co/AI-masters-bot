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
        "🔍 Поиск ответа... Пожалуйста, подождите.",
        reply_markup=get_menu_button_keyboard()
    )
    
    try:
        # Загружаем контекст о программах
        programs = await storage.load_programs()
        context = _build_context_from_programs(programs)
        
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
            
            # Используем улучшенный fallback ответ
            fallback_answer = _generate_fallback_answer(question, programs)
            await message.answer(
                fallback_answer,
                reply_markup=get_menu_button_keyboard()
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

def _generate_fallback_answer(question: str, programs: list) -> str:
    """Генерирует fallback ответ на основе ключевых слов и доступной информации о программах"""
    question_lower = question.lower()
    
    # Словарь ключевых слов и соответствующих ответов
    keyword_responses = {
        'поступление': """
📚 **Информация о поступлении:**

Для поступления на магистерские программы ИТМО по ИИ обычно требуется:
• Диплом бакалавра в области IT, математики или смежных областей
• Успешная сдача вступительных испытаний
• Портфолио проектов (для некоторых программ)

Рекомендую обратиться в приемную комиссию ИТМО для получения актуальной информации.
        """,
        
        'стоимость': """
💰 **Стоимость обучения:**

Информация о стоимости обучения может изменяться каждый год.
Для получения актуальных данных обратитесь:
• В приемную комиссию ИТМО
• На официальный сайт университета
• По телефону горячей линии
        """,
        
        'срок': """
⏰ **Сроки обучения:**

Стандартная продолжительность магистратуры в ИТМО составляет 2 года (4 семестра).
Программы включают:
• Обязательные дисциплины
• Выборочные курсы
• Практику
• Написание магистерской диссертации
        """,
        
        'курс': f"""
📖 **Доступные курсы:**

В рамках магистерских программ ИТМО по ИИ изучаются:
• Машинное обучение и нейронные сети
• Компьютерное зрение и обработка изображений
• Обработка естественного языка (NLP)
• Робототехника и автономные системы
• Анализ данных и Data Science

{_get_programs_summary(programs)}
        """,
        
        'программа': f"""
🎓 **Магистерские программы:**

{_get_programs_summary(programs)}

Каждая программа имеет свою специализацию и набор обязательных и выборочных дисциплин.
        """
    }
    
    # Поиск подходящего ответа по ключевым словам
    for keyword, response in keyword_responses.items():
        if keyword in question_lower:
            return response.strip()
    
    # Если ключевые слова не найдены, даем общий ответ
    return f"""
🤖 **Общая информация:**

{_get_programs_summary(programs)}

Для получения более детальной информации рекомендую:
• Обратиться в приемную комиссию ИТМО
• Посетить официальный сайт университета  
• Связаться с координаторами программ

❓ Попробуйте переформулировать вопрос более конкретно.
    """.strip()

def _get_programs_summary(programs: list) -> str:
    """Создает краткую сводку о доступных программах"""
    if not programs:
        return "К сожалению, информация о программах временно недоступна."
    
    summary = "Доступные программы:\n"
    for program in programs:
        summary += f"• **{program.name}** - {program.description or 'Инновационная программа по ИИ'}\n"
        summary += f"  └ {len(program.courses)} курсов, {program.total_credits} кредитов\n"
    
    return summary 