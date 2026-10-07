from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PersistencePluginContext:
    plugin_name: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def ready(self) -> bool:
        return bool(self.plugin_name.strip())


__all__ = ["PersistencePluginContext"]
