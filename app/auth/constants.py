"""
Модуль инициализации глобальных компонентов безопасности, хранилища и логирования.
"""

from fastapi.security import HTTPBearer

from app.utils.logging import Logger
from app.utils.security import Security
from app.utils.storage import Storage


# Глобальные экземпляры
security_global = Security()
storage_global = Storage()
logger_global = Logger()

# Схема безопасности для JWT
security_scheme = HTTPBearer()


def get_security() -> Security:
    """Возвращает глобальный экземпляр Security."""
    return security_global


def get_security_scheme() -> HTTPBearer:
    """Возвращает схему безопасности JWT."""
    return security_scheme


def get_storage() -> Storage:
    """Возвращает глобальный экземпляр Storage."""
    return storage_global


def get_logger() -> Logger:
    """Возвращает глобальный экземпляр Logger."""
    return logger_global