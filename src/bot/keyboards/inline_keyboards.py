from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ...data.models import ProgramType

def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Просмотр программ", callback_data="view_programs")],
        [InlineKeyboardButton(text="🎯 Получить рекомендации", callback_data="get_recommendations")],
        [InlineKeyboardButton(text="❓ Задать вопрос", callback_data="ask_question")],
        [InlineKeyboardButton(text="⚖️ Сравнить программы", callback_data="compare_programs")]
    ])

def create_program_selection_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🤖 Искусственный интеллект", 
            callback_data=f"program_{ProgramType.AI.value}"
        )],
        [InlineKeyboardButton(
            text="🚀 ИИ в продуктах", 
            callback_data=f"program_{ProgramType.AI_PRODUCT.value}"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])

def create_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])

def create_electives_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🤖 Выборочные для ИИ", 
            callback_data=f"electives_{ProgramType.AI.value}"
        )],
        [InlineKeyboardButton(
            text="🚀 Выборочные для ИИ в продуктах", 
            callback_data=f"electives_{ProgramType.AI_PRODUCT.value}"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]) 