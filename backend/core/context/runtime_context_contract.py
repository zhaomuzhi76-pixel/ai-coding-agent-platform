from __future__ import annotations

from typing import TypedDict

from backend.core.context.context_identity_contract import (
    ContextIdentitySnapshot,
)
from backend.core.context.context_metadata_contract import (
    ContextMetadataSnapshot,
)
from backend.core.context.execution_storage_contract import (
    ExecutionContextStorageSnapshot,
)


class RuntimeContextSnapshot(
    TypedDict,
):
    """
    Runtime context snapshot contract.

    Responsibility:
        - define runtime context snapshot structure

    Not Responsible:
        - runtime lifecycle state
        - runtime lifecycle management
        - execution state management
        - persistence
    """

    name: str
    version: str
    responsibility: tuple[str, ...]
    ready: bool
    identity: ContextIdentitySnapshot
    storage: ExecutionContextStorageSnapshot
    metadata: ContextMetadataSnapshot


__all__ = [
    "RuntimeContextSnapshot",
]
