import pytest
from datetime import datetime
from src.data.models import Program, Course, UserProfile, UserSession, ProgramType

def test_course_model():
    """Test Course model creation and validation"""
    course = Course(
        id="cs101",
        name="Computer Science Basics",
        credits=5,
        semester=1,
        is_elective=False,
        prerequisites=["math101"],
        description="Introduction to computer science",
        category="core"
    )
    
    assert course.id == "cs101"
    assert course.name == "Computer Science Basics"
    assert course.credits == 5
    assert course.is_elective is False
    assert len(course.prerequisites) == 1

def test_program_model():
    """Test Program model creation and validation"""
    course = Course(
        id="cs101",
        name="Computer Science Basics", 
        credits=5,
        semester=1,
        is_elective=False
    )
    
    program = Program(
        id="ai_masters",
        name="AI Masters Program",
        type=ProgramType.AI,
        url="https://example.com/ai",
        courses=[course],
        total_credits=120,
        duration_semesters=4,
        description="Advanced AI program",
        parsed_at=datetime.now()
    )
    
    assert program.type == ProgramType.AI
    assert len(program.courses) == 1
    assert program.total_credits == 120

def test_user_profile_model():
    """Test UserProfile model creation and validation"""
    now = datetime.now()
    profile = UserProfile(
        user_id="12345",
        username="testuser",
        background="Computer Science",
        interests=["AI", "ML"],
        goals=["Learn AI", "Get job"],
        preferred_program=ProgramType.AI,
        created_at=now,
        updated_at=now
    )
    
    assert profile.user_id == "12345"
    assert len(profile.interests) == 2
    assert profile.preferred_program == ProgramType.AI

def test_user_session_model():
    """Test UserSession model creation and validation"""
    session = UserSession(
        user_id="12345",
        current_state="program_selection",
        session_data={"step": 1, "answers": []},
        created_at=datetime.now()
    )
    
    assert session.user_id == "12345"
    assert session.current_state == "program_selection"
    assert "step" in session.session_data 