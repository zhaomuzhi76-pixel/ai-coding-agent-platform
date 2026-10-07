"""Stub backend for smoke tests (no external deps)."""
from __future__ import annotations

import os
from typing import Any, Dict, List


class StubBackend:
    """In-memory fake backend — for pipeline tests, not real training."""

    name = "stub"

    def __init__(self) -> None:
        self.prepared: List[Dict[str, Any]] = []
        self.trained_count = 0
        self.saved_to: List[str] = []

    def available(self) -> bool:
        return True

    def prepare(self, base_model: str, config: Any) -> Any:
        artifact = {"base_model": base_model, "config": config}
        self.prepared.append(artifact)
        return artifact

    def train(self, model: Any, samples: List[Any]) -> Any:
        self.trained_count += len(samples)
        model = dict(model)
        model["trained_samples"] = len(samples)
        return model

    def save(self, model: Any, output_dir: str) -> None:
        os.makedirs(output_dir, exist_ok=True)
        self.saved_to.append(output_dir)

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return {
            "name": self.name,
            "ready": self.ready(),
            "prepared": len(self.prepared),
            "trained": self.trained_count,
            "saved_to": list(self.saved_to),
        }
