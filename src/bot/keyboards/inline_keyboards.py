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
        text="Сравнить программы",
        callback_data="compare_programs"
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
    
    builder.adjust(2, 2, 1)
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
        ("Стартапы", "startup")
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

def get_courses_keyboard(courses: List[Course]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for course in courses[:10]:  # Показываем первые 10 курсов
        builder.add(InlineKeyboardButton(
            text=f"{course.name} ({course.credits} кр.)",
            callback_data=f"course_{course.id}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="Экспортировать список",
        callback_data="export_courses"
    ))
    builder.add(InlineKeyboardButton(
        text="Назад",
        callback_data="back_to_main"
    ))
    
    builder.adjust(1)
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