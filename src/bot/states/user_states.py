from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    # Начальные состояния
    MAIN_MENU = State()
    
    # Сбор профиля пользователя
    COLLECTING_BACKGROUND = State()
    COLLECTING_INTERESTS = State()
    COLLECTING_GOALS = State()
    
    # Выбор программы
    PROGRAM_SELECTION = State()
    PROGRAM_COMPARISON = State()
    
    # Рекомендации
    GETTING_RECOMMENDATIONS = State()
    VIEWING_COURSES = State()
    
    # Q&A режим
    QA_MODE = State()
    
    # Экспорт данных
    EXPORT_FORMAT_SELECTION = State() 