import asyncio
import base64
import json
import threading
import datetime
import uuid  # Импортируем модуль uuid для генерации уникальных идентификаторов

from fastapi import APIRouter, HTTPException, Depends, Request, status
from typing import List

from app.auth.auth import get_current_user, storage, logger
from app.messages.schemas import Message, PublicKeyRequest, PublicKeyResponse, UserResponse
from app.utils.logging import Logger
from app.utils.security import Security

# Задаем логгер для модуля message
logger = Logger()

router = APIRouter(prefix="/messages", tags=["messages"])

messages_queue = []
queue_lock = threading.Lock()


@router.get("/long_polling")
async def long_polling(
    current_user: UserResponse = Depends(get_current_user),
    request: Request = None,
    timeout: int = 30  # Клиент может указать время ожидания (по умолчанию — 30 секунд)
):
    """
    Асинхронный long polling. Ожидает новые сообщения в течение `timeout` секунд.
    Если сообщений нет — возвращает пустой ответ.
    """
    client_ip = request.client.host
    logger.log_request("GET", "/long_polling", client_ip, 200)

    # Асинхронное ожидание появления сообщений
    start_time = asyncio.get_event_loop().time()

    while asyncio.get_event_loop().time() - start_time < timeout:
        await asyncio.sleep(0.5)  # Неблокирующая проверка каждые 500 мс

        with queue_lock:  # Используем синхронный лок, так как queue — общий список
            user_messages = [msg for msg in messages_queue if msg["to"] == current_user.username]

        if user_messages:
            with queue_lock:
                # Удаляем сообщения из очереди
                messages_queue[:] = [msg for msg in messages_queue if msg["to"] != current_user.username]
            return {"status": "OK", "messages": user_messages}

    # Если таймаут истёк и сообщений нет
    return {"status": "no new messages"}


@router.post("/send_message")
async def send_message(
    message_data: Message,
    current_user: UserResponse = Depends(get_current_user),
    request: Request = None,
):
    """Отправка шифрованного сообщения пользователю"""
    client_ip = request.client.host
    logger.log_request("POST", "/send_message", client_ip, 200)

    recipient = storage.get_user_by_username(message_data.to)
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found",
        )

    # Генерируем уникальный ID для сообщения
    message_id = str(uuid.uuid4())

    # Сохраняем сообщение в очередь для отправки
    with queue_lock:
        messages_queue.append(
            {
                "to": message_data.to,
                "from": current_user.username,
                "message": message_data.message,
                "timestamp": datetime.datetime.now().isoformat(),
                "id": message_id
            }
        )

    logger.info(f"Message sent from {current_user.username} to {message_data.to}")
    return {"message": "Message sent successfully", "message_id": message_id}