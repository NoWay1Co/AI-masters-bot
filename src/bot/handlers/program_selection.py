from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from ...services.recommendation_service import recommendation_service
from ...data.models import ProgramType
from ...utils.logger import logger
from ..keyboards.inline_keyboards import create_program_selection_keyboard, create_back_keyboard

router = Router()

@router.callback_query(F.data == "view_programs")
async def view_programs_handler(callback: CallbackQuery):
    await callback.answer()
    
    await callback.message.edit_text(
        "Доступные программы магистратуры ИТМО по ИИ:",
        reply_markup=create_program_selection_keyboard()
    )

@router.callback_query(F.data.startswith("program_"))
async def program_details_handler(callback: CallbackQuery):
    await callback.answer()
    
    program_type_str = callback.data.split("_")[1]
    program_type = ProgramType(program_type_str)
    
    await callback.message.edit_text(
        "Загружаю информацию о программе...",
        reply_markup=None
    )
    
    try:
        programs = await recommendation_service._get_programs()
        target_program = next((p for p in programs if p.type == program_type), None)
        
        if not target_program:
            await callback.message.edit_text(
                "Информация о программе временно недоступна.",
                reply_markup=create_back_keyboard()
            )
            return
        
        # Формируем детальную информацию о программе
        courses_count = len(target_program.courses)
        elective_count = len([c for c in target_program.courses if c.is_elective])
        required_count = courses_count - elective_count
        
        program_info = f"""
**{target_program.name}**

📋 **Описание:**
{target_program.description or 'Описание скоро будет добавлено'}

📊 **Основная информация:**
• Продолжительность: {target_program.duration_semesters} семестра
• Общие кредиты: {target_program.total_credits}
• Всего курсов: {courses_count}
• Обязательных: {required_count}
• Выборочных: {elective_count}

🔗 **Подробнее:** {target_program.url}
        """
        
        # Добавляем несколько ключевых курсов
        if target_program.courses:
            program_info += "\n\n📚 **Некоторые курсы:**\n"
            for course in target_program.courses[:5]:
                program_info += f"• {course.name} ({course.credits} кредитов)\n"
            
            if len(target_program.courses) > 5:
                program_info += f"• ... и еще {len(target_program.courses) - 5} курсов\n"
        
        await callback.message.edit_text(
            program_info,
            reply_markup=create_back_keyboard(),
            parse_mode="Markdown"
        )
        
        logger.info("Program details viewed", 
                   user_id=callback.from_user.id, 
                   program_type=program_type.value)
        
    except Exception as e:
        logger.error("Failed to load program details", 
                    user_id=callback.from_user.id, 
                    program_type=program_type_str,
                    error=str(e))
        
        await callback.message.edit_text(
            "Произошла ошибка при загрузке информации о программе. Попробуйте позже.",
            reply_markup=create_back_keyboard()
        ) 