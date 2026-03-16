from typing import List, Optional

from pydantic import BaseModel


class Message(BaseModel):
    """
    Схема для входящего зашифрованного сообщения.

    :param to: Имя получателя.
    :param message: Сообщение в формате base64 (уже зашифровано на стороне клиента).
    """
    to: str
    message: str  # encrypted message in base64


class PublicKeyRequest(BaseModel):
    """
    Запрос на получение публичных ключей пользователей.

    :param usernames: Список имён пользователей, чьи ключи запрашиваются.
    """
    usernames: List[str]


class PublicKeyResponse(BaseModel):
    """
    Ответ с публичным ключом одного пользователя.

    :param username: Имя пользователя.
    :param publickey: Публичный ключ в формате PEM, закодированный в base64.
    """
    username: str
    publickey: str  # base64 encoded


class UserResponse(BaseModel):
    """
    Модель данных о пользователе в ответах API.

    :param username: Уникальное имя пользователя.
    :param alias: Отображаемое имя (псевдоним).
    :param id: UUID сессии; может быть None, если пользователь не активен.
    """
    username: str
    alias: str
    id: Optional[str] = None  # null if user is not active