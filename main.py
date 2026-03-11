import uvicorn

from app.config.config import HOST, PORT
from app.fast_api_main import app

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)