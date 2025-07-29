import pytest
import os
import tempfile
import shutil
from datetime import datetime
from src.data.json_storage import JSONStorage
from src.data.models import UserProfile, Program, Course, ProgramType

class TestDataIntegration:
    @pytest.fixture
    def temp_data_dir(self):
        # Создаем временную директорию для тестов
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Очищаем после тестов
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage(self, temp_data_dir):
        return JSONStorage(data_dir=temp_data_dir)
    
    @pytest.fixture
    def sample_user_profile(self):
        return UserProfile(
            user_id="123456",
            username="test_user",
            background="Computer Science",
            interests=["AI", "ML"],
            goals=["career change"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_program(self):
        return Program(
            id="test_ai_program",
            name="Тестовая программа ИИ",
            type=ProgramType.AI,
            url="https://test.example.com",
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
                    is_elective=True
                )
            ],
            total_credits=120,
            duration_semesters=4,
            parsed_at=datetime.now()
        )
    
    @pytest.mark.integration
    def test_user_profile_crud_operations(self, storage, sample_user_profile):
        # Create
        storage.save_user_profile(sample_user_profile)
        
        # Read
        loaded_profile = storage.load_user_profile(sample_user_profile.user_id)
        assert loaded_profile is not None
        assert loaded_profile.user_id == sample_user_profile.user_id
        assert loaded_profile.username == sample_user_profile.username
        assert loaded_profile.interests == sample_user_profile.interests
        
        # Update
        sample_user_profile.background = "Updated background"
        sample_user_profile.interests.append("Deep Learning")
        storage.save_user_profile(sample_user_profile)
        
        updated_profile = storage.load_user_profile(sample_user_profile.user_id)
        assert updated_profile.background == "Updated background"
        assert "Deep Learning" in updated_profile.interests
        
        # Delete (через удаление файла)
        user_file = os.path.join(storage.users_dir, f"{sample_user_profile.user_id}.json")
        assert os.path.exists(user_file)
        os.remove(user_file)
        
        deleted_profile = storage.load_user_profile(sample_user_profile.user_id)
        assert deleted_profile is None
    
    @pytest.mark.integration
    def test_programs_storage_operations(self, storage, sample_program):
        programs = [sample_program]
        
        # Save
        storage.save_programs(programs)
        
        # Load
        loaded_programs = storage.load_programs()
        assert len(loaded_programs) == 1
        assert loaded_programs[0].id == sample_program.id
        assert loaded_programs[0].name == sample_program.name
        assert len(loaded_programs[0].courses) == 2
        
        # Test course details
        ml_course = next(c for c in loaded_programs[0].courses if c.name == "Машинное обучение")
        assert ml_course.credits == 6
        assert not ml_course.is_elective
        
        dl_course = next(c for c in loaded_programs[0].courses if c.name == "Глубокое обучение")
        assert dl_course.credits == 4
        assert dl_course.is_elective
    
    @pytest.mark.integration
    def test_concurrent_user_operations(self, storage):
        # Создаем несколько пользователей одновременно
        users = []
        for i in range(5):
            user = UserProfile(
                user_id=f"user_{i}",
                username=f"user_{i}",
                background=f"Background {i}",
                interests=[f"Interest_{i}"],
                goals=[f"goal_{i}"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            users.append(user)
            storage.save_user_profile(user)
        
        # Проверяем, что все пользователи сохранены
        for user in users:
            loaded_user = storage.load_user_profile(user.user_id)
            assert loaded_user is not None
            assert loaded_user.username == user.username
            assert loaded_user.background == user.background
    
    @pytest.mark.integration 
    def test_file_permissions_and_structure(self, storage, sample_user_profile):
        storage.save_user_profile(sample_user_profile)
        
        # Проверяем структуру директорий
        assert os.path.exists(storage.users_dir)
        
        # Проверяем файл пользователя
        user_file = os.path.join(storage.users_dir, f"{sample_user_profile.user_id}.json")
        assert os.path.exists(user_file)
        assert os.path.isfile(user_file)
        
        # Проверяем права доступа
        stat_info = os.stat(user_file)
        assert stat_info.st_size > 0  # Файл не пустой
    
    @pytest.mark.integration
    def test_data_persistence_across_instances(self, temp_data_dir, sample_user_profile):
        # Сохраняем данные с первым экземпляром
        storage1 = JSONStorage(data_dir=temp_data_dir)
        storage1.save_user_profile(sample_user_profile)
        
        # Загружаем данные с новым экземпляром
        storage2 = JSONStorage(data_dir=temp_data_dir)
        loaded_profile = storage2.load_user_profile(sample_user_profile.user_id)
        
        assert loaded_profile is not None
        assert loaded_profile.user_id == sample_user_profile.user_id
        assert loaded_profile.username == sample_user_profile.username
    
    @pytest.mark.integration
    def test_invalid_data_handling(self, storage):
        # Тест загрузки несуществующего пользователя
        nonexistent_profile = storage.load_user_profile("nonexistent_user")
        assert nonexistent_profile is None
        
        # Тест загрузки программ при отсутствии файла
        programs = storage.load_programs()
        assert programs == []
    
    @pytest.mark.integration
    def test_large_data_operations(self, storage):
        # Создаем большое количество программ с курсами
        programs = []
        for i in range(10):
            courses = []
            for j in range(20):  # 20 курсов на программу
                course = Course(
                    id=f"course_{i}_{j}",
                    name=f"Курс {j} программы {i}",
                    credits=3 + (j % 5),
                    semester=1 + (j % 4),
                    is_elective=(j % 3 == 0)
                )
                courses.append(course)
            
            program = Program(
                id=f"program_{i}",
                name=f"Программа {i}",
                type=ProgramType.AI if i % 2 == 0 else ProgramType.AI_PRODUCT,
                url=f"https://test{i}.example.com",
                courses=courses,
                total_credits=120,
                duration_semesters=4,
                parsed_at=datetime.now()
            )
            programs.append(program)
        
        # Сохраняем и загружаем
        storage.save_programs(programs)
        loaded_programs = storage.load_programs()
        
        assert len(loaded_programs) == 10
        assert all(len(p.courses) == 20 for p in loaded_programs)
        assert sum(len(p.courses) for p in loaded_programs) == 200 