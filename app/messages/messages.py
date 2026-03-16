import asyncio
import base64
import datetime
import json
import threading
import uuid
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Request, status

from app.auth.auth import get_current_user
from app.auth.constants import get_storage
from app.messages.schemas import Message, PublicKeyRequest, PublicKeyResponse, UserResponse
from app.utils.logging import Logger
from app.utils.security import Security
from app.utils.storage import Storage

# Инициализация логгера и глобальной очереди сообщений
logger = Logger()
messages_queue: List[dict] = []
queue_lock = threading.Lock()

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/long_polling")
async def long_polling(
    current_user: UserResponse = Depends(get_current_user),
    request: Request = None,
    timeout: int = 30,
) -> dict:
    """
    Асинхронный endpoint для long polling.

    Клиент ожидает новые сообщения в течение указанного времени (`timeout`).
    Как только появляются сообщения для пользователя — они возвращаются.
    При истечении таймаута возвращается пустой ответ.

    :param current_user: Текущий аутентифицированный пользователь (из JWT).
    :param request: Объект запроса (для логирования IP).
    :param timeout: Время ожидания новых сообщений в секундах (по умолчанию — 30).
    :return: Словарь с результатом: сообщения или статус отсутствия новых данных.
    """
    client_ip = request.client.host
    logger.log_request("GET", "/long_polling", client_ip, 200)

    start_time = asyncio.get_event_loop().time()

    while (asyncio.get_event_loop().time() - start_time) < timeout:
        await asyncio.sleep(0.5)  # Проверка каждые 500 мс без блокировки

        with queue_lock:
            user_messages = [
                msg for msg in messages_queue if msg["to"] == current_user.username
            ]

        if user_messages:
            with queue_lock:
                # Удаляем доставленные сообщения
                messages_queue[:] = [
                    msg for msg in messages_queue if msg["to"] != current_user.username
                ]

            return {"status": "OK", "messages": user_messages}

    return {"status": "no new messages"}


@router.post("/send_message")
async def send_message(
    message_data: Message,
    current_user: UserResponse = Depends(get_current_user),
    storage: Storage = Depends(get_storage),
    request: Request = None,
) -> dict:
    """
    Отправка зашифрованного сообщения другому пользователю.

    Принимает уже зашифрованное сообщение от клиента, проверяет получателя,
    добавляет метаданные (ID, временная метка) и помещает в очередь доставки.

    :param message_data: Данные сообщения (получатель, зашифрованное содержимое).
    :param current_user: Отправитель (определяется по токену).
    :param storage: Хранилище пользователей (DI через Depends).
    :param request: Объект запроса (для логирования).
    :return: Подтверждение отправки и ID сообщения.
    :raises HTTPException: Если получатель не найден.
    """
    client_ip = request.client.host
    logger.log_request("POST", "/send_message", client_ip, 200)

    recipient = storage.get_user_by_username(message_data.to)
    if not recipient:
        logger.warning(f"Failed to send message: recipient '{message_data.to}' not found (from {current_user.username})")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found",
        )

    message_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    message_entry = {
        "to": message_data.to,
        "from": current_user.username,
        "message": message_data.message,
        "timestamp": timestamp,
        "id": message_id,
    }

    with queue_lock:
        messages_queue.append(message_entry)

    logger.info(f"Message sent from {current_user.username} to {message_data.to} [ID: {message_id}]")
    return {"message": "Message sent successfully", "message_id": message_id}