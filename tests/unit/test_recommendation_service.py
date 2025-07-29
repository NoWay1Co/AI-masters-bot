import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from src.services.recommendation_service import RecommendationService
from src.data.models import UserProfile, Program, Course, ProgramType

class TestRecommendationService:
    @pytest.fixture
    def recommendation_service(self):
        return RecommendationService()
    
    @pytest.fixture
    def sample_user_profile(self):
        return UserProfile(
            user_id="123456",
            username="test_user",
            background="Computer Science",
            interests=["Machine Learning", "Data Science"],
            goals=["career change"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_programs(self):
        ai_program = Program(
            id="ai_program",
            name="Искусственный интеллект",
            type=ProgramType.AI,
            url="https://example.com/ai",
            courses=[
                Course(
                    id="course1",
                    name="Машинное обучение",
                    credits=6,
                    semester=1,
                    is_elective=False
                ),
                Course(
                    id="course2",
                    name="Глубокое обучение",
                    credits=4,
                    semester=2,
                    is_elective=False
                )
            ],
            total_credits=120,
            duration_semesters=4,
            parsed_at=datetime.now()
        )
        
        product_program = Program(
            id="ai_product",
            name="Продукты с ИИ",
            type=ProgramType.AI_PRODUCT,
            url="https://example.com/ai-product",
            courses=[
                Course(
                    id="course3",
                    name="Product Management",
                    credits=5,
                    semester=1,
                    is_elective=False
                )
            ],
            total_credits=100,
            duration_semesters=3,
            parsed_at=datetime.now()
        )
        
        return [ai_program, product_program]
    
    @pytest.mark.asyncio
    async def test_get_program_recommendations_success(self, recommendation_service, sample_user_profile):
        mock_programs = [MagicMock(), MagicMock()]
        mock_llm_response = "Рекомендуем программу ИИ"
        
        with patch.object(recommendation_service, '_get_programs', return_value=mock_programs), \
             patch('src.services.recommendation_service.llm_service.generate_recommendations', 
                   return_value=mock_llm_response):
            
            result = await recommendation_service.get_program_recommendations(sample_user_profile)
            
            assert result == mock_llm_response
    
    @pytest.mark.asyncio
    async def test_get_program_recommendations_no_programs(self, recommendation_service, sample_user_profile):
        with patch.object(recommendation_service, '_get_programs', return_value=[]):
            
            result = await recommendation_service.get_program_recommendations(sample_user_profile)
            
            assert "данные о программах временно недоступны" in result.lower()
    
    @pytest.mark.asyncio 
    async def test_get_program_recommendations_llm_failure(self, recommendation_service, sample_user_profile):
        mock_programs = [MagicMock()]
        
        with patch.object(recommendation_service, '_get_programs', return_value=mock_programs), \
             patch('src.services.recommendation_service.llm_service.generate_recommendations', 
                   return_value=None):
            
            result = await recommendation_service.get_program_recommendations(sample_user_profile)
            
            assert "рекомендую программу" in result.lower()
    
    def test_format_user_profile(self, recommendation_service, sample_user_profile):
        result = recommendation_service._format_user_profile(sample_user_profile)
        
        assert "Computer Science" in result
        assert "Machine Learning" in result
        assert "career change" in result
    
    def test_format_programs_data(self, recommendation_service, sample_programs):
        result = recommendation_service._format_programs_data(sample_programs)
        
        assert "Искусственный интеллект" in result
        assert "Продукты с ИИ" in result
        assert "120" in result  # total credits
        assert "Машинное обучение" in result
    
    @pytest.mark.asyncio
    async def test_compare_programs_success(self, recommendation_service):
        mock_programs = [MagicMock(), MagicMock()]
        mock_llm_response = "Сравнение программ"
        
        with patch.object(recommendation_service, '_get_programs', return_value=mock_programs), \
             patch('src.services.recommendation_service.llm_service.generate_response', 
                   return_value=mock_llm_response):
            
            result = await recommendation_service.compare_programs()
            
            assert result == mock_llm_response
    
    @pytest.mark.asyncio
    async def test_compare_programs_insufficient_data(self, recommendation_service):
        with patch.object(recommendation_service, '_get_programs', return_value=[]):
            
            result = await recommendation_service.compare_programs()
            
            assert "недостаточно данных" in result.lower() 