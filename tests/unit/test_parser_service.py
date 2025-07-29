import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from src.services.parser_service import ITMOParser
from src.data.models import Program, Course, ProgramType

class TestITMOParser:
    @pytest.fixture
    def parser(self):
        return ITMOParser()
    
    @pytest.fixture
    def mock_html_response(self):
        return """
        <html>
            <head><title>Искусственный интеллект - ИТМО</title></head>
            <body>
                <h1>Магистратура "Искусственный интеллект"</h1>
                <p class="program-description">Программа для подготовки специалистов в области ИИ</p>
                <a href="/files/curriculum.pdf">Скачать учебный план</a>
            </body>
        </html>
        """
    
    @pytest.mark.asyncio
    async def test_parse_program_page_success(self, parser, mock_html_response):
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.text = mock_html_response
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with patch.object(parser, '_parse_curriculum_file', return_value=[]):
                program = await parser._parse_program_page(
                    ProgramType.AI, 
                    "https://abit.itmo.ru/program/master/ai"
                )
            
            assert program is not None
            assert program.name == "Магистратура \"Искусственный интеллект\""
            assert program.type == ProgramType.AI
            assert "подготовки специалистов" in program.description
    
    @pytest.mark.asyncio
    async def test_find_curriculum_link(self, parser):
        html = """
        <html>
            <body>
                <a href="/files/plan.pdf">Скачать учебный план</a>
                <a href="/other.pdf">Другой файл</a>
            </body>
        </html>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        link = await parser._find_curriculum_link(soup, "https://example.com")
        
        assert link == "https://example.com/files/plan.pdf"
    
    def test_extract_courses_from_text(self, parser):
        text = """
        1. Машинное обучение 6 з.е.
        2. Компьютерное зрение 4 з.е.
        3. Выборочная дисциплина 3 з.е.
        """
        
        courses = parser._extract_courses_from_text(text)
        
        assert len(courses) == 3
        assert courses[0].name == "Машинное обучение"
        assert courses[0].credits == 6
        assert courses[2].is_elective == True
    
    @pytest.mark.asyncio
    async def test_parse_all_programs(self, parser):
        with patch.object(parser, '_parse_program_page') as mock_parse:
            mock_program = Program(
                id="ai",
                name="Test Program",
                type=ProgramType.AI,
                url="https://test.com",
                courses=[],
                total_credits=120,
                duration_semesters=4,
                parsed_at=datetime.now()
            )
            mock_parse.return_value = mock_program
            
            programs = await parser.parse_all_programs()
            
            assert len(programs) == 2  # AI and AI_PRODUCT
            assert all(isinstance(p, Program) for p in programs)
    
    @pytest.mark.asyncio
    async def test_parse_program_page_http_error(self, parser):
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("HTTP Error")
            
            program = await parser._parse_program_page(
                ProgramType.AI, 
                "https://invalid-url.com"
            )
            
            assert program is None
    
    def test_extract_courses_invalid_format(self, parser):
        text = "Некорректный формат текста без дисциплин"
        
        courses = parser._extract_courses_from_text(text)
        
        assert len(courses) == 0 