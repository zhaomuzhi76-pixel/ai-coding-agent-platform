"""当现有 registry 无 register_model 时，用它适配，避免改动 registry.py。"""
from __future__ import annotations

from typing import Any


class LegacyRegistryAdapter:
    def __init__(self, registry: Any) -> None:
        self._r = registry

    def register_model(self, model_id: str, *, provider: str,
                       context_window: int, display_name: str) -> None:
        bucket = getattr(self._r, "_models", None)
        if bucket is None:
            bucket = {}
            setattr(self._r, "_models", bucket)
        bucket[model_id] = {
            "id": model_id,
            "provider": provider,
            "context_window": context_window,
            "display_name": display_name,
        }
