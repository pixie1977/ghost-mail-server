from threading import Thread
from typing import List, Tuple

import traceback

from app.client.test_client import GhostMailClient


class EchoUser(Thread):
    """Поток для автоматического ответа на входящие сообщения через GhostMailClient."""

    def __init__(self) -> None:
        super().__init__()
        self.client = GhostMailClient()
        self.login = "echo_user"
        self.alias = "echo_user_alias"
        self.password = "echo_password"
        self.daemon = True  # Автоматическое завершение потока при выходе

    def run(self) -> None:
        """Основной цикл работы: регистрация, вход, чтение и ответ на сообщения."""
        while True:
            try:
                # Регистрация (если ещё не зарегистрирован)
                try:
                    self.client.register(
                        username=self.login,
                        password=self.password,
                        alias=self.alias,
                    )
                except Exception as e1:
                    print(f"Регистрация не удалась: {e1}")

                # Вход в систему
                data, status_code = self.client.login(
                    username=self.login,
                    password=self.password,
                )

                if status_code == 200:
                    # Основной цикл обработки сообщений
                    while True:
                        messages, status_code = self.client.get_received_messages()
                        if status_code == 200 and messages:
                            for message in messages:
                                from_login: str = message["from"]
                                text: str = message["message"]

                                # Получаем публичный ключ отправителя
                                id_list: List[str] = [from_login]
                                from_public_keys: List[Tuple[dict]] = self.client.get_publics(id_list)

                                # Извлекаем публичный ключ — костыль из-за странного формата
                                # TODO: разобраться, почему get_publics возвращает [(publickey_dict,), ...]
                                from_public_key: str = from_public_keys[0][0].get("publickey", "")
                                if not from_public_key:
                                    print(f"Не удалось получить publickey для {from_login}")
                                    continue

                                # Отправляем ECHO-ответ
                                self.client.send_message(
                                    recipient=from_login,
                                    content=f"ECHO: {text}",
                                    recipient_public_key_pem=from_public_key,
                                )
                else:
                    raise Exception("Login failed")

            except Exception as e:
                print(f"Неожиданная ошибка в EchoUser: {e}")
                traceback.print_exc()