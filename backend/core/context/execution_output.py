from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Final
from uuid import uuid4

from backend.core.context.execution_output_contract import (
    ExecutionOutputSnapshot,
)
from backend.core.context.execution_output_validator import (
    ExecutionOutputValidator,
)
from backend.core.context.output_payload_protocol import (
    OutputPayloadProtocol,
)
from backend.core.contracts.payload import Payload


_CST: Final = timezone(
    timedelta(hours=8),
)


class ExecutionOutput:
    """Immutable execution output entity."""

    VERSION = "6.0"

    RESPONSIBILITY = (
        "execution_output_entity",
    )

    def __init__(
        self,
        name: str,
        payload: OutputPayloadProtocol,
    ) -> None:
        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "output name must be str"
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "output name required"
            )

        if not isinstance(
            payload,
            OutputPayloadProtocol,
        ):
            raise TypeError(
                "payload must implement OutputPayloadProtocol"
            )

        payload_snapshot = payload.dump()

        ExecutionOutputValidator.validate_snapshot(
            payload_snapshot
        )

        self._output_id = (
            f"out_{uuid4().hex}"
        )

        self._name = name

        self._payload_snapshot: Payload = (
            deepcopy(
                payload_snapshot
            )
        )

        self._created_at = datetime.now(
            _CST
        ).isoformat()

    @property
    def output_id(
        self,
    ) -> str:
        return self._output_id

    @property
    def name(
        self,
    ) -> str:
        return self._name

    @property
    def payload_snapshot(
        self,
    ) -> Payload:
        return deepcopy(
            self._payload_snapshot
        )

    @property
    def created_at(
        self,
    ) -> str:
        return self._created_at

    def ready(
        self,
    ) -> bool:
        return bool(
            self._output_id
            and self._name
            and self._created_at
        )

    def dump(
        self,
    ) -> ExecutionOutputSnapshot:
        return {
            "name": "ExecutionOutput",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "output_id": self.output_id,
            "output_name": self.name,
            "created_at": self.created_at,
            "payload": self.payload_snapshot,
        }


__all__ = [
    "ExecutionOutput",
]
