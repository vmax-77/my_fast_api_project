import os
import sys

# ЭТО ДОЛЖНО БЫТЬ САМЫМ ПЕРВЫМ - ПЕРЕД ЛЮБЫМИ ИМПОРТАМИ
os.environ["PYTEST_RUNNING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["BASE_URL"] = "http://localhost:8000"
os.environ["PASSLIB_BCRYPT_AVOID_WRAP_BUG"] = "1"

# Заглушка для Redis
class DummyRedis:
    def get(self, key):
        return None
    def setex(self, key, time, value):
        return None
    def delete(self, key):
        return None
    def flushall(self):
        return None

# Подмена redis_client ДО импорта app.main
sys.modules['app.redis_client'] = type('module', (), {'redis_client': DummyRedis()})()

# ТЕПЕРЬ импортируем
from app.main import app
from app.database import Base, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import pytest

TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture
def db_session(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def auth_token(client):
    # Регистрируем тестового пользователя
    client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    })
    response = client.post("/auth/token", data={
        "username": "testuser",
        "password": "testpass123"
    })
    return response.json()["access_token"]