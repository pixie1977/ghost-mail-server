import uvicorn

from app.config.config import HOST, PORT
from app.fast_api_main import app


def run_server() -> None:
    """
    Запускает Uvicorn-сервер с параметрами из конфигурации.

    Использует хост и порт из config.py.
    """
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    run_server()