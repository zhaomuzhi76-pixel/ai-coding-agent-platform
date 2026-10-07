from __future__ import annotations

from typing import TypedDict

from backend.core.contracts.payload import Payload


class ExecutionOutputSnapshot(TypedDict):
    """Execution output entity snapshot contract."""

    name: str
    version: str
    responsibility: tuple[str, ...]
    ready: bool
    output_id: str
    output_name: str
    created_at: str
    payload: Payload


__all__ = [
    "ExecutionOutputSnapshot",
]
