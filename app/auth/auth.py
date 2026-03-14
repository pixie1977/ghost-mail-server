# app/auth/auth.py
import base64
import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.schemas import UserRegistration, UserLogin, User
from app.config.config import ACCESS_TOKEN_EXPIRE_MINUTES, DEBUG, JWT_TOKEN_SECRET_KEY, ALGORITHM
from app.messages.schemas import PublicKeyRequest, UserResponse, PublicKeyResponse
from app.utils.logging import Logger
from app.utils.security import Security
from app.utils.storage import Storage

router = APIRouter(prefix="/auth", tags=["auth"])

# Инициализация компонентов безопасности, хранилища и логирования
security = Security()
storage = Storage()
logger = Logger()

# Схема безопасности для JWT
security_scheme = HTTPBearer()


class RateLimiter:
    """Простой in-memory лимитер запросов по IP."""

    def __init__(self, max_requests: int, window: int = 60):
        self.max_requests = max_requests  # Максимальное количество запросов
        self.window = window  # Окно в секундах
        self.requests = {}  # ip -> список временных меток

    def is_allowed(self, ip: str) -> bool:
        now = datetime.now().timestamp()

        # Удаляем устаревшие запросы
        if ip in self.requests:
            self.requests[ip] = [t for t in self.requests[ip] if now - t < self.window]
        else:
            self.requests[ip] = []

        # Проверяем лимит
        if len(self.requests[ip]) >= self.max_requests:
            return False

        # Добавляем новый запрос
        self.requests[ip].append(now)
        return True


# Лимитеры
register_limiter = RateLimiter(max_requests=5)  # 5 запросов в минуту
login_limiter = RateLimiter(max_requests=10)  # 10 запросов в минуту


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """Зависимость для получения текущего аутентифицированного пользователя."""
    try:
        payload = security.decode_jwt_token(credentials.credentials, JWT_TOKEN_SECRET_KEY, ALGORITHM)
        username = payload.get("login")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = storage.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/get_server_key")
async def get_server_key():
    """Возвращает публичный ключ сервера."""
    logger.log_request("GET", "/get_server_key", "", 200)
    return {"public_key": security.get_self_public_key_pem()}


@router.post("/register")
async def register(
        user_data: UserRegistration,
        request: Request,
        security: Security = Depends(Security),
):
    """Регистрация нового пользователя."""
    client_ip = request.client.host

    # Проверка лимита запросов
    if not register_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for registration from {client_ip}")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")

    # Проверка существования пользователя
    if storage.user_exists(user_data.username):
        logger.warning(f"Registration failed: username {user_data.username} already exists")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    # Создание нового пользователя
    new_user = User(
        username=user_data.username,
        alias=user_data.alias,
        hashed_password=security.hash_password(user_data.password),
        role=user_data.role,
        public_key=user_data.public_key,
    )

    if storage.save_user(new_user):
        logger.info(f"User {user_data.username} registered successfully")
        return {"message": "User registered successfully"}
    else:
        logger.error(f"Failed to save user {user_data.username}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save user")


@router.get("/get_users")
async def get_users(
        current_user: UserResponse = Depends(get_current_user),
        request: Request = None,
):
    """Возвращает список зарегистрированных пользователей, зашифрованный открытым ключом текущего пользователя"""
    client_ip = request.client.host
    logger.log_request("GET", "/get_users", client_ip, 200)

    current_user_full = storage.get_user_by_username(current_user.username)

    users = storage.get_all_users()
    response_data = []
    for user in users:
        response_data.append(
            {
                "login": user.username,
                "alias": user.alias,
                "id": user.id,
                "public_key": user.public_key,
            }
        )

    # Шифруем данные с помощью RSA-OAEP
    try:
        encrypted_list_b64 = Security.encrypt_object_with_public(
            response_data,
            current_user_full.public_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")

    return encrypted_list_b64


@router.post("/get_publics")
async def get_public_keys(
        request_data: PublicKeyRequest,
        current_user: UserResponse = Depends(get_current_user),
        request: Request = None,
):
    """Retrieve public keys for requested users."""
    client_ip = request.client.host
    logger.log_request("POST", "/get_publics", client_ip, 200)

    current_user_full = storage.get_user_by_username(current_user.username)

    response = []
    for username in request_data.usernames:
        user = storage.get_user_by_username(username)
        if user and user.public_key:
            response.append({"username": user.username, "publickey": user.public_key})

    # Шифруем данные с помощью RSA-OAEP
    try:
        encrypted_list_b64 = Security.encrypt_object_with_public(
            response,
            current_user_full.public_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")

    return encrypted_list_b64


@router.post("/login")
async def login(user_data: UserLogin, request: Request):
    """Аутентификация пользователя и выдача JWT токена."""
    client_ip = request.client.host

    # Проверка лимита запросов
    if not login_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for login from {client_ip}")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")

    # Получение пользователя
    user = storage.get_user_by_username(user_data.username)
    if not user:
        logger.log_authentication(user_data.username, False, client_ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Проверка пароля
    if not security.verify_password(user_data.password, user.hashed_password):
        logger.log_authentication(user_data.username, False, client_ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Обновление времени последнего входа
    storage.update_user(
        username=user_data.username,
        last_login=datetime.now().isoformat(),
        is_active=True
    )

    if user_data.public_key:
        storage.update_user(
            username=user_data.username,
            public_key=user_data.public_key,
        )

    # Формирование полезной нагрузки токена
    expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    token_payload = {
        "sub": user.id,
        "alias": user.alias,
        "role": user.role,
    }

    if DEBUG:
        token_payload["login"] = user.username

    # Генерация JWT токена
    token = security.create_jwt_token(token_payload, JWT_TOKEN_SECRET_KEY, ALGORITHM, expires_in)

    logger.log_authentication(user_data.username, True, client_ip)
    logger.info(f"User {user_data.username} logged in successfully")

    return {"access_token": token, "token_type": "bearer"}
