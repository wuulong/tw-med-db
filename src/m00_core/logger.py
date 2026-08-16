"""
logger.py - 雙管道 Console 與檔案滾動 Logger
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def setup_module_logger(module_name: str = "med_db", log_file_path: str = "logs/tw_med_engine.log") -> logging.Logger:
    """
    建立雙管道 Log：Console 輸出與檔案滾動紀錄 (RotatingFileHandler 10MB x 5)。
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 1. Console Stream Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 2. Rotating File Handler
        try:
            log_dir = os.path.dirname(log_file_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            file_handler = RotatingFileHandler(log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass

    return logger
