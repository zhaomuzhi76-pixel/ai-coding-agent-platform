"""FinetuneTrainer: orchestrate prepare → train → save."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.finetune.backends.base import FinetuneBackend
from backend.finetune.backends.peft_lora import LoRABackend
from backend.finetune.backends.prefix_tuning import PrefixTuningBackend
from backend.finetune.backends.stub import StubBackend
from backend.finetune.config import FinetuneConfig
from backend.finetune.data.sample import FinetuneSample


@dataclass
class TrainReport:
    method: str
    base_model: str
    sample_count: int
    saved_to: str = ""
    backend: str = ""
    ok: bool = True
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def dump(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            "base_model": self.base_model,
            "sample_count": self.sample_count,
            "saved_to": self.saved_to,
            "backend": self.backend,
            "ok": self.ok,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


def _select_backend(config: FinetuneConfig) -> FinetuneBackend:
    if config.method == "lora":
        return LoRABackend()
    if config.method == "prefix":
        return PrefixTuningBackend()
    if config.method == "stub":
        return StubBackend()
    raise ValueError(f"unknown method: {config.method}")


class FinetuneTrainer:
    """High-level trainer orchestrating backend + data."""

    def __init__(
        self,
        config: FinetuneConfig,
        backend: Optional[FinetuneBackend] = None,
    ) -> None:
        if not isinstance(config, FinetuneConfig):
            raise TypeError("config must FinetuneConfig")
        if not config.base_model:
            raise ValueError("config.base_model required")
        self._config = config
        self._backend = backend or _select_backend(config)

    @property
    def config(self) -> FinetuneConfig:
        return self._config

    @property
    def backend(self) -> FinetuneBackend:
        return self._backend

    def ready(self) -> bool:
        return self._backend.ready()

    def available(self) -> bool:
        return self._backend.available()

    def train(self, samples: List[FinetuneSample], on_progress=None) -> TrainReport:
        report = TrainReport(
            method=self._config.method,
            base_model=self._config.base_model,
            sample_count=len(samples),
            backend=self._backend.name,
        )
        if not samples:
            report.ok = False
            report.error = "no samples"
            return report
        try:
            artifact = self._backend.prepare(
                self._config.base_model, self._config,
            )
            trained = self._backend.train(artifact, list(samples), on_progress=on_progress)
            self._backend.save(trained, self._config.output_dir)
            report.saved_to = self._config.output_dir
            report.metadata["config"] = self._config.to_dict()
        except NotImplementedError as exc:
            report.ok = False
            report.error = f"not_implemented: {exc}"
        except Exception as exc:
            report.ok = False
            report.error = f"{type(exc).__name__}: {exc}"
        return report

    def dump(self) -> Dict[str, Any]:
        return {
            "config": self._config.to_dict(),
            "backend": self._backend.dump(),
            "ready": self.ready(),
            "available": self.available(),
        }


__all__ = ["FinetuneTrainer", "TrainReport"]
