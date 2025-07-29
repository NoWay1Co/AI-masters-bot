from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ..states.user_states import UserStates
from ..keyboards.inline_keyboards import get_main_menu_keyboard
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

Например:
- Какие курсы по машинному обучению есть в программе?
- Сколько длится обучение?
- Какие требования для поступления?
- Есть ли практика в компаниях?

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
            "Пожалуйста, задайте более развернутый вопрос.\n\n"
            "Для возврата в меню напишите /menu"
        )
        return
    
    # Проверяем релевантность вопроса
    if not _is_relevant_question(question):
        await message.answer(
            "Я отвечаю только на вопросы о магистерских программах ИТМО по ИИ.\n\n"
            "Попробуйте переформулировать вопрос или задайте другой.\n\n"
            "Для возврата в меню напишите /menu"
        )
        logger.info("Irrelevant question filtered", user_id=user_id, question=question[:50])
        return
    
    # Показываем индикатор печати
    await message.answer("Поиск ответа... Пожалуйста, подождите.")
    
    try:
        # Загружаем контекст о программах
        programs = await storage.load_programs()
        context = _build_context_from_programs(programs)
        
        # Генерируем ответ
        answer = await llm_service.answer_question(question, context)
        
        if answer:
            # Ограничиваем длину ответа
            if len(answer) > 4000:
                answer = answer[:4000] + "...\n\nДля получения полной информации обратитесь к консультанту."
            
            await message.answer(
                f"Ответ на ваш вопрос:\n\n{answer}\n\n"
                "Есть еще вопросы? Задавайте!\n"
                "Для возврата в меню напишите /menu"
            )
            
            logger.info("Question answered", user_id=user_id, question_length=len(question))
        else:
            await message.answer(
                "К сожалению, не удалось найти ответ на ваш вопрос.\n\n"
                "Попробуйте переформулировать вопрос или обратитесь к приемной комиссии ИТМО.\n\n"
                "Для возврата в меню напишите /menu"
            )
            
            logger.warning("Failed to answer question", user_id=user_id, question=question[:50])
    
    except Exception as e:
        logger.error("Error in Q&A processing", user_id=user_id, error=str(e))
        await message.answer(
            "Произошла ошибка при обработке вопроса. Попробуйте позже.\n\n"
            "Для возврата в меню напишите /menu"
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