import json
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import Program, UserProfile, UserSession
from ..utils.config import settings
from ..utils.logger import logger

class JSONStorage:
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self.static_dir = self.data_dir / "static"
        self.users_dir = self.data_dir / "users"
        self._ensure_directories()
    
    def _ensure_directories(self):
        self.static_dir.mkdir(parents=True, exist_ok=True)
        self.users_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_programs(self, programs: List[Program]) -> None:
        programs_data = [program.model_dump() for program in programs]
        file_path = self.static_dir / "programs.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(programs_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info("Programs saved", count=len(programs), file=str(file_path))
    
    async def load_programs(self) -> List[Program]:
        file_path = self.static_dir / "programs.json"
        
        if not file_path.exists():
            logger.warning("Programs file not found", file=str(file_path))
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        programs = [Program(**item) for item in data]
        logger.info("Programs loaded", count=len(programs))
        return programs
    
    async def save_user_profile(self, profile: UserProfile) -> None:
        file_path = self.users_dir / f"{profile.user_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(profile.model_dump(), f, ensure_ascii=False, indent=2, default=str)
        
        logger.info("User profile saved", user_id=profile.user_id)
    
    async def load_user_profile(self, user_id: str) -> Optional[UserProfile]:
        file_path = self.users_dir / f"{user_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return UserProfile(**data)

storage = JSONStorage() 