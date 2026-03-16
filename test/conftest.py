import threading
import time
import pytest
import uvicorn

from app.config.config import HOST, PORT
from app.fast_api_main import app


def run_server() -> None:
    """
    Запускает Uvicorn-сервер.

    Сервер запускается с указанными хостом и портом, уровень логирования — info.
    """
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


@pytest.fixture(scope="session")
def server():
    """
    Фикстура для запуска сервера в фоновом режиме перед выполнением тестов.

    Запускает сервер в отдельном потоке с флагом daemon=True.
    Добавлена задержка на 2 секунды для стабильного старта сервера.

    :yield: Управление передаётся тестам после старта сервера.
    """
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Ожидание запуска сервера
    time.sleep(2)

    yield

    # Сервер завершается автоматически (daemon=True)