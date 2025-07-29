import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from src.data.json_storage import JSONStorage
from src.data.models import Program, Course, UserProfile, ProgramType

@pytest.fixture
def temp_storage():
    """Create temporary storage for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    storage = JSONStorage(data_dir=temp_dir)
    yield storage
    shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_save_and_load_programs(temp_storage):
    """Test saving and loading programs"""
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
        parsed_at=datetime.now()
    )
    
    await temp_storage.save_programs([program])
    loaded_programs = await temp_storage.load_programs()
    
    assert len(loaded_programs) == 1
    assert loaded_programs[0].id == "ai_masters"
    assert loaded_programs[0].type == ProgramType.AI
    assert len(loaded_programs[0].courses) == 1

@pytest.mark.asyncio
async def test_save_and_load_user_profile(temp_storage):
    """Test saving and loading user profiles"""
    now = datetime.now()
    profile = UserProfile(
        user_id="12345",
        username="testuser",
        background="Computer Science",
        interests=["AI", "ML"],
        created_at=now,
        updated_at=now
    )
    
    await temp_storage.save_user_profile(profile)
    loaded_profile = await temp_storage.load_user_profile("12345")
    
    assert loaded_profile is not None
    assert loaded_profile.user_id == "12345"
    assert loaded_profile.username == "testuser"
    assert len(loaded_profile.interests) == 2

@pytest.mark.asyncio
async def test_load_nonexistent_user_profile(temp_storage):
    """Test loading non-existent user profile returns None"""
    profile = await temp_storage.load_user_profile("nonexistent")
    assert profile is None

@pytest.mark.asyncio
async def test_load_programs_empty_file(temp_storage):
    """Test loading programs when file doesn't exist"""
    programs = await temp_storage.load_programs()
    assert programs == [] 