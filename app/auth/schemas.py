from typing import Optional

from pydantic import BaseModel, Field


class UserRegistration(BaseModel):
    """Схема данных для регистрации пользователя."""
    username: str = Field(..., min_length=3)
    alias: str = Field(..., min_length=1)
    password: str = Field(..., min_length=6)
    role: str = Field(...)
    public_key: str = Field(...)  # RSA public key


class UserLogin(BaseModel):
    """Схема данных для входа пользователя."""
    username: str = Field(...)
    password: str = Field(...)
    public_key: Optional[str] = None  # RSA public key


class User(BaseModel):
    """Полная модель пользователя в системе."""
    username: str
    alias: str
    hashed_password: str  # base64 encoded
    role: str  # base64 encoded
    id: Optional[str] = None  # session UUID
    public_key: str  # RSA public key, base64 encoded
    last_login: Optional[str] = None