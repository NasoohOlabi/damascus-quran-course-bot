import logging
import sys
from typing import Optional


def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """Configure structured logging with level handling"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    logger.addHandler(console_handler)

    # Configure third-party loggers
    for lib in ['httpx', 'telegram', 'googleapiclient']:
        logging.getLogger(lib).setLevel(logging.WARNING)

    return logger
