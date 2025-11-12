# app/logging_config.py
"""Central logging configuration.

Initializes Python logging using LOG_LEVEL from settings. Import this module
once early (e.g., in main.py) to apply configuration.
"""
from logging import basicConfig, getLogger, Formatter, StreamHandler, INFO
import logging
from app.config.config import settings
import sys

_LEVEL_MAP = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'NOTSET': logging.NOTSET,
}

level = _LEVEL_MAP.get(settings.log_level.upper(), INFO)

handler = StreamHandler(sys.stdout)
handler.setFormatter(Formatter('[%(asctime)s] %(levelname)s %(name)s - %(message)s'))

root_logger = getLogger()
root_logger.setLevel(level)
# Avoid duplicate handlers if re-imported
if not root_logger.handlers:
    root_logger.addHandler(handler)

getLogger(__name__).debug("Logging initialized at level %s", settings.log_level)
