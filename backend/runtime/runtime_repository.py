"""
Runtime Repository Contract

Responsibility:

    - runtime entity persistence contract
    - runtime lifecycle storage boundary


Responsible:

    - create runtime
    - load runtime
    - delete runtime
    - persist runtime state
    - persist runtime events
    - persist runtime results


Not Responsible:

    - execution lifecycle
    - DAG scheduling
    - executor dispatch
    - recovery decision
    - database implementation
"""

from __future__ import annotations


from typing import Protocol


from backend.runtime.runtime_model import (
    RuntimeInstance,
)


class RuntimeRepository(
    Protocol,
):

    VERSION = "1.0"


    async def create_runtime(
        self,
        runtime: RuntimeInstance,
    ) -> None:
        ...


    async def get_runtime(
        self,
        runtime_id: str,
    ) -> RuntimeInstance | None:
        ...


    async def delete_runtime(
        self,
        runtime_id: str,
    ) -> bool:
        ...


    async def save_event(
        self,
        runtime_id: str,
        event: dict,
    ) -> None:
        ...


    async def get_events(
        self,
        runtime_id: str,
    ) -> list[dict]:
        ...


    async def save_result(
        self,
        runtime_id: str,
        result: dict,
    ) -> None:
        ...


    async def get_result(
        self,
        runtime_id: str,
    ) -> dict | None:
        ...


    async def save_state(
        self,
        runtime_id: str,
        state: dict,
    ) -> None:
        ...


    async def get_state(
        self,
        runtime_id: str,
    ) -> dict | None:
        ...


__all__ = [
    "RuntimeRepository",
]
