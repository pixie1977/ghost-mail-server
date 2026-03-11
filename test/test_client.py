import base64
import json

import requests
from cryptography.hazmat.primitives import serialization

from app.utils.security import Security


class GhostMailClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.private_key = None
        self.public_key = None
        self.server_pubkey = self.get_server_public_key()  # Получаем публичный ключ сервера при инициализации
        self._generate_rsa_keys()

    def _generate_rsa_keys(self):
        """Генерирует RSA-ключевую пару (4096 бит)"""
        security = Security()
        security.generate_rsa_keys()
        self.private_key = security.private_key
        self.public_key = security.public_key

    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def register(self, username: str, password: str, alias: str):
        url = f"{self.base_url}/auth/register"
        data = {
            "username": username,
            "password": password,
            "alias": alias,
            "role": "user",
            "public_key": Security.get_public_key_pem(self.public_key),
        }
        response = self.session.post(url, json=data, headers=self._get_headers())
        return response.json(), response.status_code

    def login(self, username: str, password: str):
        url = f"{self.base_url}/auth/login"
        data = {
            "username": username,
            "password": password,
            "public_key": Security.get_public_key_pem(self.public_key),
        }
        response = self.session.post(url, json=data, headers=self._get_headers())
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        return response.json(), response.status_code

    def send_message(self, recipient: str, content: str, recipient_public_key_pem:str):
        cyphered_text = Security.encrypt_text_with_public(plaintext=content.encode("utf-8"),
                                                          public_key_pem=recipient_public_key_pem)
        base64_cyphered_str = base64.b64encode(cyphered_text).decode('utf-8')
        url = f"{self.base_url}/messages/send_message"
        data = {"to": recipient, "message": base64_cyphered_str}
        response = self.session.post(url, json=data, headers=self._get_headers())
        return response.json(), response.status_code

    def get_server_public_key(self):
        url = f"{self.base_url}/auth/get_server_key"
        response = self.session.get(url, headers=self._get_headers())
        if response.status_code == 200:
            return response.json().get("public_key")
        else:
            raise Exception(f"Failed to fetch server public key: {response.status_code} - {response.text}")

    def get_received_messages(self):
        url = f"{self.base_url}/messages/long_polling"
        response = self.session.get(url, headers=self._get_headers())
        if response.status_code != 200:
            raise Exception(f"Failed to fetch messages: {response.status_code} - {response.text}")
        received_data = response.json()
        messages = received_data.get("messages")
        if len(messages) == 0:
            return []
        mapped_response = list(map(lambda x: self._map_message(x), messages))
        return mapped_response, response.status_code

    def get_users(self):
        url = f"{self.base_url}/auth/get_users"
        response = self.session.get(url, headers=self._get_headers())
        decrypted_data = Security.decrypt_object_with_private(
            encrypted_blocks_json=response.json(),
            private_key=self.private_key
        )
        if isinstance(decrypted_data, str):
            return json.loads(decrypted_data), response.status_code
        return decrypted_data, response.status_code  # если уже dict/list

    def get_publics(self, id_list: list):
        if id_list is None:
            id_list = []
        url = f"{self.base_url}/auth/get_publics"
        body = {"usernames": id_list}
        response = self.session.post(url, headers=self._get_headers(), json=body)
        decrypted_data = Security.decrypt_object_with_private(
            encrypted_blocks_json=response.json(),
            private_key=self.private_key
        )
        if isinstance(decrypted_data, str):
            json_data = json.loads(decrypted_data)
        else:
            json_data = decrypted_data
        return json_data, response.status_code

    def long_polling(self):
        url = f"{self.base_url}/messages/long_polling"
        response = self.session.get(url, headers=self._get_headers(), timeout=30)  # Добавлен таймаут для long-polling
        return response.json(), response.status_code

    def get_sent_messages(self):
        url = f"{self.base_url}/messages/sent"
        response = self.session.get(url, headers=self._get_headers())
        return response.json(), response.status_code

    def _map_message(self, message:dict):
        msg_from = message.get("from")
        content = message.get("message")
        decoded_content = base64.b64decode(content)
        plain_text = Security.decrypt_with_private(encrypted_message=decoded_content,
                                                   private_key=self.private_key).decode("utf-8")
        return {"from":msg_from, "message":plain_text}
