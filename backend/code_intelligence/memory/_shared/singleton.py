"""Thread-safe singleton mixin."""
from __future__ import annotations

import threading
from typing import Any, ClassVar


class SingletonMixin:
    _LOCK: ClassVar[threading.Lock] = threading.Lock()
    _INSTANCE: ClassVar[Any] = None

    @classmethod
    def instance(cls):
        with cls._LOCK:
            if cls._INSTANCE is None:
                cls._INSTANCE = cls()
            return cls._INSTANCE
