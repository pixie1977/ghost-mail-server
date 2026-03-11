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
    """Класс для управления хранением пользователей в JSON-файле с поддержкой резервного копирования."""

    def __init__(self, users_file: str = "users.json", backup_dir: str = "backups") -> None:
        self.users_file = users_file
        self.backup_dir = backup_dir
        self.lock = threading.RLock()
        self.log = Logger()
        self.users_data = []

        # Создание директории для бэкапов, если не существует
        if not os.path.exists(self.backup_dir):
            self.log.info(f"Creating backup directory at {self.backup_dir}")
            os.makedirs(self.backup_dir)

        # Инициализация файла пользователей, если он отсутствует
        if not os.path.exists(self.users_file):
            self.log.info(f"Creating new users file at {self.users_file}")
            with open(self.users_file, "w") as f:
                json.dump(self.users_data, f)

    def create_backup(self) -> str:
        """Создаёт резервную копию файла users.json с временной меткой."""

        if not os.path.exists(self.users_file):
            return ""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"users_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        try:
            shutil.copy2(self.users_file, backup_path)
            return backup_path
        except Exception as e:
            print(f"Backup failed: {e}")
            return ""

    def get_all_users(self) -> List[User]:
        """Возвращает список всех пользователей из файла."""
        with self.lock:
            try:
                with open(self.users_file, "r") as f:
                    users_data = json.load(f)
                    return [User(**user) for user in users_data]
            except (FileNotFoundError, json.JSONDecodeError):
                return []

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Возвращает пользователя по имени, если он существует."""
        users = self.get_all_users()
        return next((user for user in users if user.username == username), None)

    def user_exists(self, username: str) -> bool:
        """Проверяет, существует ли пользователь с указанным именем."""
        return self.get_user_by_username(username) is not None

    def save_user(self, user: User) -> bool:
        """Сохраняет пользователя в файл с предварительным созданием резервной копии."""
        with self.lock:
            try:
                self.create_backup()
                users = self.get_all_users()
                # Удаляем существующего пользователя с таким же именем
                users = [u for u in users if u.username != user.username]
                users.append(user)

                with open(self.users_file, "w") as f:
                    json.dump([u.dict() for u in users], f, indent=2)

                return True
            except Exception as e:
                print(f"Failed to save user: {e}")
                return False

    def update_user(self, username: str, **kwargs) -> bool:
        """Обновляет поля пользователя по имени."""
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
                    with open(self.users_file, "w") as f:
                        json.dump([u.dict() for u in users], f, indent=2)

                return updated
            except Exception as e:
                print(f"Failed to update user: {e}")
                return False