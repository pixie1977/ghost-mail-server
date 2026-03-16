from fastapi import FastAPI

from app.auth.auth import router as auth_router
from app.client.echo_user import EchoUser
from app.config.config import DEBUG
from app.messages.messages import router as messages_router
from app.utils.logging import Logger


# Инициализация логгера и приложения
logger = Logger()
app = FastAPI(title="Ghost Mail Server", description="Secure and fully anonymous messaging server")


@app.get("/")
def read_root() -> dict:
    """
    Корневой эндпоинт.

    :return: Приветственное сообщение.
    """
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Ghost Mail Server"}


# Подключение роутеров
app.include_router(auth_router, tags=["auth"])
app.include_router(messages_router, tags=["messages"])


@app.on_event("startup")
async def startup_event() -> None:
    """
    Действия при запуске сервера.

    В режиме отладки запускается тестовый пользователь (EchoUser).
    """
    logger.info("Ghost Mail Server starting up...")
    if DEBUG:
        echo_user = EchoUser()
        echo_user.start()
        logger.info("EchoUser started for testing")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Действия при остановке сервера.
    """
    logger.info("Ghost Mail Server shutting down...")


__all__ = ["app"]