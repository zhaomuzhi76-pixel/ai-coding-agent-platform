from __future__ import annotations

from backend.core.contracts.value import CoreValue

import sys
from pathlib import Path
from typing import Final

from loguru import logger as _logger


class LoggerManager:
    """
    Minimal logging foundation.

    Responsibility:

        - configure application logging
        - provide logger access

    Not Responsible:

        - configuration loading
        - metrics
        - tracing
        - health monitoring
        - lifecycle orchestration
        - business logging policy
        - global application state
    """

    VERSION: Final = "8.0"

    RESPONSIBILITY: Final = (
        "application_logging",
    )

    _initialized = False

    def init(
        self,
        log_dir: str | Path = "logs",
        level: str = "INFO",
    ) -> None:

        if self._initialized:
            return

        target_dir = Path(
            log_dir
        )

        if not target_dir.is_absolute():
            target_dir = Path.cwd() / target_dir

        target_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        _logger.remove()

        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level:<8}</level> | "
            "<cyan>{name}</cyan>:"
            "<cyan>{function}</cyan>:"
            "<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level:<8} | "
            "{process.id}:{thread.id} | "
            "{name}:{function}:{line} | "
            "{message}"
        )

        _logger.add(
            sys.stdout,
            level=level,
            colorize=True,
            enqueue=True,
            backtrace=False,
            diagnose=False,
            format=console_format,
        )

        _logger.add(
            target_dir / "app.log",
            level=level,
            encoding="utf-8",
            enqueue=True,
            backtrace=False,
            diagnose=False,
            format=file_format,
        )

        _logger.add(
            target_dir / "error.log",
            level="ERROR",
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=False,
            format=file_format,
        )

        self._initialized = True

    def get(
        self,
        module: str | None = None,
    ):
        if not self._initialized:
            self.init()

        if module is None:
            return _logger

        return _logger.bind(
            module=module
        )

    def ready(
        self,
    ) -> bool:

        return self._initialized

    def dump(
        self,
    ) -> dict[str, CoreValue]:

        return {
            "name": "LoggerManager",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = [
    "LoggerManager",
]
