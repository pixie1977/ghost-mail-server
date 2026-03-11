from typing import List, Optional

from pydantic import BaseModel


class Message(BaseModel):
    to: str
    message: str  # encrypted message in base64


class PublicKeyRequest(BaseModel):
    usernames: List[str]


class PublicKeyResponse(BaseModel):
    username: str
    publickey: str  # base64 encoded


class UserResponse(BaseModel):
    username: str
    alias: str
    id: Optional[str] = None  # null if user is not active