import logging
from app.config import LOGS_DIR, create_required_directories


def get_logger(name: str = "subtitle_pipeline") -> logging.Logger:
    """
    Create and return a project logger.

    Logs are saved inside:
    backend/logs/pipeline.log

    This helps us debug errors and makes the project look production-ready.
    """

    create_required_directories()

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate logs if logger is called multiple times
    if logger.handlers:
        return logger

    log_file = LOGS_DIR / "pipeline.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    log_format = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler.setFormatter(log_format)
    console_handler.setFormatter(log_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger