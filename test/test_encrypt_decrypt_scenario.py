import json
import os

from app.utils.security import Security
from test_client import GhostMailClient


def test_register_login_workflow():
    """Тест шифрования и дешифрования большого JSON-объекта."""
    security = Security()

    long_string = "a" * 2046
    data = {
        "login": "login",
        "password": "password",
    }

    array_string = [long_string for _ in range(256)]
    data["array_string"] = array_string

    print("\n🧪 Начинаем тест шифрования и дешифрования большого объекта...")

    # Получаем публичный ключ в формате PEM
    public_key_pem = security.get_self_public_key_pem()

    # Шифруем объект
    encrypted_blocks_json = security.encrypt_object_with_public(data, public_key_pem)
    print("✅ Объект успешно зашифрован.")

    # Дешифруем объект
    decrypted_data = Security.decrypt_object_with_private(
        encrypted_blocks_json, security.private_key
    )
    print("✅ Объект успешно расшифрован.")

    # Проверяем, что данные совпадают
    assert decrypted_data == data, "Расшифрованные данные не совпадают с оригинальными!"
    print("✅ Шифрование и дешифрование прошли успешно, данные идентичны.")

    print("\n✅ Все тесты пройдены успешно!")