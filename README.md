# Проект Fast API

Сервис, который позволяет пользователям сокращать длинные ссылки, получать их аналитику и управлять ими
(Проект является учебным и выполнен в рамках задания магистратуры)

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
```


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

## Аутентификация

### Регистрация
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "username",
    "password": "password123"
  }'
  ```

### Получение токена
  ```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=username&password=password123"
  ```


### Создание ссылки (с авторизацией)
```bash
curl -X POST "http://localhost:8000/links/shorten" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "original_url": "https://example.com",
    "custom_alias": "myalias"
  }'
  ```

  ## База данных

### Таблица users
- id (PRIMARY KEY)
- email (UNIQUE)
- username (UNIQUE)
- hashed_password
- is_active
- created_at

### Таблица links
- id (PRIMARY KEY)
- original_url
- short_code (UNIQUE)
- custom_alias (UNIQUE, NULLABLE)
- clicks
- created_at
- expires_at (NULLABLE)
- last_accessed (NULLABLE)
- is_active
- user_id (FOREIGN KEY REFERENCES users.id)