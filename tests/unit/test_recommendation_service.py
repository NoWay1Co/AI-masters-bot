import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from src.services.recommendation_service import RecommendationService
from src.data.models import UserProfile, Program, Course, ProgramType

@pytest.fixture
def recommendation_service():
    return RecommendationService()

@pytest.fixture
def sample_user_profile():
    return UserProfile(
        user_id="123",
        username="testuser",
        background="Computer Science student",
        interests=["machine learning", "neural networks"],
        goals=["work in AI", "research"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@pytest.fixture
def sample_programs():
    course1 = Course(
        id="c1",
        name="Machine Learning",
        credits=6,
        semester=1,
        is_elective=False
    )
    course2 = Course(
        id="c2",
        name="Deep Learning",
        credits=4,
        semester=2,
        is_elective=True
    )
    
    program = Program(
        id="p1",
        name="Artificial Intelligence",
        type=ProgramType.AI,
        url="https://example.com",
        courses=[course1, course2],
        total_credits=120,
        duration_semesters=4,
        description="AI program description",
        parsed_at=datetime.now()
    )
    
    return [program]

@pytest.mark.asyncio
async def test_get_program_recommendations_success(recommendation_service, sample_user_profile, sample_programs):
    with patch.object(recommendation_service, '_get_programs', return_value=sample_programs), \
         patch('src.services.recommendation_service.llm_service.generate_recommendations', 
               return_value="Great AI program recommendation"):
        
        result = await recommendation_service.get_program_recommendations(sample_user_profile)
        
        assert result == "Great AI program recommendation"

@pytest.mark.asyncio
async def test_get_program_recommendations_no_programs(recommendation_service, sample_user_profile):
    with patch.object(recommendation_service, '_get_programs', return_value=[]):
        
        result = await recommendation_service.get_program_recommendations(sample_user_profile)
        
        assert "данные о программах временно недоступны" in result.lower()

@pytest.mark.asyncio
async def test_get_program_recommendations_llm_failure(recommendation_service, sample_user_profile, sample_programs):
    with patch.object(recommendation_service, '_get_programs', return_value=sample_programs), \
         patch('src.services.recommendation_service.llm_service.generate_recommendations', 
               return_value=None):
        
        result = await recommendation_service.get_program_recommendations(sample_user_profile)
        
        assert "рекомендую программу" in result.lower()

@pytest.mark.asyncio
async def test_get_course_recommendations_with_interests(recommendation_service, sample_user_profile, sample_programs):
    sample_user_profile.interests = ["deep learning"]
    
    with patch.object(recommendation_service, '_get_programs', return_value=sample_programs):
        
        result = await recommendation_service.get_course_recommendations(
            sample_user_profile, ProgramType.AI
        )
        
        assert len(result) == 1
        assert result[0].name == "Deep Learning"

@pytest.mark.asyncio
async def test_get_course_recommendations_no_matches(recommendation_service, sample_user_profile, sample_programs):
    sample_user_profile.interests = ["unrelated topic"]
    
    with patch.object(recommendation_service, '_get_programs', return_value=sample_programs):
        
        result = await recommendation_service.get_course_recommendations(
            sample_user_profile, ProgramType.AI
        )
        
        assert len(result) == 1  # Should return first few courses as fallback

@pytest.mark.asyncio
async def test_get_course_recommendations_no_program(recommendation_service, sample_user_profile):
    with patch.object(recommendation_service, '_get_programs', return_value=[]):
        
        result = await recommendation_service.get_course_recommendations(
            sample_user_profile, ProgramType.AI
        )
        
        assert len(result) == 0

@pytest.mark.asyncio
async def test_compare_programs_success(recommendation_service, sample_programs):
    # Add second program for comparison
    second_program = Program(
        id="p2",
        name="AI in Products",
        type=ProgramType.AI_PRODUCT,
        url="https://example2.com",
        courses=[],
        total_credits=100,
        duration_semesters=4,
        description="AI Product program",
        parsed_at=datetime.now()
    )
    
    programs = sample_programs + [second_program]
    
    with patch.object(recommendation_service, '_get_programs', return_value=programs), \
         patch('src.services.recommendation_service.llm_service.generate_response', 
               return_value="Detailed comparison"):
        
        result = await recommendation_service.compare_programs()
        
        assert result == "Detailed comparison"

@pytest.mark.asyncio
async def test_compare_programs_insufficient_data(recommendation_service):
    with patch.object(recommendation_service, '_get_programs', return_value=[]):
        
        result = await recommendation_service.compare_programs()
        
        assert "недостаточно данных" in result.lower()

@pytest.mark.asyncio
async def test_compare_programs_llm_failure(recommendation_service, sample_programs):
    # Add second program
    second_program = Program(
        id="p2",
        name="AI in Products",
        type=ProgramType.AI_PRODUCT,
        url="https://example2.com",
        courses=[],
        total_credits=100,
        duration_semesters=4,
        parsed_at=datetime.now()
    )
    
    programs = sample_programs + [second_program]
    
    with patch.object(recommendation_service, '_get_programs', return_value=programs), \
         patch('src.services.recommendation_service.llm_service.generate_response', 
               return_value=None):
        
        result = await recommendation_service.compare_programs()
        
        assert "сравнение программ" in result.lower()

def test_format_user_profile(recommendation_service, sample_user_profile):
    result = recommendation_service._format_user_profile(sample_user_profile)
    
    assert "Computer Science student" in result
    assert "machine learning" in result
    assert "work in AI" in result

def test_format_user_profile_empty_fields(recommendation_service):
    profile = UserProfile(
        user_id="123",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    result = recommendation_service._format_user_profile(profile)
    
    assert "Не указан" in result
    assert "Не указаны" in result

def test_format_programs_data(recommendation_service, sample_programs):
    result = recommendation_service._format_programs_data(sample_programs)
    
    assert "Artificial Intelligence" in result
    assert "Machine Learning" in result
    assert "Deep Learning" in result
    assert "120" in result  # total credits

def test_generate_fallback_recommendation_product_interest(recommendation_service, sample_programs):
    profile = UserProfile(
        user_id="123",
        interests=["продукт", "разработка"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Mock programs with AI_PRODUCT type
    ai_product_program = Program(
        id="p2",
        name="AI in Products",
        type=ProgramType.AI_PRODUCT,
        url="https://example.com",
        courses=[],
        total_credits=100,
        duration_semesters=4,
        parsed_at=datetime.now()
    )
    
    programs = sample_programs + [ai_product_program]
    
    result = recommendation_service._generate_fallback_recommendation(profile, programs)
    
    assert "AI in Products" in result

def test_generate_fallback_recommendation_ai_default(recommendation_service, sample_programs):
    profile = UserProfile(
        user_id="123",
        interests=["машинное обучение"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    result = recommendation_service._generate_fallback_recommendation(profile, sample_programs)
    
    assert "Artificial Intelligence" in result 