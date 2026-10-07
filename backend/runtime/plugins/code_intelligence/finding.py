from __future__ import annotations

from backend.core.code_intelligence.finding_protocol import (
    CodeFindingProtocol,
)


class RuntimeCodeIntelligenceFinding(
    CodeFindingProtocol,
):
    """
    Runtime-owned canonical finding wrapper.

    Converts an implementation payload into the Core
    CodeFindingProtocol boundary without leaking implementation
    types into Core or Application.
    """

    VERSION = "1.0"

    def __init__(
        self,
        payload: object,
    ) -> None:
        if payload is None:
            raise ValueError(
                "finding payload required"
            )

        self.payload = payload

    def dump(
        self,
    ) -> dict[str, object]:
        if isinstance(
            self.payload,
            dict,
        ):
            return dict(
                self.payload
            )

        return {
            "value": self.payload,
        }


__all__ = [
    "RuntimeCodeIntelligenceFinding",
]
