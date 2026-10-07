from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class IdentityContextProtocol(
    Protocol,
):
    """
    Context identity capability contract.

    Responsibility:

        - expose runtime identity fields
    """

    @property
    def request_id(
        self,
    ) -> str:
        ...

    @property
    def trace_id(
        self,
    ) -> str:
        ...

    @property
    def workspace_id(
        self,
    ) -> str | None:
        ...

    @property
    def user_id(
        self,
    ) -> str | None:
        ...

    @property
    def created_at(
        self,
    ) -> str:
        ...


__all__ = [
    "IdentityContextProtocol",
]
