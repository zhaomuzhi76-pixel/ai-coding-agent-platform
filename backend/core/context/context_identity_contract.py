from __future__ import annotations

from typing import TypedDict

from backend.core.contracts.value import CoreValue


class ContextIdentitySnapshot(
    TypedDict,
):
    """
    Context identity snapshot contract.
    """

    name: str
    version: str
    responsibility: tuple[str, ...]
    ready: bool
    identity: dict[str, CoreValue]


__all__ = [
    "ContextIdentitySnapshot",
]
