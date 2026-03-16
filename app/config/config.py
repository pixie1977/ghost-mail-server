import os
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv


# Загружаем .env (если есть)
CURRENT_DIRECTORY = Path(__file__).parent.resolve()
load_dotenv()


def get_env_var(
    var_name: str,
    cast: Callable[[str], Any] = str,
    required: bool = True,
) -> Any:
    """
    Универсальная функция для получения переменных окружения.

    :param var_name: имя переменной окружения
    :param cast: функция для приведения типа (по умолчанию str)
    :param required: обязательно ли наличие переменной
    :return: значение переменной окружения, приведённое к нужному типу
    :raises Exception: если переменная не установлена или не может быть приведена к типу
    """
    value = os.getenv(var_name)
    if required and not value:
        raise Exception(f"{var_name} environment variable not set")
    if value is None:
        return None
    try:
        return cast(value)
    except (ValueError, TypeError) as exc:
        raise Exception(f"Cannot cast {var_name}={value} to {cast}") from exc


JWT_TOKEN_SECRET_KEY = get_env_var("JWT_TOKEN_SECRET_KEY")

ALGORITHM = get_env_var("ALGORITHM")

ACCESS_TOKEN_EXPIRE_MINUTES = get_env_var("ACCESS_TOKEN_EXPIRE_MINUTES", cast=int)

DEBUG = get_env_var("DEBUG", cast=lambda v: v.lower() == "true")

HOST = get_env_var("HOST")

PORT = get_env_var("PORT", cast=int)