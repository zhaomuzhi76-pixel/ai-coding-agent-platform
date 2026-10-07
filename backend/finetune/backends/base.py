"""FinetuneBackend protocol."""
from __future__ import annotations

from typing import Any, List, Protocol, runtime_checkable

from backend.finetune.config import FinetuneConfig


@runtime_checkable
class FinetuneBackend(Protocol):
    name: str

    def available(self) -> bool: ...

    def prepare(self, base_model: str, config: FinetuneConfig) -> Any: ...

    def train(self, model: Any, samples: List[Any]) -> Any: ...

    def save(self, model: Any, output_dir: str) -> None: ...

    def ready(self) -> bool: ...

    def dump(self) -> dict: ...
