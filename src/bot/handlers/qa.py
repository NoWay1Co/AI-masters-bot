from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from typing import Optional

from ...services.llm_service import llm_service
from ...services.recommendation_service import recommendation_service
from ...data.json_storage import storage
from ...utils.logger import logger
from ..keyboards.inline_keyboards import create_back_keyboard
from ..states.user_states import QuestionState

router = Router()

@router.callback_query(F.data == "ask_question")
async def ask_question_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    await callback.message.edit_text(
        "Задайте ваш вопрос о программах магистратуры ИТМО по ИИ:",
        reply_markup=create_back_keyboard()
    )
    
    await state.set_state(QuestionState.waiting_for_question)

@router.message(StateFilter(QuestionState.waiting_for_question))
async def process_question(message: Message, state: FSMContext):
    question = message.text.strip()
    
    if not question:
        await message.reply(
            "Пожалуйста, задайте вопрос текстом.",
            reply_markup=create_back_keyboard()
        )
        return
    
    await message.reply(
        "Обрабатываю ваш вопрос...",
        reply_markup=None
    )
    
    try:
        # Получаем контекст о программах
        programs = await recommendation_service._get_programs()
        context = recommendation_service._format_programs_data(programs) if programs else ""
        
        # Генерируем ответ с помощью LLM
        answer = await llm_service.answer_question(question, context)
        
        if answer:
            await message.reply(
                f"Ответ на ваш вопрос:\n\n{answer}",
                reply_markup=create_back_keyboard()
            )
            
            logger.info(
                "Question answered",
                user_id=message.from_user.id,
                question_length=len(question),
                answer_length=len(answer)
            )
        else:
            # Fallback ответ если LLM недоступен
            fallback_answer = await _generate_fallback_answer(question, programs)
            await message.reply(
                fallback_answer,
                reply_markup=create_back_keyboard()
            )
            
    except Exception as e:
        logger.error("Failed to process question", user_id=message.from_user.id, error=str(e))
        await message.reply(
            "Произошла ошибка при обработке вопроса. Попробуйте позже или переформулируйте вопрос.",
            reply_markup=create_back_keyboard()
        )
    
    await state.clear()

async def _generate_fallback_answer(question: str, programs) -> str:
    question_lower = question.lower()
    
    # Простые паттерны для fallback ответов
    if any(word in question_lower for word in ["сколько", "длительность", "семестр"]):
        return """
        Магистерские программы ИТМО по ИИ рассчитаны на 2 года (4 семестра) обучения.
        Общая продолжительность: 120 зачетных единиц (кредитов).
        """
    
    elif any(word in question_lower for word in ["курс", "предмет", "дисциплина"]):
        if programs:
            total_courses = sum(len(p.courses) for p in programs)
            return f"""
            В программах магистратуры представлено множество курсов:
            - Общее количество дисциплин: {total_courses}
            - Включают обязательные и выборочные курсы
            - Покрывают все аспекты искусственного интеллекта
            """
        else:
            return "Программы включают разнообразные курсы по искусственному интеллекту, машинному обучению и смежным областям."
    
    elif any(word in question_lower for word in ["поступление", "требования", "документы"]):
        return """
        Для поступления в магистратуру ИТМО по ИИ обычно требуется:
        - Диплом бакалавра (или специалиста)
        - Результаты вступительных испытаний
        - Портфолио работ (для некоторых программ)
        
        Подробные требования уточняйте на официальном сайте ИТМО.
        """
    
    elif any(word in question_lower for word in ["стоимость", "цена", "оплата"]):
        return """
        Информация о стоимости обучения:
        - Доступны бюджетные и платные места
        - Стоимость варьируется в зависимости от программы
        - Возможны различные формы финансовой поддержки
        
        Актуальные цены смотрите на сайте ИТМО.
        """
    
    else:
        return """
        Ваш вопрос принят. К сожалению, сейчас не могу дать детальный ответ.
        
        Рекомендую:
        - Посетить официальный сайт ИТМО
        - Обратиться в приемную комиссию
        - Использовать другие разделы бота для получения информации о программах
        """ 