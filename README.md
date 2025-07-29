# AI Masters Bot - Чат-бот для ИТМО Магистратура

Телеграм-бот для помощи абитуриентам в выборе магистерских программ ИТМО.

Данный бот будет какое-то время развернут локально на моем железе, чтобы вы могли его протестировать.
Найти бота можно по тегу @siiikehelperbot


## Требования


### Docker запуск:
- Docker
- Docker Compose
- Telegram Bot Token

## Установка и запуск

### Запуск через Docker (рекомендуется)

> 📋 **Быстрый старт:** См. [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) для краткого руководства

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd AI-masters-bot
```

2. Создайте `.env` файл:
```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
OLLAMA_MODEL=llama3
LOG_LEVEL=INFO
```

3. Запустите через Docker Compose:
```bash
docker-compose up -d
```

4. Скачайте модель для Ollama (при первом запуске):
```bash
docker exec ai-masters-ollama ollama pull llama3
```

5. Проверьте логи:
```bash
docker-compose logs -f ai-masters-bot
```

### Локальный запуск

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd AI-masters-bot
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Заполните переменные окружения в `.env`:
```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
DATA_DIR=data
LOG_LEVEL=INFO
```

5. Запустите Ollama отдельно и скачайте модель:
```bash
ollama serve
ollama pull llama3
```

6. Запустите бота:
```bash
python run.py
```

## Структура проекта

```
ai_masters_bot/
├── src/                 # Исходный код
│   ├── bot/            # Telegram бот
│   ├── services/       # Бизнес логика
│   ├── data/           # Модели данных
│   └── utils/          # Утилиты
├── data/               # Данные приложения
├── tests/              # Тесты
├── docker-compose.yml  # Docker Compose конфигурация
├── Dockerfile          # Образ Python приложения
├── .dockerignore       # Исключения Docker
├── env.example         # Пример переменных окружения
├── requirements.txt    # Зависимости Python
└── DOCKER_QUICKSTART.md # Быстрый старт с Docker
```

## Тестирование

```bash
pytest
```
