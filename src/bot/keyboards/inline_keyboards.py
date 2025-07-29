from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from ...data.models import Program, Course, ProgramType

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="Выбрать программу",
        callback_data="select_program"
    ))
    builder.add(InlineKeyboardButton(
        text="Получить рекомендации",
        callback_data="get_recommendations"
    ))
    builder.add(InlineKeyboardButton(
        text="Задать вопрос",
        callback_data="qa_mode"
    ))
    builder.add(InlineKeyboardButton(
        text="Мой профиль",
        callback_data="view_profile"
    ))
    
    builder.adjust(2, 2)
    return builder.as_markup()

def get_programs_keyboard(programs: List[Program]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for program in programs:
        builder.add(InlineKeyboardButton(
            text=program.name,
            callback_data=f"program_{program.id}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="Назад",
        callback_data="back_to_main"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_profile_setup_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="Указать образование",
        callback_data="set_background"
    ))
    builder.add(InlineKeyboardButton(
        text="Указать интересы",
        callback_data="set_interests"
    ))
    builder.add(InlineKeyboardButton(
        text="Указать цели",
        callback_data="set_goals"
    ))
    builder.add(InlineKeyboardButton(
        text="Пропустить",
        callback_data="skip_profile"
    ))
    
    builder.adjust(2, 2)
    return builder.as_markup()

def get_interests_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    interests = [
        ("Машинное обучение", "ml"),
        ("Компьютерное зрение", "cv"),
        ("NLP", "nlp"),
        ("Робототехника", "robotics"),
        ("Продукты", "products"),
        ("Данные", "data"),
        ("Исследования", "research"),
        ("Стартапы", "startup"),
        ("Веб-разработка", "web"),
        ("Мобильная разработка", "mobile"),
        ("Игровая разработка", "gamedev"),
        ("Кибербезопасность", "security"),
        ("Блокчейн", "blockchain"),
        ("IoT", "iot"),
        ("AR/VR", "arvr"),
        ("DevOps", "devops"),
        ("UI/UX дизайн", "design"),
        ("Биоинформатика", "bioinformatics")
    ]
    
    for interest_text, interest_code in interests:
        builder.add(InlineKeyboardButton(
            text=interest_text,
            callback_data=f"int_{interest_code}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="Готово",
        callback_data="int_done"
    ))
    
    builder.adjust(2)
    return builder.as_markup()

def get_goals_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    goals = [
        ("Карьера в IT", "career"),
        ("Наука", "science"),
        ("Стартап", "startup"),
        ("Смена профессии", "change"),
        ("Углубить знания", "knowledge"),
        ("Получить диплом", "diploma")
    ]
    
    for goal_text, goal_code in goals:
        builder.add(InlineKeyboardButton(
            text=goal_text,
            callback_data=f"goal_{goal_code}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="Готово",
        callback_data="goal_done"
    ))
    
    builder.adjust(2)
    return builder.as_markup()

def get_courses_keyboard(courses: List[Course], page: int = 0, program_id: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Пагинация - по 5 курсов на страницу
    courses_per_page = 5
    start_idx = page * courses_per_page
    end_idx = start_idx + courses_per_page
    page_courses = courses[start_idx:end_idx]
    
    for course in page_courses:
        # Показываем тип курса в названии
        course_type = "Обяз." if not course.is_elective else "Выбор."
        builder.add(InlineKeyboardButton(
            text=f"{course_type} {course.name} ({course.credits} кр., сем. {course.semester})",
            callback_data=f"course_{course.id}"
        ))
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Пред.", callback_data=f"courses_page_{page-1}_{program_id}"))
    if end_idx < len(courses):
        nav_buttons.append(InlineKeyboardButton(text="След. ▶️", callback_data=f"courses_page_{page+1}_{program_id}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Дополнительные кнопки
    builder.add(InlineKeyboardButton(
        text="📄 Скачать программу",
        callback_data=f"download_program_{program_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="Главное меню",
        callback_data="back_to_main"
    ))
    
    builder.adjust(1, 2, 1, 1)
    return builder.as_markup()

def get_export_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="Скачать как текст",
        callback_data="export_text"
    ))
    builder.add(InlineKeyboardButton(
        text="Отправить в чат",
        callback_data="export_message"
    ))
    builder.add(InlineKeyboardButton(
        text="Отмена",
        callback_data="back_to_main"
    ))
    
    builder.adjust(2, 1)
    return builder.as_markup()

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="Да",
        callback_data="confirm_yes"
    ))
    builder.add(InlineKeyboardButton(
        text="Нет",
        callback_data="confirm_no"
    ))
    
    builder.adjust(2)
    return builder.as_markup()

def get_menu_button_keyboard() -> InlineKeyboardMarkup:
    """Создает простую клавиатуру с одной кнопкой 'Меню'"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="📱 Меню",
        callback_data="back_to_main"
    ))
    
    return builder.as_markup()

def get_program_actions_keyboard(program_id: str = None) -> InlineKeyboardMarkup:
    """Создает клавиатуру для действий с программой без показа курсов"""
    builder = InlineKeyboardBuilder()
    
    if program_id:
        builder.add(InlineKeyboardButton(
            text="📄 Скачать программу",
            callback_data=f"download_program_{program_id}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="🏠 Главное меню",
        callback_data="back_to_main"
    ))
    
    builder.adjust(1)
    return builder.as_markup() 