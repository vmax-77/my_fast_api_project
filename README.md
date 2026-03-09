# Проект Fast API

Сервис для сокращения ссылок с аналитикой и управлением.

## Возможности

- Создание коротких ссылок
- Кастомные алиасы
- Удаление/обновление ссылок (только для авторов)
- Статистика переходов
- Поиск по оригинальному URL
- Время жизни ссылки
- Кэширование популярных ссылок в Redis
- Очистка неиспользуемых ссылок
- История истекших ссылок

## Технологии

- FastAPI
- PostgreSQL
- Redis
- Docker

## Запуск

```bash
# Клонировать репозиторий
git clone <repository-url>
cd url-shortener

# Запустить с Docker Compose
docker-compose up --build

# Запустить локально (нужны PostgreSQL и Redis)
pip install -r requirements.txt
uvicorn app.main:app --reload

Сервис будет доступен по адресу: http://localhost:8000
Документация API: http://localhost:8000/docs


## Примеры запросов

### Создание ссылки
```bash
curl -X POST "http://localhost:8000/links/shorten" \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://example.com/very-long-url",
    "custom_alias": "myalias",
    "expires_at": "2024-12-31T23:59:59"
  }'
```

### Получение статистики
```bash
curl "http://localhost:8000/links/myalias/stats"
```

### Поиск по оригинальному URL
```bash
curl "http://localhost:8000/links/search?original_url=example.com"
```