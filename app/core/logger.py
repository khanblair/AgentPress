"""
app/core/logger.py — Structured logging routed to /logs files + console
"""

import sys
import logging
from pathlib import Path
from loguru import logger
import os

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Read from env directly (settings not imported here to avoid circular imports)
CONSOLE_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


def setup_logger(name: str = "agentpress") -> "logger":
    logger.remove()

    # Console — colourised, level from .env
    logger.add(
        sys.stderr,
        colorize=True,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan> — {message}"
        ),
        level=CONSOLE_LEVEL,
    )

    # Full execution log — always DEBUG
    logger.add(
        LOG_DIR / "agent_execution.log",
        rotation="50 MB",
        retention="14 days",
        compression="gz",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} — {message}",
        level="DEBUG",
        enqueue=True,
    )

    # Error-only log
    logger.add(
        LOG_DIR / "api_errors.log",
        rotation="20 MB",
        retention="30 days",
        compression="gz",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} — {message}",
        level="ERROR",
        enqueue=True,
    )

    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            frame, depth = sys._getframe(6), 6
            while frame and frame.f_code.co_filename == getattr(logging, "__file__", ""):
                frame = frame.f_back
                depth += 1
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    return logger.bind(name=name)


log = setup_logger("agentpress")
