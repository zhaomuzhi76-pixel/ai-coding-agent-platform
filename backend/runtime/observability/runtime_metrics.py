from __future__ import annotations

from time import perf_counter
from typing import Any

from backend.runtime.observability.metrics_store import (
    MetricsStore,
)


class RuntimeMetrics:
    """
    Runtime metrics collector.

    Each collector owns an isolated MetricsStore instance.

    Responsibility:
        - calculate runtime duration
        - update runtime metric repository

    Not Responsible:
        - event logging
        - persistence
        - lifecycle control
        - business processing
    """

    VERSION = "8.1"

    RESPONSIBILITY = (
        "runtime_metrics_collection",
    )

    def __init__(
        self,
        store: MetricsStore | None = None,
    ) -> None:
        self.store = (
            store
            if store is not None
            else MetricsStore()
        )

        if not self.store.ready():
            raise RuntimeError(
                "metrics store unavailable"
            )

        self.running = False
        self.start_time = 0.0

    def start(
        self,
    ) -> None:
        self.running = True
        self.start_time = perf_counter()

    def finish(
        self,
    ) -> None:
        if not self.running:
            return

        elapsed = (
            perf_counter()
            - self.start_time
        )

        current_elapsed = self.store.get(
            "elapsed",
        )

        self.store.update(
            "elapsed",
            current_elapsed + elapsed,
        )

        self.store.increment(
            "execution_count",
        )

        self.running = False
        self.start_time = 0.0

    def snapshot(
        self,
    ) -> dict[str, Any]:
        data = self.store.snapshot()
        data["running"] = self.running
        return data

    def clear(
        self,
    ) -> None:
        self.running = False
        self.start_time = 0.0
        self.store.reset()

    def ready(
        self,
    ) -> bool:
        return (
            self.store.ready()
        )

    def dump(
        self,
    ) -> dict[str, Any]:
        return {
            "name":
                type(self).__name__,
            "version":
                self.VERSION,
            "responsibility":
                self.RESPONSIBILITY,
            "ready":
                self.ready(),
            "metrics":
                self.snapshot(),
            "store":
                type(self.store).__name__,
        }


__all__ = [
    "RuntimeMetrics",
]
