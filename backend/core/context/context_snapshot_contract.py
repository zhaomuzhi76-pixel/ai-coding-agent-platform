from __future__ import annotations

from typing import TypedDict


class ContextSnapshot(
    TypedDict,
):
    """
    Base context snapshot contract.

    Responsibility:

        - define the minimal context snapshot structure
    """

    name: str
    version: str
    responsibility: tuple[str, ...]
    ready: bool


__all__ = [
    "ContextSnapshot",
]
