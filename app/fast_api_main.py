from fastapi import FastAPI

from app.auth.auth import router as auth_router
from app.messages.messages import router as messages_router
from app.utils.logging import Logger

# Задаем логгер для модуля main
logger = Logger()

app = FastAPI(title="Ghost Mail Server", description="Secure and fully anonymous messaging server")

app.include_router(auth_router, tags=["auth"])
app.include_router(messages_router, tags=["messages"])


@app.get("/")
def read_root():
    """корневой эндпоинт"""
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Ghost Mail Server"}


@app.on_event("startup")
async def startup_event():
    """Запуск сервера"""
    logger.info("Ghost Mail Server starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Остановка сервер"""
    logger.info("Ghost Mail Server shutting down...")

