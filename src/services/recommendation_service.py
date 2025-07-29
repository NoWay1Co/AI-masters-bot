from typing import List, Optional, Dict
import json
from ..data.models import UserProfile, Program, Course, ProgramType
from .llm_service import llm_service
from ..data.json_storage import storage
from ..utils.logger import logger

class RecommendationService:
    def __init__(self):
        self.programs_cache: List[Program] = []
    
    async def get_program_recommendations(self, user_profile: UserProfile) -> Optional[str]:
        try:
            programs = await self._get_programs()
            if not programs:
                return "К сожалению, данные о программах временно недоступны."
            
            user_profile_text = self._format_user_profile(user_profile)
            programs_text = self._format_programs_data(programs)
            
            recommendation = await llm_service.generate_recommendations(
                user_profile_text, programs_text
            )
            
            if recommendation:
                logger.info("Recommendation generated", user_id=user_profile.user_id)
                return recommendation
            else:
                return self._generate_fallback_recommendation(user_profile, programs)
        
        except Exception as e:
            logger.error("Failed to generate recommendation", user_id=user_profile.user_id, error=str(e))
            return "Произошла ошибка при генерации рекомендаций. Попробуйте позже."
    
    async def get_course_recommendations(self, user_profile: UserProfile, program_type: ProgramType) -> List[Course]:
        try:
            programs = await self._get_programs()
            target_program = next((p for p in programs if p.type == program_type), None)
            
            if not target_program:
                return []
            
            elective_courses = [course for course in target_program.courses if course.is_elective]
            
            # Простая логика выбора на основе интересов пользователя
            recommended_courses = []
            user_interests = [interest.lower() for interest in user_profile.interests]
            
            for course in elective_courses:
                course_name_lower = course.name.lower()
                relevance_score = sum(
                    1 for interest in user_interests
                    if interest in course_name_lower
                )
                
                if relevance_score > 0:
                    recommended_courses.append(course)
            
            # Если нет совпадений, возвращаем первые несколько курсов
            if not recommended_courses:
                recommended_courses = elective_courses[:3]
            
            return recommended_courses
        
        except Exception as e:
            logger.error("Failed to get course recommendations", error=str(e))
            return []
    
    async def compare_programs(self) -> Optional[str]:
        try:
            programs = await self._get_programs()
            if len(programs) < 2:
                return "Недостаточно данных для сравнения программ."
            
            comparison_data = self._format_programs_comparison(programs)
            
            prompt = f"""
            Сравни две магистерские программы ИТМО по ИИ:
            
            {comparison_data}
            
            Проведи детальное сравнение по следующим критериям:
            1. Фокус и специализация
            2. Количество и виды курсов
            3. Практическая направленность
            4. Подходящий профиль студента
            
            Ответ:
            """
            
            comparison = await llm_service.generate_response(prompt)
            return comparison or self._generate_fallback_comparison(programs)
        
        except Exception as e:
            logger.error("Failed to compare programs", error=str(e))
            return "Ошибка при сравнении программ."
    
    async def _get_programs(self) -> List[Program]:
        if not self.programs_cache:
            self.programs_cache = await storage.load_programs()
        return self.programs_cache
    
    def _format_user_profile(self, profile: UserProfile) -> str:
        background = profile.background or "Не указан"
        interests = ", ".join(profile.interests) if profile.interests else "Не указаны"
        goals = ", ".join(profile.goals) if profile.goals else "Не указаны"
        
        return f"""
        Опыт и образование: {background}
        Интересы: {interests}
        Цели: {goals}
        """
    
    def _format_programs_data(self, programs: List[Program]) -> str:
        programs_text = ""
        
        for program in programs:
            courses_count = len(program.courses)
            elective_count = len([c for c in program.courses if c.is_elective])
            
            programs_text += f"""
            Программа: {program.name}
            Описание: {program.description or 'Описание недоступно'}
            Общее количество курсов: {courses_count}
            Выборочных дисциплин: {elective_count}
            Общие кредиты: {program.total_credits}
            
            Основные курсы:
            """
            
            for course in program.courses[:10]:  # Первые 10 курсов
                programs_text += f"- {course.name} ({course.credits} кредитов)\n"
            
            programs_text += "\n"
        
        return programs_text
    
    def _format_programs_comparison(self, programs: List[Program]) -> str:
        comparison_text = ""
        
        for i, program in enumerate(programs, 1):
            comparison_text += f"""
            Программа {i}: {program.name}
            - Всего курсов: {len(program.courses)}
            - Выборочных: {len([c for c in program.courses if c.is_elective])}
            - Кредиты: {program.total_credits}
            - Семестры: {program.duration_semesters}
            
            """
        
        return comparison_text
    
    def _generate_fallback_recommendation(self, profile: UserProfile, programs: List[Program]) -> str:
        if not programs:
            return "Данные о программах недоступны."
        
        # Простая логика выбора программы
        if any("продукт" in interest.lower() for interest in profile.interests):
            recommended_program = next(
                (p for p in programs if p.type == ProgramType.AI_PRODUCT), 
                programs[0]
            )
        else:
            recommended_program = next(
                (p for p in programs if p.type == ProgramType.AI), 
                programs[0]
            )
        
        return f"""
        На основе вашего профиля рекомендую программу: {recommended_program.name}
        
        Эта программа включает {len(recommended_program.courses)} курсов 
        и предлагает {len([c for c in recommended_program.courses if c.is_elective])} выборочных дисциплин.
        
        Для получения более детальных рекомендаций обратитесь к консультанту.
        """
    
    def _generate_fallback_comparison(self, programs: List[Program]) -> str:
        if len(programs) < 2:
            return "Недостаточно программ для сравнения."
        
        prog1, prog2 = programs[0], programs[1]
        
        return f"""
        Сравнение программ:
        
        {prog1.name}:
        - Курсов: {len(prog1.courses)}
        - Кредитов: {prog1.total_credits}
        
        {prog2.name}:
        - Курсов: {len(prog2.courses)}
        - Кредитов: {prog2.total_credits}
        
        Для детального анализа требуется дополнительная информация.
        """

recommendation_service = RecommendationService() 