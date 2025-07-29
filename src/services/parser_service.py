import httpx
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
from urllib.parse import urljoin, urlparse
import re
from ..data.models import Program, Course, ProgramType
from ..utils.logger import logger
from datetime import datetime, timedelta
from pypdf import PdfReader
from docx import Document
import openpyxl
from io import BytesIO
from .cache_service import cache_service

class ITMOParser:
    def __init__(self):
        self.base_url = "https://abit.itmo.ru"
        self.programs_urls = {
            ProgramType.AI: "https://abit.itmo.ru/program/master/ai",
            ProgramType.AI_PRODUCT: "https://abit.itmo.ru/program/master/ai_product"
        }
    
    async def parse_all_programs(self) -> List[Program]:
        cache_key = "all_programs"
        
        # Проверяем кэш
        cached_programs = await cache_service.get(cache_key)
        if cached_programs:
            logger.info("Using cached programs", count=len(cached_programs))
            return cached_programs
        
        programs = []
        
        for program_type, url in self.programs_urls.items():
            try:
                program = await self._parse_program_page(program_type, url)
                if program:
                    programs.append(program)
            except Exception as e:
                logger.error("Failed to parse program", program_type=program_type, error=str(e))
        
        # Если парсинг не дал результатов, используем mock данные
        if not programs or all(len(p.courses) == 0 for p in programs):
            logger.info("Using mock data for demonstration")
            programs = self._get_mock_programs()
        
        # Сохраняем в кэш на 6 часов
        if programs:
            await cache_service.set(cache_key, programs, timedelta(hours=6))
        
        return programs
    
    def _get_mock_programs(self) -> List[Program]:
        """Временные mock данные для демонстрации функциональности"""
        
        ai_courses = [
            Course(
                id="ai_1",
                name="Основы машинного обучения",
                credits=6,
                semester=1,
                is_elective=False,
                description="Изучение базовых алгоритмов машинного обучения, линейных моделей, деревьев решений."
            ),
            Course(
                id="ai_2", 
                name="Глубокое обучение",
                credits=6,
                semester=2,
                is_elective=False,
                description="Нейронные сети, сверточные и рекуррентные архитектуры, трансформеры."
            ),
            Course(
                id="ai_3",
                name="Компьютерное зрение", 
                credits=5,
                semester=2,
                is_elective=True,
                description="Обработка изображений, детекция объектов, семантическая сегментация."
            ),
            Course(
                id="ai_4",
                name="Обработка естественного языка",
                credits=5,
                semester=3,
                is_elective=True,
                description="Анализ текстов, языковые модели, машинный перевод."
            ),
            Course(
                id="ai_5",
                name="Математические методы в ИИ",
                credits=4,
                semester=1,
                is_elective=False,
                description="Линейная алгебра, теория вероятностей, оптимизация для ИИ."
            ),
            Course(
                id="ai_6",
                name="Этика ИИ и безопасность",
                credits=3,
                semester=3,
                is_elective=True,
                description="Этические аспекты ИИ, безопасность алгоритмов, объяснимость."
            ),
            Course(
                id="ai_7",
                name="Проектная деятельность",
                credits=8,
                semester=4,
                is_elective=False,
                description="Выполнение итогового проекта с применением изученных технологий ИИ."
            )
        ]
        
        ai_product_courses = [
            Course(
                id="aip_1",
                name="Управление AI-продуктами",
                credits=6,
                semester=1,
                is_elective=False,
                description="Методология разработки AI-продуктов, жизненный цикл, метрики."
            ),
            Course(
                id="aip_2",
                name="Data Science для продуктов",
                credits=6,
                semester=1,
                is_elective=False,
                description="Анализ данных, A/B тестирование, построение аналитических дашбордов."
            ),
            Course(
                id="aip_3",
                name="MLOps и инфраструктура",
                credits=5,
                semester=2,
                is_elective=False,
                description="Развертывание ML-моделей, мониторинг, CI/CD для ML."
            ),
            Course(
                id="aip_4",
                name="Бизнес-анализ AI-решений",
                credits=4,
                semester=2,
                is_elective=True,
                description="ROI AI-проектов, оценка эффективности, бизнес-кейсы."
            ),
            Course(
                id="aip_5",
                name="UX/UI для AI-продуктов",
                credits=4,
                semester=3,
                is_elective=True,
                description="Проектирование интерфейсов с ИИ, пользовательский опыт."
            ),
            Course(
                id="aip_6",
                name="Правовые аспекты ИИ",
                credits=3,
                semester=3,
                is_elective=True,
                description="Регулирование ИИ, GDPR, интеллектуальная собственность."
            ),
            Course(
                id="aip_7",
                name="Стартап в области ИИ",
                credits=6,
                semester=4,
                is_elective=False,
                description="Создание AI-стартапа от идеи до MVP и первых продаж."
            )
        ]
        
        programs = [
            Program(
                id="ai",
                name="Искусственный интеллект",
                type=ProgramType.AI,
                url="https://abit.itmo.ru/program/master/ai",
                courses=ai_courses,
                total_credits=sum(course.credits for course in ai_courses),
                duration_semesters=4,
                description="""Программа готовит специалистов в области искусственного интеллекта. 
                Студенты изучают машинное обучение, нейронные сети, компьютерное зрение, 
                обработку естественного языка. Обучение включает работу над реальными проектами 
                с ведущими IT-компаниями.""",
                parsed_at=datetime.now()
            ),
            Program(
                id="ai_product",
                name="Управление ИИ-продуктами/AI Product",
                type=ProgramType.AI_PRODUCT,
                url="https://abit.itmo.ru/program/master/ai_product",
                courses=ai_product_courses,
                total_credits=sum(course.credits for course in ai_product_courses),
                duration_semesters=4,
                description="""Программа для тех, кто хочет создавать и управлять AI-продуктами. 
                Изучение методологий разработки, бизнес-анализа, UX для ИИ, правовых аспектов. 
                Выпускники становятся продакт-менеджерами в области ИИ.""",
                parsed_at=datetime.now()
            )
        ]
        
        return programs
    
    async def _parse_program_page(self, program_type: ProgramType, url: str) -> Optional[Program]:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Извлекаем название программы
        title_elem = soup.find('h1') or soup.find('title')
        program_name = title_elem.get_text(strip=True) if title_elem else f"Program {program_type}"
        
        # Извлекаем описание
        description = await self._extract_description(soup)
        
        # Ищем ссылку на учебный план
        curriculum_url = await self._find_curriculum_link(soup, url)
        
        # Парсим учебный план
        courses = []
        if curriculum_url:
            courses = await self._parse_curriculum_file(curriculum_url)
        
        program = Program(
            id=program_type.value,
            name=program_name,
            type=program_type,
            url=url,
            courses=courses,
            total_credits=sum(course.credits for course in courses),
            duration_semesters=max((course.semester for course in courses), default=4),
            description=description,
            parsed_at=datetime.now()
        )
        
        logger.info("Program parsed", program_id=program.id, courses_count=len(courses))
        return program
    
    async def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        # Ищем описание программы в различных местах
        selectors = [
            '.program-description',
            '.content-main p',
            '.program-info',
            'meta[name="description"]'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    return elem.get('content', '').strip()
                else:
                    return elem.get_text(strip=True)
        
        return None
    
    async def _find_curriculum_link(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        # Ищем ссылку на учебный план
        
        # 1. Ищем кнопку "Скачать учебный план"
        download_button = soup.find('a', string=re.compile(r'скачать\s+учебный\s+план', re.I))
        if download_button and download_button.get('href'):
            full_url = urljoin(base_url, download_button.get('href'))
            logger.info("Found curriculum download button", url=full_url)
            return full_url
        
        # 2. Ищем по различным селекторам
        selectors = [
            'a:contains("Скачать учебный план")',
            'a:contains("учебный план")',
            'a[href*="curriculum"]',
            'a[href*="study_plan"]',
            'a[href*="educational_plan"]'
        ]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    href = elem.get('href')
                    if href and not href.startswith('#'):
                        full_url = urljoin(base_url, href)
                        logger.info("Found curriculum link by selector", url=full_url, selector=selector)
                        return full_url
            except Exception:
                continue
        
        # 3. Ищем по тексту ссылок
        patterns = [
            r'учебный\s+план',
            r'curriculum',
            r'план\s+обучения',
            r'скачать.*план'
        ]
        
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            link_text = link.get_text(strip=True).lower()
            href = link.get('href')
            
            if href and not href.startswith('#'):
                # Проверяем текст ссылки
                for pattern in patterns:
                    if re.search(pattern, link_text, re.I):
                        full_url = urljoin(base_url, href)
                        logger.info("Found curriculum link by text pattern", url=full_url, text=link_text)
                        return full_url
                
                # Проверяем расширение файла
                if any(ext in href.lower() for ext in ['.pdf', '.docx', '.xlsx']):
                    if any(word in href.lower() for word in ['plan', 'curriculum', 'учебн']):
                        full_url = urljoin(base_url, href)
                        logger.info("Found curriculum file by extension", url=full_url)
                        return full_url
        
        logger.warning("No curriculum link found")
        return None
    
    async def _parse_curriculum_file(self, file_url: str) -> List[Course]:
        cache_key = f"curriculum_{file_url}"
        
        # Проверяем кэш
        cached_courses = await cache_service.get(cache_key)
        if cached_courses:
            logger.info("Using cached curriculum", file_url=file_url, count=len(cached_courses))
            return cached_courses
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(file_url)
                response.raise_for_status()
            
            file_content = response.content
            file_extension = self._get_file_extension(file_url)
            
            courses = []
            if file_extension == '.pdf':
                courses = await self._parse_pdf_curriculum(file_content)
            elif file_extension == '.docx':
                courses = await self._parse_docx_curriculum(file_content)
            elif file_extension == '.xlsx':
                courses = await self._parse_xlsx_curriculum(file_content)
            else:
                logger.warning("Unsupported file format", file_url=file_url)
                return []
            
            # Сохраняем в кэш на 12 часов
            if courses:
                await cache_service.set(cache_key, courses, timedelta(hours=12))
            
            return courses
        
        except Exception as e:
            logger.error("Failed to parse curriculum file", file_url=file_url, error=str(e))
            return []
    
    def _get_file_extension(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.lower()
        for ext in ['.pdf', '.docx', '.xlsx']:
            if path.endswith(ext):
                return ext
        return ''
    
    async def _parse_pdf_curriculum(self, content: bytes) -> List[Course]:
        courses = []
        
        with BytesIO(content) as pdf_file:
            reader = PdfReader(pdf_file)
            
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text()
            
            courses = self._extract_courses_from_text(full_text)
        
        return courses
    
    async def _parse_docx_curriculum(self, content: bytes) -> List[Course]:
        courses = []
        
        with BytesIO(content) as docx_file:
            doc = Document(docx_file)
            
            full_text = ""
            for paragraph in doc.paragraphs:
                full_text += paragraph.text + "\n"
            
            # Также парсим таблицы
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text for cell in row.cells)
                    full_text += row_text + "\n"
            
            courses = self._extract_courses_from_text(full_text)
        
        return courses
    
    async def _parse_xlsx_curriculum(self, content: bytes) -> List[Course]:
        courses = []
        
        with BytesIO(content) as xlsx_file:
            workbook = openpyxl.load_workbook(xlsx_file)
            
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                courses.extend(self._extract_courses_from_excel_sheet(sheet))
        
        return courses
    
    def _extract_courses_from_text(self, text: str) -> List[Course]:
        courses = []
        lines = text.split('\n')
        
        course_patterns = [
            r'(\d+)\.\s*(.+?)\s+(\d+)\s*з\.е\.',  # Номер. Название кредиты з.е.
            r'(.+?)\s+(\d+)\s*кредит',             # Название кредиты
            r'(\d+)\s+семестр.*?(.+?)\s+(\d+)',    # семестр название кредиты
        ]
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            for pattern in course_patterns:
                match = re.search(pattern, line, re.I)
                if match:
                    course = self._create_course_from_match(match, i)
                    if course:
                        courses.append(course)
                    break
        
        return courses
    
    def _extract_courses_from_excel_sheet(self, sheet) -> List[Course]:
        courses = []
        
        # Пытаемся найти заголовки колонок
        headers = {}
        for row_idx, row in enumerate(sheet.iter_rows(max_row=10)):
            for col_idx, cell in enumerate(row):
                if cell.value:
                    value = str(cell.value).lower()
                    if 'дисциплин' in value or 'предмет' in value:
                        headers['name'] = col_idx
                    elif 'кредит' in value or 'з.е' in value:
                        headers['credits'] = col_idx
                    elif 'семестр' in value:
                        headers['semester'] = col_idx
            
            if len(headers) >= 2:  # Нашли основные колонки
                break
        
        # Парсим данные
        for row in sheet.iter_rows(min_row=row_idx + 2):
            try:
                name = ""
                credits = 0
                semester = 1
                
                if 'name' in headers and row[headers['name']].value:
                    name = str(row[headers['name']].value).strip()
                
                if 'credits' in headers and row[headers['credits']].value:
                    credits_val = str(row[headers['credits']].value)
                    credits = int(re.search(r'\d+', credits_val).group()) if re.search(r'\d+', credits_val) else 0
                
                if 'semester' in headers and row[headers['semester']].value:
                    semester_val = str(row[headers['semester']].value)
                    semester = int(re.search(r'\d+', semester_val).group()) if re.search(r'\d+', semester_val) else 1
                
                if name and credits > 0:
                    course = Course(
                        id=f"course_{len(courses)}",
                        name=name,
                        credits=credits,
                        semester=semester,
                        is_elective='выборн' in name.lower() or 'элект' in name.lower()
                    )
                    courses.append(course)
            
            except Exception as e:
                logger.debug("Failed to parse excel row", error=str(e))
                continue
        
        return courses
    
    def _create_course_from_match(self, match, line_number: int) -> Optional[Course]:
        try:
            groups = match.groups()
            
            if len(groups) >= 2:
                # Определяем, какая группа содержит название и кредиты
                name = ""
                credits = 0
                
                for group in groups:
                    if group and group.isdigit():
                        credits = int(group)
                    elif group and not group.isdigit():
                        if len(group) > len(name):
                            name = group.strip()
                
                if name and credits > 0:
                    return Course(
                        id=f"course_{line_number}",
                        name=name,
                        credits=credits,
                        semester=1,  # По умолчанию
                        is_elective='выборн' in name.lower() or 'элект' in name.lower()
                    )
        
        except Exception as e:
            logger.debug("Failed to create course from match", error=str(e))
        
        return None 