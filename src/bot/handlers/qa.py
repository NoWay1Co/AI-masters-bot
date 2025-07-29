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

Вы можете задать любой вопрос о поступлении в магистратуру ИТМО по ИИ.

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
        # Загружаем только программы для прямых ответов
        programs = await storage.load_programs()
        
        # Строим полный контекст со всеми программами и курсами
        context = _build_full_programs_context(programs)
        
        # Значительно ограничиваем размер контекста для быстрой работы
        max_context_length = 15000  # Уменьшаем для быстрой работы
        if len(context) > max_context_length:
            context = context[:max_context_length] + "\n\n[Контекст сокращен]"
        
        # Генерируем прямой ответ через LLM
        answer = await llm_service.answer_question(question, context)
        
        if answer:
            # LLM успешно ответил с данными
            if len(answer) > 4000:
                answer = answer[:4000] + "...\n\nДля получения полной информации обратитесь к консультанту."
            
            await processing_msg.delete()
            await message.answer(
                f"💡 **Ответ на ваш вопрос:**\n\n{answer}\n\n"
                "❓ Есть еще вопросы? Задавайте!",
                reply_markup=get_menu_button_keyboard(),
                parse_mode="Markdown"
            )
            logger.info("Question answered via LLM with data", user_id=user_id, question_length=len(question))
        else:
            # LLM не смог ответить с данными, пробуем многоуровневый подход
            logger.info("LLM failed with data, trying multi-level approach", user_id=user_id)
            
            # Этап 1: Проверяем, есть ли конкретные данные в вопросе
            data_answer = _try_data_search(question, programs)
            
            if data_answer:
                # Найдены конкретные данные
                await processing_msg.delete()
                await message.answer(
                    f"💡 **Ответ на ваш вопрос:**\n\n{data_answer}\n\n"
                    "❓ Есть еще вопросы? Задавайте!",
                    reply_markup=get_menu_button_keyboard(),
                    parse_mode="Markdown"
                )
                logger.info("Question answered via data search", user_id=user_id)
            else:
                # Этап 2: Пробуем LLM для общих вопросов без больших данных
                general_answer = await _try_general_llm_answer(question)
                
                if general_answer and general_answer.strip():
                    await processing_msg.delete()
                    await message.answer(
                        f"💡 **Ответ на ваш вопрос:**\n\n{general_answer}\n\n"
                        "❓ Есть еще вопросы? Задавайте!",
                        reply_markup=get_menu_button_keyboard(),
                        parse_mode="Markdown"
                    )
                    logger.info("Question answered via general LLM", user_id=user_id)
                else:
                    # Этап 3: Fallback ответ
                    await processing_msg.delete()
                    fallback_answer = _generate_simple_fallback_answer(question, programs)
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

def _build_full_programs_context(programs) -> str:
    """Строит полный контекст со всеми данными о программах для Q&A"""
    if not programs:
        return "Информация о программах временно недоступна."
    
    context = "Полная информация о магистерских программах ИТМО по ИИ:\n\n"
    
    for program in programs:
        context += f"ПРОГРАММА: {program.name}\n"
        context += f"Описание: {program.description or 'Инновационная программа по ИИ'}\n"
        context += f"Общие кредиты: {program.total_credits}\n"
        context += f"Всего курсов: {len(program.courses)}\n"
        
        if hasattr(program, 'url') and program.url:
            context += f"Сайт: {program.url}\n"
        
        # Добавляем все курсы
        mandatory_courses = [c for c in program.courses if not c.is_elective]
        if mandatory_courses:
            context += "\nОБЯЗАТЕЛЬНЫЕ КУРСЫ:\n"
            for course in mandatory_courses:
                context += f"- {course.name} ({course.credits} кредитов, {course.semester} семестр)\n"
        
        elective_courses = [c for c in program.courses if c.is_elective]
        if elective_courses:
            context += "\nВЫБОРОЧНЫЕ КУРСЫ:\n"
            for course in elective_courses:
                context += f"- {course.name} ({course.credits} кредитов, {course.semester} семестр)\n"
        
        context += "\n" + "="*50 + "\n\n"
    
    return context

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

def _try_data_search(question: str, programs: list) -> str:
    """Этап 1: Ищет конкретные данные в программах и курсах"""
    question_lower = question.lower()
    logger.info("Trying data search", question=question_lower[:50])
    
    # Используем существующую логику поиска курсов
    found_courses = []
    
    for program in programs:
        for course in program.courses:
            course_name_lower = course.name.lower()
            
            # Поиск по точному совпадению фразы (убираем знаки пунктуации)
            course_clean = course_name_lower.replace(',', '').replace('.', '').replace('?', '').replace('!', '')
            question_clean = question_lower.replace(',', '').replace('.', '').replace('?', '').replace('!', '')
            
            if course_clean in question_clean or question_clean in course_clean:
                found_courses.append((program.name, course.name, course.credits, course.semester, course.is_elective))
                continue
            
            # Поиск по ключевым словам
            course_words = [word for word in course_clean.split() if len(word) > 2]
            question_words = [word for word in question_clean.split() if len(word) > 2]
            
            matches = sum(1 for word in course_words if word in question_words)
            if matches >= 2 and len(course_words) >= 2:
                found_courses.append((program.name, course.name, course.credits, course.semester, course.is_elective))
            elif matches >= 1 and len(course_words) >= 2:
                partial_matches = 0
                for course_word in course_words:
                    for question_word in question_words:
                        if (len(course_word) > 4 and len(question_word) > 4 and 
                            (course_word in question_word or question_word in course_word)):
                            partial_matches += 1
                            break
                
                if partial_matches >= 1:
                    found_courses.append((program.name, course.name, course.credits, course.semester, course.is_elective))
    
    # Если нашли курсы, возвращаем результат
    if found_courses:
        if len(found_courses) == 1:
            program_name, course_name, credits, semester, is_elective = found_courses[0]
            course_type = "выборочный" if is_elective else "обязательный"
            return f"Курс **{course_name}** есть в программе **{program_name}** ({course_type}, {credits} кредитов, {semester} семестр)."
        else:
            answer = f"Найдено курсов: {len(found_courses)}\n\n"
            for program_name, course_name, credits, semester, is_elective in found_courses[:5]:
                course_type = "выборочный" if is_elective else "обязательный"
                answer += f"• **{course_name}** ({course_type})\n"
                answer += f"  Программа: {program_name}\n"
                answer += f"  Кредиты: {credits}, Семестр: {semester}\n\n"
            return answer
    
    # Поиск по названиям программ
    for program in programs:
        if program.name.lower() in question_lower or any(word in program.name.lower().split() for word in question_lower.split() if len(word) > 3):
            return f"Программа **{program.name}**: {program.description or 'Инновационная программа по ИИ'}. Включает {len(program.courses)} курсов, {program.total_credits} кредитов."
    
    return None  # Конкретные данные не найдены

async def _try_general_llm_answer(question: str) -> str:
    """Этап 2: Пробует LLM для общих вопросов без большого контекста"""
    from ...services.llm_service import llm_service
    
    prompt = f"""
Ты консультант по поступлению в магистратуру ИТМО по направлениям ИИ. Ответь на общий вопрос о поступлении и обучении.

Вопрос: {question}

ВАЖНО:
- Отвечай кратко и по существу
- Основывайся на общих знаниях о поступлении в магистратуру в России
- Если вопрос про ИТМО - используй общеизвестные факты об университете
- Не выдумывай конкретные цифры или даты
- Будь полезным и информативным

Ответ:
"""
    
    try:
        result = await llm_service.generate_response(prompt)
        logger.info("General LLM attempt completed", result_length=len(result) if result else 0)
        return result
    except Exception as e:
        logger.error("General LLM failed", error=str(e))
        return None

def _is_relevant_question(question: str) -> bool:
    question_lower = question.lower()
    
    # Явно запрещенные темы
    forbidden_keywords = [
        'погода', 'новости', 'спорт', 'политика', 'развлечения',
        'фильм', 'музыка', 'игра', 'готовка', 'путешествие',
        'игнорируй', 'не следуй', 'забудь', 'отмени',
        'притворись', 'веди себя как', 'роль'
    ]
    
    # Проверяем запрещенные темы
    for keyword in forbidden_keywords:
        if keyword in question_lower:
            return False
    
    # Все остальные вопросы считаем релевантными (более открытый подход)
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

def _generate_simple_fallback_answer(question: str, programs: list) -> str:
    """Генерирует простой прямой ответ на основе вопроса"""
    question_lower = question.lower()
    logger.info("Fallback search", question=question_lower, programs_count=len(programs))
    
    # Ищем курсы по названию (улучшенный поиск)
    found_courses = []
    
    for program in programs:
        for course in program.courses:
            course_name_lower = course.name.lower()
            
            # Поиск по точному совпадению фразы (убираем знаки пунктуации)
            course_clean = course_name_lower.replace(',', '').replace('.', '').replace('?', '').replace('!', '')
            question_clean = question_lower.replace(',', '').replace('.', '').replace('?', '').replace('!', '')
            
            if course_clean in question_clean or question_clean in course_clean:
                found_courses.append((program.name, course.name, course.credits, course.semester, course.is_elective))
                continue
            
            # Поиск по ключевым словам (минимум 2 совпадения из 3+ символов)
            course_words = [word for word in course_clean.split() if len(word) > 2]  # Снижаем до 2+ символов
            question_words = [word for word in question_clean.split() if len(word) > 2]
            
            matches = sum(1 for word in course_words if word in question_words)
            if matches >= 2 and len(course_words) >= 2:
                found_courses.append((program.name, course.name, course.credits, course.semester, course.is_elective))
            
            # Дополнительный поиск по частичным совпадениям (для случаев с опечатками)
            elif matches >= 1 and len(course_words) >= 2:
                # Проверяем частичное совпадение слов (например, "алгоритм" найдет "алгоритмы")
                partial_matches = 0
                for course_word in course_words:
                    for question_word in question_words:
                        if (len(course_word) > 4 and len(question_word) > 4 and 
                            (course_word in question_word or question_word in course_word)):
                            partial_matches += 1
                            break
                
                if partial_matches >= 1:
                    found_courses.append((program.name, course.name, course.credits, course.semester, course.is_elective))
    
    if found_courses:
        if len(found_courses) == 1:
            program_name, course_name, credits, semester, is_elective = found_courses[0]
            course_type = "выборочный" if is_elective else "обязательный"
            return f"Курс **{course_name}** есть в программе **{program_name}** ({course_type}, {credits} кредитов, {semester} семестр)."
        else:
            answer = f"Найдено курсов: {len(found_courses)}\n\n"
            for program_name, course_name, credits, semester, is_elective in found_courses[:5]:  # Показываем максимум 5
                course_type = "выборочный" if is_elective else "обязательный"
                answer += f"• **{course_name}** ({course_type})\n"
                answer += f"  Программа: {program_name}\n"
                answer += f"  Кредиты: {credits}, Семестр: {semester}\n\n"
            return answer
    
    # Общий ответ если ничего конкретного не найдено
    return f"""
На основе доступных данных о программах могу ответить на вопросы о:
• Курсах и дисциплинах в программах
• Структуре программ обучения
• Требованиях к поступлению
• Содержании программ

{_get_programs_summary(programs)}

Попробуйте переформулировать вопрос более конкретно.
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