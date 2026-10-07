from __future__ import annotations

from typing import Any


class MetricsStore:
    """
    Runtime metrics state repository.

    Responsibility:
        - store runtime metric state
        - provide metric snapshot

    Not Responsible:
        - metric calculation
        - lifecycle tracking
        - reporting
    """

    VERSION = "4.1"

    RESPONSIBILITY = (
        "runtime_metrics_repository",
    )

    DEFAULTS = {
        "started_at": None,
        "finished_at": None,
        "elapsed": 0,
        "execution_count": 0,
        "success_count": 0,
        "failure_count": 0,
    }

    def __init__(
        self,
    ) -> None:
        self.reset()

    def reset(
        self,
    ) -> None:
        self.data = dict(self.DEFAULTS)

    def update(
        self,
        key: str,
        value: Any,
    ) -> None:
        if key not in self.DEFAULTS:
            raise KeyError(
                f"unknown metric: {key}"
            )

        self.data[key] = value

    def increment(
        self,
        key: str,
    ) -> None:
        if key not in self.DEFAULTS:
            raise KeyError(
                f"unknown metric: {key}"
            )

        value = self.data[key]

        if not isinstance(
            value,
            int,
        ):
            raise TypeError(
                "metric must integer"
            )

        self.data[key] = value + 1

    def get(
        self,
        key: str,
    ) -> Any:
        return self.data[key]

    def snapshot(
        self,
    ) -> dict[str, Any]:
        return dict(self.data)

    def ready(
        self,
    ) -> bool:
        return bool(self.data)

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
        }


__all__ = [
    "MetricsStore",
]
