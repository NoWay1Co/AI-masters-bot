from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class ProgramType(str, Enum):
    AI = "ai"
    AI_PRODUCT = "ai_product"

class Course(BaseModel):
    id: str
    name: str
    credits: int
    hours: int = 0  # Добавляем часы
    semester: int
    is_elective: bool
    block: Optional[str] = None  # Блок (Модули, Практики, ГИА и т.д.)
    category: Optional[str] = None  # Категория дисциплины
    prerequisites: List[str] = []
    description: Optional[str] = None

class ProgramDetails(BaseModel):
    """Дополнительная информация о программе со страницы"""
    form_of_study: Optional[str] = None  # Форма обучения
    duration: Optional[str] = None  # Длительность
    language: Optional[str] = None  # Язык обучения
    cost_per_year: Optional[str] = None  # Стоимость контрактного обучения (год)
    dormitory: Optional[str] = None  # Общежитие
    military_center: Optional[str] = None  # Военный учебный центр
    accreditation: Optional[str] = None  # Гос. аккредитация
    additional_opportunities: Optional[str] = None  # Дополнительные возможности
    program_manager: Optional[str] = None  # Менеджер программы
    manager_contacts: Optional[str] = None  # Контакты менеджера
    study_directions: Optional[str] = None  # Направления подготовки
    about_program: Optional[str] = None  # О программе

class Program(BaseModel):
    id: str
    name: str
    type: ProgramType
    url: str
    courses: List[Course]
    total_credits: int
    duration_semesters: int
    description: Optional[str] = None
    details: Optional[ProgramDetails] = None  # Дополнительная информация
    parsed_at: datetime

class UserProfile(BaseModel):
    user_id: str
    username: Optional[str] = None
    background: Optional[str] = None
    interests: List[str] = []
    goals: List[str] = []
    preferred_program: Optional[ProgramType] = None
    created_at: datetime
    updated_at: datetime

class UserSession(BaseModel):
    user_id: str
    current_state: Optional[str] = None
    session_data: Dict = {}
    created_at: datetime 