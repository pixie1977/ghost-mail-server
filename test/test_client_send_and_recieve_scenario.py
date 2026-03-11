import base64
import os

import pytest
from app.utils.security import Security
from test_client import GhostMailClient


def test_client_send_receive_message_flow(server):
    """Тест полного цикла: регистрация, логин, отправка и получение сообщений между двумя клиентами"""

    # Путь к файлу
    file_path = "users.json"

    # Удаление файла, если он существует
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Файл {file_path} был удалён.")
    else:
        print(f"Файл {file_path} не найден. Пропускаем удаление.")

    # Создаем двух клиентов
    client1 = GhostMailClient()
    client2 = GhostMailClient()
    
    # Регистрация client1
    print("\nРегистрация client1...")
    reg_data1, reg_status1 = client1.register("testuser1", "testpass1", "Test Alias 1")
    assert reg_status1 == 200, f"Регистрация client1 не удалась: {reg_data1}"
    print(f"Статус регистрации client1: {reg_status1}, Данные: {reg_data1}")
    
    # Логин client1
    print("\nЛогин client1...")
    login_data1, login_status1 = client1.login("testuser1", "testpass1")
    assert login_status1 == 200, f"Логин client1 не удался: {login_data1}"
    assert "access_token" in login_data1, "Токен отсутствует в ответе логина client1"
    print(f"Статус client1: {login_status1}, Данные: {login_data1}")
    
    # Регистрация client2
    print("\nРегистрация client2...")
    reg_data2, reg_status2 = client2.register("testuser2", "testpass2", "Test Alias 2")
    assert reg_status2 == 200, f"Регистрация client2 не удалась: {reg_data2}"
    print(f"Статус регистрации client2: {reg_status2}, Данные: {reg_data2}")
    
    # Логин client2
    print("\nЛогин client2...")
    login_data2, login_status2 = client2.login("testuser2", "testpass2")
    assert login_status2 == 200, f"Логин client2 не удался: {login_data2}"
    assert "access_token" in login_data2, "Токен отсутствует в ответе логина client2"
    print(f"Статус client2: {login_status2}, Данные: {login_data2}")
    
    # Получение списка пользователей
    print("\nclient1 запрашивает список пользователей...")
    users_data, users_status = client1.get_users()
    assert users_status == 200, f"Получение списка пользователей не удалось: {users_data}"
    assert isinstance(users_data, list), "Список пользователей должен быть списком"
    assert len(users_data) >= 2, "Должно быть как минимум 2 зарегистрированных пользователя"
    print(f"Список пользователей: {users_data}")

    print("\nclient1 запрашивает список public keys...")
    users_ids = list(map(lambda x: x.get("login"), users_data))
    users_public_keys, users_status = client1.get_publics(users_ids)
    assert users_status == 200, f"Получение спискa публичных ключей не удалось: {users_data}"
    assert isinstance(users_public_keys, list), "Список публичных ключей должен быть списком"
    assert len(users_public_keys) >= 2, "Должно быть как минимум 2 ключа"
    print(f"Список публичных ключей: {users_public_keys}")

    # # Отправка сообщения от client1 к client2
    print("\nОтправка сообщения от client1 к client2...")
    plain_text="Привет, это тестовое сообщение!"

    target_username = "testuser2"
    found_user = next(
        filter(lambda user: user.get("username") == target_username, users_public_keys),
        None  # вернёт None, если пользователь не найден
    )
    assert found_user is not None, f"Пользователь {target_username} не найден в списке"
    print(f"Найден пользователь для отправки: {found_user}")
    #Шифруется текст с помощью публичного RSA-ключа адресата
    public_key_pem=found_user.get("publickey")

    msg_data, msg_status = client1.send_message(
        recipient="testuser2",
        content=plain_text,
        recipient_public_key_pem=public_key_pem
    )
    assert msg_status == 200, f"Отправка сообщения не удалась: {msg_data}"
    assert "message_id" in msg_data, "ID сообщения отсутствует в ответе"
    print(f"Статус: {msg_status}, Данные: {msg_data}")

    # Получение входящих сообщений client2
    print("\nПолучение входящих сообщений client2...")
    received_messages, received_status = client2.get_received_messages()
    assert received_status == 200, f"Получение входящих сообщений не удалось: {received_data}"
    assert isinstance(received_messages, list), "Входящие сообщения должны быть списком"
    assert len(received_messages) > 0, "Должно быть хотя бы одно входящее сообщение"

    message = received_messages[0]
    assert message.get("from") == "testuser1", "Отправитель сообщения не совпадает"

    plain_text = message.get("message")
    assert plain_text == "Привет, это тестовое сообщение!", "Содержание сообщения не совпадает"
    print(f"Статус: {received_status}, Данные: {received_messages}")
