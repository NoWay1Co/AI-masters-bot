import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.services.parser_service import ITMOParser
from src.data.models import ProgramType, Course


class TestITMOParser:
    @pytest.fixture
    def parser(self):
        return ITMOParser()
    
    def test_get_file_extension(self, parser):
        assert parser._get_file_extension("http://example.com/file.pdf") == ".pdf"
        assert parser._get_file_extension("http://example.com/file.docx") == ".docx"
        assert parser._get_file_extension("http://example.com/file.xlsx") == ".xlsx"
        assert parser._get_file_extension("http://example.com/file.txt") == ""
    
    def test_create_course_from_match(self, parser):
        import re
        
        # Test pattern: "1. Course Name 5 з.е."
        pattern = r'(\d+)\.\s*(.+?)\s+(\d+)\s*з\.е\.'
        text = "1. Машинное обучение 5 з.е."
        match = re.search(pattern, text)
        
        course = parser._create_course_from_match(match, 1)
        
        assert course is not None
        assert course.name == "Машинное обучение"
        assert course.credits == 5
        assert course.semester == 1
        assert not course.is_elective
    
    def test_create_course_from_match_elective(self, parser):
        import re
        
        pattern = r'(\d+)\.\s*(.+?)\s+(\d+)\s*з\.е\.'
        text = "2. Выборная дисциплина 3 з.е."
        match = re.search(pattern, text)
        
        course = parser._create_course_from_match(match, 2)
        
        assert course is not None
        assert course.name == "Выборная дисциплина"
        assert course.credits == 3
        assert course.is_elective
    
    def test_extract_courses_from_text(self, parser):
        text = """
        1. Машинное обучение 5 з.е.
        2. Выборная дисциплина 3 з.е.
        Некоторый текст без курса
        3. Анализ данных 4 з.е.
        """
        
        courses = parser._extract_courses_from_text(text)
        
        assert len(courses) == 3
        assert courses[0].name == "Машинное обучение"
        assert courses[0].credits == 5
        assert courses[1].name == "Выборная дисциплина"
        assert courses[1].is_elective
        assert courses[2].name == "Анализ данных"
        assert courses[2].credits == 4
    
    @pytest.mark.asyncio
    async def test_parse_all_programs_with_cache(self, parser):
        with patch('src.services.parser_service.cache_service') as mock_cache:
            mock_cache.get = AsyncMock(return_value=[])
            mock_cache.set = AsyncMock()
            
            with patch.object(parser, '_parse_program_page', return_value=None):
                result = await parser.parse_all_programs()
                
                assert result == []
                mock_cache.get.assert_called_once_with("all_programs")
    
    @pytest.mark.asyncio
    async def test_parse_curriculum_file_unsupported_format(self, parser):
        result = await parser._parse_curriculum_file("http://example.com/file.txt")
        assert result == [] 