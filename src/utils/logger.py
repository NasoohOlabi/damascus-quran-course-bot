import logging
import os
import sys
from datetime import datetime
from typing import Optional


def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """Configure structured logging with level handling"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
    )

    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create file handler with daily log files
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(logs_dir, f'{today}.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Configure third-party loggers
    for lib in ['httpx', 'telegram', 'googleapiclient']:
        logging.getLogger(lib).setLevel(logging.WARNING)

    return logger
