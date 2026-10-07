from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ApplicationPluginContext:
    """
    Runtime context exposed to plugins.

    Owns:
        - runtime execution context

    Does not own:
        - plugin lifecycle
        - plugin registration
    """

    plugin_name: str
    runtime: Any = None
    metadata: dict[str, Any] | None = None

    def ready(self) -> bool:
        return bool(
            self.plugin_name
        )


__all__ = [
    "ApplicationPluginContext",
]
