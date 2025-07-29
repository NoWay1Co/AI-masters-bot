# Docker Quick Start

Быстрый запуск AI Masters Bot через Docker Compose.

## Предварительные требования

- Docker
- Docker Compose
- Telegram Bot Token

## Быстрый старт

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd AI-masters-bot
```

2. **Настройте переменные окружения:**
```bash
cp env.example .env
# Отредактируйте .env и добавьте ваш TELEGRAM_TOKEN
```

3. **Запустите сервисы:**
```bash
docker-compose up -d
```

4. **Скачайте LLM модель (при первом запуске):**
```bash
docker exec ai-masters-ollama ollama pull llama3
```

5. **Проверьте статус:**
```bash
docker-compose ps
docker-compose logs -f ai-masters-bot
```

## Управление

- **Остановка:** `docker-compose down`
- **Перезапуск:** `docker-compose restart`
- **Логи:** `docker-compose logs -f`
- **Обновление:** `docker-compose down && docker-compose build --no-cache && docker-compose up -d`

## Файловая структура Docker

- `docker-compose.yml` - основной файл конфигурации
- `Dockerfile` - образ Python приложения  
- `.dockerignore` - исключения для Docker build
- `.env` - переменные окружения (создается из env.example)

## Порты и сервисы

- **Ollama:** порт 11434 (внутренний LLM API)
- **Bot:** без внешних портов (работает через Telegram API)
- **Volumes:** `./data` для данных, `./logs` для логов

Готово! Бот должен быть доступен в Telegram. 