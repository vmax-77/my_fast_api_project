## Запуск тестов

### Установка зависимостей
```bash
pip install pytest pytest-cov
```

### Запуск тестов с покрытием
```bash
pytest tests/ -v --cov=app --cov-report=term --cov-report=html
```