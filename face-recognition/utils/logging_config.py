"""
Настройка логгера для системы распознавания лиц.
"""
import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", 
                  log_format: Optional[str] = None,
                  log_file: Optional[str] = None) -> logging.Logger:
    """
    Настройка и возврат логгера для приложения.
    
    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Формат сообщений лога
        log_file: Путь к файлу лога (если None, логи выводятся в консоль)
        
    Returns:
        Настроенный логгер
    """
    if log_format is None:
        log_format = "[%(levelname)s] %(name)s: %(message)s"
    
    # Создаём логгер
    logger = logging.getLogger("face_recognition")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Очищаем существующие обработчики
    logger.handlers.clear()
    
    # Создаём форматтер
    formatter = logging.Formatter(log_format)
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файловый обработчик (если указан)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
