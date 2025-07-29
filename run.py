#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Добавляем путь к модулям
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 