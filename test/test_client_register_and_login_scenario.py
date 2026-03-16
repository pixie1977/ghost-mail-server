import os

from app.client.test_client import GhostMailClient

def test_register_login_workflow(server):
    # Путь к файлу
    file_path = "users.json"

    # Удаление файла, если он существует
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Файл {file_path} был удалён.")
    else:
        print(f"Файл {file_path} не найден. Пропускаем удаление.")

    client1 = GhostMailClient()
    client2 = GhostMailClient()

    # --- Тест: Регистрация client1 ---
    print("Регистрация client1...")
    reg_data, reg_status = client1.register("testuser1", "testpass1", "Test Alias 1")
    print(f"Статус регистрации client1: {reg_status}, Данные: {reg_data}")
    assert reg_status == 200, "Ожидалась успешная регистрация client1"

    # --- Тест: Логин client1 ---
    print("\nЛогин client1...")
    login_data, login_status = client1.login("testuser1", "testpass1")
    print(f"Статус логина client1: {login_status}, Данные: {login_data}")
    assert login_status == 200, "Ожидался успешный логин client1"
    assert "access_token" in login_data, "Токен отсутствует при логине client1"

    # --- Тест: Повторная регистрация с тем же username client1 (должна быть ошибка) ---
    print("\nПовторная регистрация client1 (ожидается ошибка)...")
    reg_data2, reg_status2 = client1.register("testuser1", "newpass", "Duplicate")
    print(f"Статус: {reg_status2}, Ответ: {reg_data2}")
    assert reg_status2 == 409, "Ожидалась ошибка 409 при дублировании username"
    assert "username already exists" in reg_data2.get("detail", "").lower(), "Нет ожидаемого сообщения об ошибке"

    # --- Тест: Регистрация client2 ---
    print("\nРегистрация client2...")
    reg_data3, reg_status3 = client2.register("testuser2", "testpass2", "Test Alias 2")
    print(f"Статус регистрации client2: {reg_status3}, Данные: {reg_data3}")
    assert reg_status3 == 200, "Ожидалась успешная регистрация client2"

    # --- Тест: Логин client2 ---
    print("\nЛогин client2...")
    login_data2, login_status2 = client2.login("testuser2", "testpass2")
    print(f"Статус логина client2: {login_status2}, Данные: {login_data2}")
    assert login_status2 == 200, "Ожидался успешный логин client2"
    assert "access_token" in login_data2, "Токен отсутствует при логине client2"

    print("\n✅ Все тесты пройдены успешно!")
