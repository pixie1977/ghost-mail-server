# app/auth/auth.py
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.constants import (
    get_security_scheme,
    get_security,
    get_storage,
    get_logger,
    security_scheme,
)
from app.auth.handlers import (
    decrypt_user_login,
    login_handler,
    register_handler,
    decrypt_user_registration,
)
from app.auth.schemas import UserRegistration, UserLogin
from app.config.config import JWT_TOKEN_SECRET_KEY, ALGORITHM
from app.messages.schemas import PublicKeyRequest
from app.utils.logging import Logger
from app.utils.security import Security
from app.utils.storage import Storage

router = APIRouter(prefix="/auth", tags=["auth"])


class RateLimiter:
    """Простой in-memory лимитер запросов по IP."""

    def __init__(self, max_requests: int, window: int = 60) -> None:
        self.max_requests = max_requests  # Максимальное количество запросов
        self.window = window  # Окно в секундах
        self.requests: Dict[str, list] = {}  # ip -> список временных меток

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


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    security: Security = Depends(security_scheme),
    storage: Storage = Depends(get_storage),
) -> Any:
    """Зависимость для получения текущего аутентифицированного пользователя."""
    try:
        payload = security.decode_jwt_token(
            credentials.credentials, JWT_TOKEN_SECRET_KEY, ALGORITHM
        )
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
async def get_server_key(
    security: Security = Depends(get_security),
    logger: Logger = Depends(get_logger),
) -> Dict[str, str]:
    """Возвращает публичный ключ сервера."""
    logger.log_request("GET", "/get_server_key", "", 200)
    return {"public_key": security.get_self_public_key_pem()}


@router.post("/login_s")
async def login_s(
    user_data_enc: Dict[str, str],
    request: Request,
    security: Security = Depends(get_security),
    storage: Storage = Depends(get_storage),
    logger: Logger = Depends(get_logger),
) -> Any:
    """Аутентификация пользователя и выдача JWT токена."""
    client_ip = request.client.host

    # Проверка лимита запросов (чтобы при DDoS не нагружать криптографией)
    if not login_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for login from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
        )

    user_data_enc_str = user_data_enc.get("txt")
    user_data = decrypt_user_login(user_data_enc_str, security)

    return login_handler(
        user_data=user_data,
        client_ip=client_ip,
        logger=logger,
        security=security,
        storage=storage,
    )


@router.post("/login")
async def login(
    user_data: UserLogin,
    request: Request,
    logger: Logger = Depends(get_logger),
) -> Any:
    """Аутентификация пользователя и выдача JWT токена."""
    client_ip = request.client.host

    # Проверка лимита запросов
    if not login_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for login from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
        )

    return login_handler(user_data=user_data, client_ip=client_ip)


@router.post("/register_s")
async def register_s(
    user_data_enc: Dict[str, str],
    request: Request,
    logger: Logger = Depends(get_logger),
    security: Security = Depends(get_security),
    storage: Storage = Depends(get_storage),
) -> Any:
    """Регистрация нового пользователя."""
    client_ip = request.client.host

    # Проверка лимита запросов
    if not register_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for registration from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
        )

    user_data_enc_str = user_data_enc.get("txt")
    user_data = decrypt_user_registration(user_data_enc_str, security)

    return register_handler(
        user_data=user_data,
        logger=logger,
        security=security,
        storage=storage,
    )


@router.post("/register")
async def register(
    user_data: UserRegistration,
    request: Request,
    security: Security = Depends(get_security),
    storage: Storage = Depends(get_storage),
    logger: Logger = Depends(get_logger),
) -> Any:
    """Регистрация нового пользователя."""
    client_ip = request.client.host

    # Проверка лимита запросов
    if not register_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for registration from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
        )

    return register_handler(
        user_data=user_data,
        logger=logger,
        security=security,
        storage=storage,
    )


@router.get("/get_users")
async def get_users(
    request: Request,
    current_user: Any = Depends(get_current_user),
    logger: Logger = Depends(get_logger),
    storage: Storage = Depends(get_storage),
) -> str:
    """Возвращает список пользователей, зашифрованный открытым ключом текущего пользователя."""
    client_ip = request.client.host
    logger.log_request("GET", "/get_users", client_ip, 200)

    current_user_full = storage.get_user_by_username(current_user.username)
    users = storage.get_all_users()
    response_data = [
        {
            "login": user.username,
            "alias": user.alias,
            "id": user.id,
            "public_key": user.public_key,
        }
        for user in users
    ]

    # Шифруем данные с помощью RSA-OAEP
    try:
        encrypted_list_b64 = Security.encrypt_object_with_public(
            response_data, current_user_full.public_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")

    return encrypted_list_b64


@router.post("/get_publics")
async def get_public_keys(
    request_data: PublicKeyRequest,
    request: Request,
    current_user: Any = Depends(get_current_user),
    logger: Logger = Depends(get_logger),
    storage: Storage = Depends(get_storage),
) -> str:
    """Возвращает открытые ключи запрошенных пользователей."""
    client_ip = request.client.host
    logger.log_request("POST", "/get_publics", client_ip, 200)

    current_user_full = storage.get_user_by_username(current_user.username)
    response = [
        {"username": user.username, "publickey": user.public_key}
        for username in request_data.usernames
        if (user := storage.get_user_by_username(username)) and user.public_key
    ]

    # Шифруем данные с помощью RSA-OAEP
    try:
        encrypted_list_b64 = Security.encrypt_object_with_public(
            response, current_user_full.public_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")

    return encrypted_list_b64