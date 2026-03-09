from fastapi import FastAPI
from app.database import engine, Base
from app.routers import links, auth, redirect
from app.config import settings

app = FastAPI(title="API-сервис сокращения ссылок")

Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(links.router, prefix="/links", tags=["Links"])
app.include_router(redirect.router, prefix="", tags=["Redirect"])

@app.get("/")
async def root():
    return {"message": "API-сервис сокращения ссылок", "docs": "/docs"}