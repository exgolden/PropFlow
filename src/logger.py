import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOGS_DIR = os.path.join(os.path.dirname(__file__), "../logs")
LOG_FILE = os.path.join(LOGS_DIR, "app.log")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(module)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger() -> logging.Logger:
    """
    Configures and returns the application logger.
    Writes to a single rotating log file — rotates every 30 days, keeps last 12 months.
    Called once in create_app().
    """
    os.makedirs(LOGS_DIR, exist_ok=True)
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        return logger
    handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="D",
        interval=30,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger


def get_logger() -> logging.Logger:
    """
    Returns the application logger.
    Call this in any module that needs to log something.
    """
    return logging.getLogger("app")