"""
Configuración de logging
"""

import logging
import sys
from datetime import datetime


def setup_logging(level: str = "INFO", log_file: str = None):
    """
    Configura el sistema de logging

    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        log_file: Archivo de log opcional
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Configurar logger raíz
    root_logger = logging.getLogger("gavilan")
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Handler de archivo si se especifica
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger con el nombre especificado"""
    return logging.getLogger(f"gavilan.{name}")
