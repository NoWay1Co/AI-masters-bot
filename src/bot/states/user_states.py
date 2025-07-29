from aiogram.fsm.state import State, StatesGroup

class ProfileState(StatesGroup):
    waiting_for_background = State()
    waiting_for_interests = State()
    waiting_for_goals = State()

class QuestionState(StatesGroup):
    waiting_for_question = State()

class ProgramSelectionState(StatesGroup):
    selecting_program = State()
    viewing_details = State() 