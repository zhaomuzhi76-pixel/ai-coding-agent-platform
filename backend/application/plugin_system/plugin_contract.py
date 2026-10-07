from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ApplicationPluginContract(ABC):
    """
    Base contract for application extensions.

    Owns:
        - plugin lifecycle entry points
        - plugin execution entry point

    Does not own:
        - registry
        - dependency resolution
        - execution routing
    """

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def version(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def initialize(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def activate(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        *,
        context: Any,
        payload: dict[str, Any],
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def ready(self) -> bool:
        raise NotImplementedError


__all__ = [
    "ApplicationPluginContract",
]
