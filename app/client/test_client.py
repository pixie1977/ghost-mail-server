import base64
import json
from typing import Dict, List, Tuple

import requests

from app.utils.security import Security


class GhostMailClient:
    """Клиент для взаимодействия с GhostMail API с шифрованием на стороне клиента."""

    base_url = "http://localhost:8000"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.token: str | None = None
        self.security = Security()

    def _get_headers(self) -> Dict[str, str]:
        """Возвращает заголовки для HTTP-запросов."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def set_token(self, token: str) -> None:
        """Устанавливает токен авторизации."""
        self.token = token

    def register(
        self, username: str, password: str, alias: str
    ) -> Tuple[dict, int]:
        """Регистрация пользователя с шифрованием данных на стороне клиента."""
        url = f"{self.base_url}/auth/register_s"
        data = {
            "username": username,
            "password": password,
            "alias": alias,
            "role": "user",
            "public_key": self.security.get_self_public_key_pem(),
        }
        server_public_key = self.get_server_public_key()
        data_enc_str = self.security.encrypt_object_with_public(
            data, server_public_key
        )
        data_enc = {"txt": data_enc_str}
        response = self.session.post(
            url, json=data_enc, headers=self._get_headers()
        )
        return response.json(), response.status_code

    def login(self, username: str, password: str) -> Tuple[dict, int]:
        """Вход пользователя; сохраняет токен при успешной аутентификации."""
        url = f"{self.base_url}/auth/login_s"
        data = {
            "username": username,
            "password": password,
            "public_key": self.security.get_self_public_key_pem(),
        }
        server_public_key = self.get_server_public_key()
        data_enc_str = self.security.encrypt_object_with_public(
            data, server_public_key
        )
        data_enc = {"txt": data_enc_str}
        response = self.session.post(
            url, json=data_enc, headers=self._get_headers()
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        return response.json(), response.status_code

    def send_message(
        self, recipient: str, content: str, recipient_public_key_pem: str
    ) -> Tuple[dict, int]:
        """Отправка зашифрованного сообщения получателю."""
        cyphered_text = Security.encrypt_text_with_public(
            plaintext=content.encode("utf-8"),
            public_key_pem=recipient_public_key_pem,
        )
        base64_cyphered_str = base64.b64encode(cyphered_text).decode("utf-8")
        url = f"{self.base_url}/messages/send_message"
        data = {"to": recipient, "message": base64_cyphered_str}
        response = self.session.post(
            url, json=data, headers=self._get_headers()
        )
        return response.json(), response.status_code

    def get_server_public_key(self) -> str:
        """Получение публичного ключа сервера."""
        url = f"{self.base_url}/auth/get_server_key"
        response = self.session.get(url, headers=self._get_headers())
        if response.status_code == 200:
            return response.json().get("public_key")
        else:
            raise Exception(
                f"Failed to fetch server public key: {response.status_code} - {response.text}"
            )

    def get_received_messages(self) -> Tuple[List[Dict], int]:
        """Получение и расшифровка входящих сообщений."""
        url = f"{self.base_url}/messages/long_polling"
        response = self.session.get(url, headers=self._get_headers())
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch messages: {response.status_code} - {response.text}"
            )
        received_data = response.json()
        messages = received_data.get("messages")
        if not messages:
            return [], response.status_code
        mapped_response = [
            self._map_message(message) for message in messages
        ]
        return mapped_response, response.status_code

    def get_users(self) -> Tuple[Dict | List, int]:
        """Получение списка пользователей (расшифровка ответа клиентом)."""
        url = f"{self.base_url}/auth/get_users"
        response = self.session.get(url, headers=self._get_headers())
        decrypted_data = Security.decrypt_object_with_private(
            encrypted_blocks_json=response.json(),
            private_key=self.security.private_key,
        )
        if isinstance(decrypted_data, str):
            return json.loads(decrypted_data), response.status_code
        return decrypted_data, response.status_code

    def get_publics(self, id_list: List[str]) -> Tuple[List[Dict], int]:
        """Получение публичных ключей по списку имён пользователей."""
        id_list = id_list or []
        url = f"{self.base_url}/auth/get_publics"
        body = {"usernames": id_list}
        response = self.session.post(
            url, headers=self._get_headers(), json=body
        )
        decrypted_data = Security.decrypt_object_with_private(
            encrypted_blocks_json=response.json(),
            private_key=self.security.private_key,
        )
        if isinstance(decrypted_data, str):
            json_data = json.loads(decrypted_data)
        else:
            json_data = decrypted_data
        return json_data, response.status_code

    def long_polling(self) -> Tuple[dict, int]:
        """Long-polling запрос для получения новых сообщений."""
        url = f"{self.base_url}/messages/long_polling"
        response = self.session.get(
            url, headers=self._get_headers(), timeout=30
        )
        return response.json(), response.status_code

    def get_sent_messages(self) -> Tuple[dict, int]:
        """Получение отправленных сообщений."""
        url = f"{self.base_url}/messages/sent"
        response = self.session.get(url, headers=self._get_headers())
        return response.json(), response.status_code

    def _map_message(self, message: Dict) -> Dict:
        """Расшифровка одного сообщения."""
        msg_from = message.get("from")
        content = message.get("message")
        decoded_content = base64.b64decode(content)
        plain_text = Security.decrypt_with_private(
            encrypted_message=decoded_content,
            private_key=self.security.private_key,
        ).decode("utf-8")
        return {"from": msg_from, "message": plain_text}