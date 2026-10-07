from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.application.project.project_registration_contract import (
    ApplicationProjectRegistrationContract,
)


@runtime_checkable
class ApplicationProjectRemovalContract(
    Protocol,
):
    """
    Application-facing project-removal contract.

    API/server layers consume this contract and never depend on the
    concrete removal implementation.
    """

    registration: ApplicationProjectRegistrationContract
    remove_count: int
    rejected_count: int

    def remove(
        self,
        project_id: str,
    ) -> object:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "ApplicationProjectRemovalContract",
]
