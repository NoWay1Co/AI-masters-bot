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
        "Режим вопросов и ответов активирован!\n\n"
        "Задайте любой вопрос об обучении в ИТМО, магистерских программах, "
        "выборочных дисциплинах или карьерных возможностях.\n\n"
        "Для выхода из режима нажмите кнопку 'Назад' или используйте /start"
    )
    await state.set_state(UserStates.QA_MODE)
    await callback.answer()

@router.message(UserStates.QA_MODE)
async def handle_question(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    question = message.text.strip()
    
    if not question:
        await message.answer("Пожалуйста, задайте вопрос.")
        return
    
    if question.lower() in ['/start', 'назад', 'выход', 'стоп']:
        await message.answer(
            "Выхожу из режима Q&A.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.set_state(UserStates.MAIN_MENU)
        return
    
    await message.answer("Обрабатываю ваш вопрос... Пожалуйста, подождите.")
    
    try:
        # Загружаем профиль пользователя для контекста
        user_profile = await storage.load_user_profile(user_id)
        
        # Генерируем ответ с помощью LLM
        answer = await llm_service.answer_question(question, user_profile)
        
        if answer:
            # Разбиваем длинный ответ на части, если необходимо
            if len(answer) > 4000:
                parts = [answer[i:i+4000] for i in range(0, len(answer), 4000)]
                
                for i, part in enumerate(parts):
                    if i == 0:
                        await message.answer(f"Ответ (часть {i+1}):\n\n{part}")
                    else:
                        await message.answer(f"Часть {i+1}:\n\n{part}")
                
                await message.answer(
                    "Есть еще вопросы? Продолжайте задавать или нажмите кнопку для возврата в главное меню.",
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                await message.answer(
                    f"{answer}\n\n"
                    "Есть еще вопросы? Продолжайте задавать или нажмите кнопку для возврата в главное меню.",
                    reply_markup=get_main_menu_keyboard()
                )
        else:
            await message.answer(
                "К сожалению, не удалось сгенерировать ответ на ваш вопрос. "
                "Попробуйте переформулировать вопрос или обратитесь к консультанту.",
                reply_markup=get_main_menu_keyboard()
            )
        
        logger.info("Question answered", user_id=user_id, question_length=len(question))
        
    except Exception as e:
        logger.error("Failed to answer question", user_id=user_id, error=str(e))
        await message.answer(
            "Произошла ошибка при обработке вопроса. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )

@router.callback_query(F.data == "back_to_qa", UserStates.QA_MODE)
async def back_to_qa(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Режим вопросов и ответов.\n\n"
        "Задайте любой вопрос об обучении в ИТМО!"
    )
    await callback.answer()

@router.message(UserStates.QA_MODE, F.content_type.in_(['photo', 'document', 'video', 'audio', 'voice']))
async def handle_non_text_qa(message: Message):
    await message.answer(
        "В режиме Q&A я могу отвечать только на текстовые вопросы. "
        "Пожалуйста, отправьте ваш вопрос текстом."
    ) 