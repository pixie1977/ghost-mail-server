import logging


class Logger:
    def __init__(self, log_file: str = "server.log",
                 log_level: int = logging.INFO,
                 log_name: str = __name__,
                 ) -> None:
        self.log_file = log_file
        self.log_level = log_level

        # Настройка логирования
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.log_file, encoding="utf-8"),
                logging.StreamHandler(),  # Вывод также в консоль
            ],
        )

        self.logger = logging.getLogger(log_name)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def log_request(self, method: str, url: str, client_ip: str, status_code: int) -> None:
        self.logger.info(f"{method} {url} - {client_ip} - {status_code}")

    def log_authentication(self, username: str, success: bool, ip: str) -> None:
        if success:
            self.logger.info(f"Authentication successful for user '{username}' from {ip}")
        else:
            self.logger.warning(f"Authentication failed for user '{username}' from {ip}")

    def log_error(self, error: Exception, context: str = "") -> None:
        self.logger.error(f"{context} - {str(error)}")