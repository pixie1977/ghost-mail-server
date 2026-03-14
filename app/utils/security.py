import base64
import json
from datetime import datetime, timedelta
from typing import Any, Dict

import bcrypt
import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey


class Security:
    """Класс для обеспечения безопасности: шифрование, хэширование, JWT."""

    def __init__(self) -> None:
        self.private_key = None
        self.public_key = None
        self.generate_rsa_keys()

    def generate_rsa_keys(self) -> None:
        """Генерирует пару RSA-ключей (4096 бит)."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )
        self.public_key = self.private_key.public_key()

    @staticmethod
    def get_public_key_pem(public_key: RSAPublicKey) -> str:
        """Возвращает публичный ключ в формате PEM."""
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem.decode("utf-8")

    def get_self_public_key_pem(self) -> str:
        """Возвращает собственный публичный ключ в формате PEM."""
        return self.get_public_key_pem(self.public_key)

    @staticmethod
    def encrypt_object_with_public(obj: object, public_key_pem: str) -> str:
        """
        Шифрует объект (в формате JSON) с помощью публичного ключа.

        :param obj: Объект для шифрования.
        :param public_key_pem: Публичный ключ в формате PEM.
        :return: Зашифрованный объект в формате base64.
        """
        response_json = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        max_block_size = 446
        encrypted_blocks = []

        # Разбиваем данные на блоки по 446 байт
        for i in range(0, len(response_json), max_block_size):
            block = response_json[i:i + max_block_size]
            encrypted_block = Security.encrypt_text_with_public(block, public_key_pem)
            encrypted_blocks.append(base64.b64encode(encrypted_block).decode("utf-8"))

        # Возвращаем список зашифрованных блоков в виде JSON
        return json.dumps(encrypted_blocks)

    @staticmethod
    def encrypt_text_with_public(plaintext: bytes, public_key_pem: str) -> bytes:
        """
        Шифрует текст с помощью публичного ключа RSA-OAEP.

        :param plaintext: Сообщение для шифрования (макс. 446 байт при RSA-4096).
        :param public_key_pem: Публичный ключ в формате PEM.
        :return: Зашифрованное сообщение.
        :raises ValueError: Если сообщение слишком длинное.
        """
        max_plaintext_size = 446  # Для RSA-4096 с OAEP и SHA-256
        if len(plaintext) > max_plaintext_size:
            raise ValueError(
                f"Сообщение слишком длинное для RSA-4096 с OAEP. "
                f"Максимум: {max_plaintext_size} байт."
            )

        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        encrypted = public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None,
            ),
        )
        return encrypted

    @staticmethod
    def decrypt_with_private(encrypted_message: bytes, private_key) -> bytes:
        """
        Дешифрует сообщение с помощью приватного ключа.

        :param encrypted_message: Зашифрованное сообщение.
        :param private_key: Приватный ключ.
        :return: Расшифрованное сообщение.
        """
        decrypted = private_key.decrypt(
            encrypted_message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None,
            ),
        )
        return decrypted

    def decrypt_self_with_private(self, encrypted_message: bytes) -> bytes:
        """
        Дешифрует сообщение с помощью собственного приватного ключа.

        :param encrypted_message: Зашифрованное сообщение.
        :return: Расшифрованное сообщение.
        """
        return self.decrypt_with_private(encrypted_message, self.private_key)

    @staticmethod
    def decrypt_object_with_private(encrypted_blocks_json: str, private_key) -> Any:
        """
        Дешифрует большой объект, зашифрованный по блокам с помощью RSA.

        :param encrypted_blocks_json: JSON-строка с массивом base64-закодированных зашифрованных блоков.
        :return: Расшифрованный объект (например, dict, list).
        :raises ValueError: Если дешифрование одного из блоков не удалось.
        """
        try:
            encrypted_blocks = json.loads(encrypted_blocks_json)
            decrypted_data = b''

            for block_b64 in encrypted_blocks:
                encrypted_block = base64.b64decode(block_b64)
                decrypted_block = Security.decrypt_with_private(encrypted_block, private_key)
                decrypted_data += decrypted_block

            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            raise ValueError(f"Ошибка при дешифровании объекта: {str(e)}")

    def hash_password(self, password: str, salt: bytes = None) -> bytes:
        """
        Хэширует пароль с использованием bcrypt.

        :param password: Пароль в виде строки.
        :param salt: Соль (генерируется, если не передана).
        :return: Хэшированный пароль.
        """
        if salt is None:
            salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Проверяет, соответствует ли пароль хэшу.

        :param password: Введённый пароль.
        :param hashed_password: Сохранённый хэш.
        :return: True, если пароль верен.
        """
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    def create_jwt_token(
        self,
        payload: Dict[str, Any],
        secret_key: str,
        algorithm: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Создаёт JWT-токен с временем жизни.

        :param payload: Полезная нагрузка.
        :param secret_key: Секретный ключ.
        :param algorithm: Алгоритм подписи.
        :param expires_in: Время жизни токена в секундах.
        :return: Закодированный JWT-токен.
        """
        payload["exp"] = datetime.utcnow() + timedelta(seconds=expires_in)
        return jwt.encode(payload, secret_key, algorithm=algorithm)

    def decode_jwt_token(
        self,
        token: str,
        secret_key: str,
        algorithm: str,
    ) -> Dict[str, Any]:
        """
        Декодирует JWT-токен.

        :param token: JWT-токен.
        :param secret_key: Секретный ключ.
        :param algorithm: Алгоритм подписи.
        :return: Раскодированная полезная нагрузка.
        :raises Exception: Если токен просрочен или невалиден.
        """
        try:
            return jwt.decode(token, secret_key, algorithms=[algorithm])
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")