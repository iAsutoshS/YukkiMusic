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
import io
from logging.handlers import RotatingFileHandler
from config import LOG_FILE_NAME  # Example: "logs/logs.txt"

# Ensure the log directory exists
log_dir = os.path.dirname(LOG_FILE_NAME)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Logging format
LOG_FORMAT = "[%(asctime)s - %(levelname)s] - %(name)s - %(message)s"
DATE_FORMAT = "%d-%b-%y %H:%M:%S"
formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

# Get root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Clear previous handlers (to avoid duplication)
if logger.hasHandlers():
    logger.handlers.clear()

# File handler
file_handler = RotatingFileHandler(LOG_FILE_NAME, maxBytes=5_000_000, backupCount=5, encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Silence noisy libraries (optional)
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
    LOGGER("UncaughtException").error("Uncaught exception occurred", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Redirect stderr (like yt_dlp errors) to log file
class StreamToLogger(io.StringIO):
    def __init__(self, logger, level):
        super().__init__()
        self.logger = logger
        self.level = level

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass

# Redirect standard error to logging
sys.stderr = StreamToLogger(LOGGER("STDERR"), logging.ERROR)


