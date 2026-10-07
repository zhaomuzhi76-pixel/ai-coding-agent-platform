from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ApplicationProjectResultContract(
    Protocol,
):
    """
    Application-facing project result contract.

    The API layer consumes only this stable projection and does not
    depend on the workspace ProjectModel implementation.
    """

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "ApplicationProjectResultContract",
]
