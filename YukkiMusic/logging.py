#
# Copyright (C) 2024-2025 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.

import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from config import LOG_FILE_NAME  # Make sure this is like "logs/logs.txt" or "logs.txt"

# Ensure the log directory exists
log_dir = os.path.dirname(LOG_FILE_NAME)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Log format and level
LOG_FORMAT = "[%(asctime)s - %(levelname)s] - %(name)s - %(message)s"
DATE_FORMAT = "%d-%b-%y %H:%M:%S"

# Create formatter
formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

# Set up root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Capture all levels

# Clear existing handlers (important in some reloadable environments)
if logger.hasHandlers():
    logger.handlers.clear()

# File handler
file_handler = RotatingFileHandler(LOG_FILE_NAME, maxBytes=5000000, backupCount=5, encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Silence overly verbose loggers (optional)
for noisy in ["httpx", "pyrogram", "pymongo", "ntgcalls", "pytgcalls"]:
    logging.getLogger(noisy).setLevel(logging.ERROR)

# Logger utility
def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

# Global exception hook
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger = LOGGER("UncaughtException")
    logger.error("Uncaught exception occurred:", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

