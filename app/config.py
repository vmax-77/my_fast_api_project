from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@db:5432/urlshortener"
    REDIS_URL: str = "redis://redis:6379"
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    BASE_URL: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"

settings = Settings()