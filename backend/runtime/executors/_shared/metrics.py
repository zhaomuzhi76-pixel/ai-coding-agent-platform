"""Execution counters shared by executors and providers."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExecutorMetrics:
    execution: int = 0
    success: int = 0
    failure: int = 0

    def mark_execution(self) -> None:
        self.execution += 1

    def mark_success(self) -> None:
        self.success += 1

    def mark_failure(self) -> None:
        self.failure += 1

    def as_dict(self) -> dict:
        return {
            "execution": self.execution,
            "success": self.success,
            "failure": self.failure,
        }
