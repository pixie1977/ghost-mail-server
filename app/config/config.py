# Определяем текущую директорию
import os
from pathlib import Path
from dotenv import load_dotenv


# Загружаем .env (если есть)
CURRENT_DIRECTORY = Path(__file__).parent.resolve()
load_dotenv()


def get_env_var(var_name: str, cast=str, required=True):
    """Универсальная функция для получения переменных окружения."""
    value = os.getenv(var_name)
    if required and not value:
        raise Exception(f"{var_name} environment variable not set")
    try:
        return cast(value)
    except (ValueError, TypeError) as exc:
        raise Exception(f"Cannot cast {var_name}={value} to {cast}") from exc


JWT_TOKEN_SECRET_KEY = get_env_var("JWT_TOKEN_SECRET_KEY")

ALGORITHM = get_env_var("ALGORITHM")

ACCESS_TOKEN_EXPIRE_MINUTES = get_env_var(
    "ACCESS_TOKEN_EXPIRE_MINUTES", cast=int
)

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

HOST = get_env_var("HOST")  # Обычно HOST — строка (например, "127.0.0.1")
PORT = get_env_var("PORT", cast=int)