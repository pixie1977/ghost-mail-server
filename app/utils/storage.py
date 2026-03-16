"""Модуль для работы с хранением данных пользователей в JSON-файле."""

import json
import os
import shutil
import threading
from datetime import datetime
from typing import List, Optional

from app.auth.schemas import User
from app.utils.logging import Logger


class Storage:
    """
    Класс для управления хранением пользователей в JSON-файле с поддержкой резервного копирования.

    Потокобезопасный доступ к данным через `threading.RLock`.
    Автоматическое создание файла и директории для бэкапов.
    Поддержка CRUD-операций: чтение, запись, обновление, проверка наличия.
    """

    def __init__(self, users_file: str = "users.json", backup_dir: str = "backups") -> None:
        """
        Инициализирует хранилище.

        :param users_file: Путь к файлу с данными пользователей.
        :param backup_dir: Директория для резервных копий.
        """
        self.users_file = users_file
        self.backup_dir = backup_dir
        self.lock = threading.RLock()
        self.log = Logger()

        # Создание директории для бэкапов
        if not os.path.exists(self.backup_dir):
            self.log.info(f"Creating backup directory at {self.backup_dir}")
            os.makedirs(self.backup_dir)

        # Инициализация файла пользователей
        if not os.path.exists(self.users_file):
            self.log.info(f"Creating new users file at {self.users_file}")
            with open(self.users_file, "w") as f:
                json.dump([], f)

    def create_backup(self) -> str:
        """
        Создаёт резервную копию файла users.json с временной меткой.

        :return: Путь к созданной копии или пустая строка при ошибке.
        """
        if not os.path.exists(self.users_file):
            return ""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"users_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        try:
            shutil.copy2(self.users_file, backup_path)
            self.log.info(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            self.log.error(f"Backup failed: {e}")
            return ""

    def get_all_users(self) -> List[User]:
        """
        Возвращает список всех пользователей из файла.

        :return: Список объектов User. Пустой список, если файл не существует или повреждён.
        """
        with self.lock:
            try:
                with open(self.users_file, "r", encoding="utf-8") as f:
                    users_data = json.load(f)
                    return [User(**user) for user in users_data]
            except (FileNotFoundError, json.JSONDecodeError) as e:
                self.log.warning(f"Failed to load users: {e}")
                return []

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Возвращает пользователя по имени.

        :param username: Имя пользователя.
        :return: Объект User или None, если не найден.
        """
        users = self.get_all_users()
        return next((user for user in users if user.username == username), None)

    def user_exists(self, username: str) -> bool:
        """
        Проверяет, существует ли пользователь с указанным именем.

        :param username: Имя пользователя.
        :return: True, если пользователь существует.
        """
        return self.get_user_by_username(username) is not None

    def save_user(self, user: User) -> bool:
        """
        Сохраняет пользователя в файл. Если пользователь уже существует — перезаписывает.

        Перед сохранением создаётся резервная копия.

        :param user: Объект User для сохранения.
        :return: True при успехе, иначе False.
        """
        with self.lock:
            try:
                self.create_backup()
                users = self.get_all_users()
                # Удаляем старую версию пользователя
                users = [u for u in users if u.username != user.username]
                users.append(user)

                with open(self.users_file, "w", encoding="utf-8") as f:
                    json.dump([u.dict() for u in users], f, indent=2, ensure_ascii=False)

                self.log.info(f"User saved: {user.username}")
                return True
            except Exception as e:
                self.log.error(f"Failed to save user {user.username}: {e}")
                return False

    def update_user(self, username: str, **kwargs) -> bool:
        """
        Обновляет поля указанного пользователя.

        :param username: Имя пользователя.
        :param kwargs: Поля и их новые значения (например, last_login="2025-04-05").
        :return: True, если пользователь найден и обновлён; иначе False.
        """
        with self.lock:
            try:
                self.create_backup()
                users = self.get_all_users()
                updated = False

                for user in users:
                    if user.username == username:
                        for key, value in kwargs.items():
                            if hasattr(user, key):
                                setattr(user, key, value)
                        updated = True
                        break

                if updated:
                    with open(self.users_file, "w", encoding="utf-8") as f:
                        json.dump([u.dict() for u in users], f, indent=2, ensure_ascii=False)
                    self.log.info(f"User updated: {username}")

                return updated
            except Exception as e:
                self.log.error(f"Failed to update user {username}: {e}")
                return False