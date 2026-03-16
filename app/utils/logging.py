import logging
from typing import Optional


class Logger:
    """
    Универсальный логгер для серверных приложений с поддержей файлового и консольного вывода.

    Настройка логирования производится один раз при первом создании экземпляра.
    Все последующие экземпляры будут использовать уже настроенный логгер с тем же именем.

    Пример использования:
        logger = Logger(__name__)
        logger.info("Сообщение")
        logger.log_request("GET", "/api/v1/data", "192.168.1.1", 200)

    :param log_file: Путь к файлу логов (по умолчанию 'server.log').
    :param log_level: Уровень логирования (по умолчанию logging.INFO).
    :param log_name: Имя логгера (рекомендуется передавать __name__).
    """

    _initialized = False

    def __init__(
        self,
        log_file: str = "server.log",
        log_level: int = logging.INFO,
        log_name: str = "app",
    ) -> None:
        self.log_file = log_file
        self.log_level = log_level
        self.logger = logging.getLogger(log_name)

        # Настраиваем хендлеры только один раз
        if not Logger._initialized:
            self._setup_logging()
            Logger._initialized = True

    def _setup_logging(self) -> None:
        """Настраивает формат и обработчики логирования."""
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Файл-хендлер с UTF-8 кодировкой
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)

        # Консольный хендлер
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)

        # Добавляем хендлеры к корневому логгеру
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    def info(self, message: str) -> None:
        """
        Логирует информационное сообщение.

        :param message: Текст сообщения.
        """
        self.logger.info(message)

    def error(self, message: str) -> None:
        """
        Логирует ошибку.

        :param message: Текст сообщения об ошибке.
        """
        self.logger.error(message)

    def warning(self, message: str) -> None:
        """
        Логирует предупреждение.

        :param message: Текст предупреждения.
        """
        self.logger.warning(message)

    def debug(self, message: str) -> None:
        """
        Логирует отладочное сообщение.

        :param message: Текст отладочной информации.
        """
        self.logger.debug(message)

    def log_request(
        self, method: str, url: str, client_ip: str, status_code: int
    ) -> None:
        """
        Логирует HTTP-запрос.

        :param method: HTTP-метод (GET, POST и т.д.).
        :param url: Запрашиваемый URL.
        :param client_ip: IP-адрес клиента.
        :param status_code: Код ответа HTTP.
        """
        self.logger.info(f"{method} {url} - {client_ip} - {status_code}")

    def log_authentication(
        self, username: str, success: bool, ip: str
    ) -> None:
        """
        Логирует попытку аутентификации.

        :param username: Имя пользователя.
        :param success: Успешна ли аутентификация.
        :param ip: IP-адрес, с которого произведена попытка.
        """
        if success:
            self.logger.info(
                f"Authentication successful for user '{username}' from {ip}"
            )
        else:
            self.logger.warning(
                f"Authentication failed for user '{username}' from {ip}"
            )

    def log_error(
        self, error: Exception, context: str = ""
    ) -> None:
        """
        Логирует исключение с дополнительным контекстом.

        :param error: Исключение (Exception).
        :param context: Дополнительный контекст (например, имя функции или действие).
        """
        error_msg = f"{context} - {str(error)}" if context else str(error)
        self.logger.error(error_msg, exc_info=True)