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
    semester: int
    is_elective: bool
    prerequisites: List[str] = []
    description: Optional[str] = None
    category: Optional[str] = None

class Program(BaseModel):
    id: str
    name: str
    type: ProgramType
    url: str
    courses: List[Course]
    total_credits: int
    duration_semesters: int
    description: Optional[str] = None
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