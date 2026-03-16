from datetime import datetime
from typing import Dict, Any

from fastapi import HTTPException
from starlette import status

from app.auth.schemas import UserRegistration, User, UserLogin
from app.config.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_TOKEN_SECRET_KEY, ALGORITHM
from app.utils.logging import Logger
from app.utils.security import Security
from app.utils.storage import Storage


def register_handler(
    logger: Logger,
    user_data: UserRegistration,
    security: Security,
    storage: Storage,
) -> Dict[str, str]:
    """
    Обработчик регистрации пользователя.
    Проверяет наличие пользователя, хэширует пароль и сохраняет в хранилище.
    """
    if storage.user_exists(user_data.username):
        logger.warning(f"Registration failed: username {user_data.username} already exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save user"
        )


def login_handler(
    client_ip: str,
    user_data: UserLogin,
    logger: Logger,
    security: Security,
    storage: Storage,
) -> Dict[str, Any]:
    """
    Обработчик входа пользователя.
    Проверяет учетные данные, обновляет данные входа и выдает JWT-токен.
    """
    user = storage.get_user_by_username(user_data.username)
    if not user:
        logger.log_authentication(user_data.username, False, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not security.verify_password(user_data.password, user.hashed_password):
        logger.log_authentication(user_data.username, False, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Обновление времени последнего входа
    storage.update_user(
        username=user_data.username,
        last_login=datetime.now().isoformat(),
        is_active=True
    )

    if user_data.public_key:
        storage.update_user(
            username=user_data.username,
            public_key=user_data.public_key
        )

    # Формирование полезной нагрузки токена
    expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    token_payload = {
        "login": user_data.username,
        "sub": user.id,
        "alias": user.alias,
        "role": user.role,
    }

    # Генерация JWT токена
    token = security.create_jwt_token(
        token_payload, JWT_TOKEN_SECRET_KEY, ALGORITHM, expires_in
    )

    logger.log_authentication(user_data.username, True, client_ip)
    logger.info(f"User {user_data.username} logged in successfully")

    return {"access_token": token, "token_type": "bearer"}


def decrypt_user_login(user_data_enc: str, _security: Security) -> UserLogin:
    """Расшифровывает зашифрованные данные входа."""
    decrypted_obj = _security.decrypt_object_with_private(user_data_enc, _security.private_key)
    return UserLogin(
        username=decrypted_obj.get("username"),
        password=decrypted_obj.get("password"),
        public_key=decrypted_obj.get("public_key"),
    )


def decrypt_user_registration(user_data_enc: str, _security: Security) -> UserRegistration:
    """Расшифровывает зашифрованные данные регистрации."""
    decrypted_obj = _security.decrypt_object_with_private(user_data_enc, _security.private_key)
    return UserRegistration(
        username=decrypted_obj.get("username"),
        alias=decrypted_obj.get("alias"),
        password=decrypted_obj.get("password"),
        role=decrypted_obj.get("role"),
        public_key=decrypted_obj.get("public_key"),
    )