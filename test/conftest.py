import threading
import time
import pytest
import uvicorn

from app.config.config import HOST, PORT
from app.fast_api_main import app


def run_server():
    """Запускает Uvicorn сервер."""
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


@pytest.fixture(scope="session")
def server():
    """Фикстура для запуска сервера в фоновом режиме перед тестами."""
    # Запуск сервера в отдельном потоке
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Ожидание, пока сервер запустится (простая задержка для надежности)
    time.sleep(2)

    yield  # Передача управления тестам

    # Сервер завершится автоматически благодаря daemon=True
