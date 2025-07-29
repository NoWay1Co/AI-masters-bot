# AI Masters Bot - Чат-бот для ИТМО Магистратура

Телеграм-бот для помощи абитуриентам в выборе магистерских программ ИТМО.

## Требования

- Python 3.11+
- Telegram Bot Token
- Ollama

## Установка

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
```
TELEGRAM_TOKEN=your_telegram_bot_token_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
DATA_DIR=data
LOG_LEVEL=INFO
```

## Запуск

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
└── requirements.txt    # Зависимости
```

## Тестирование

```bash
pytest
```
