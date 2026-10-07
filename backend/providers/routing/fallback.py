"""Fallback chain: try models in order, return first success."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List


@dataclass
class FallbackAttempt:
    model: str
    ok: bool
    error: str = ""


@dataclass
class FallbackResult:
    value: Any
    used_model: str
    attempts: List[FallbackAttempt] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return bool(self.used_model)


class FallbackChain:
    """Run a callable across a list of models until one succeeds."""

    def __init__(self, models: List[str]) -> None:
        if not models:
            raise ValueError("fallback chain requires at least one model")
        self._models = list(models)

    def run(
        self,
        call: Callable[[str], Any],
        *,
        ignore: tuple = (),
    ) -> FallbackResult:
        attempts: List[FallbackAttempt] = []
        for model in self._models:
            try:
                value = call(model)
                attempts.append(FallbackAttempt(model=model, ok=True))
                return FallbackResult(
                    value=value, used_model=model, attempts=attempts,
                )
            except ignore:
                raise
            except Exception as exc:
                attempts.append(FallbackAttempt(
                    model=model, ok=False,
                    error=f"{type(exc).__name__}: {exc}",
                ))
        return FallbackResult(
            value=None, used_model="", attempts=attempts,
        )

    def models(self) -> List[str]:
        return list(self._models)

    def ready(self) -> bool:
        return bool(self._models)

    def dump(self) -> dict:
        return {"ready": self.ready(), "models": list(self._models)}
