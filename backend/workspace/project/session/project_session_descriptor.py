from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ProjectSessionDescriptor:
    """
    Immutable programming-project session identity descriptor.

    Owns:
        - session identity
        - project/workspace/runtime binding
        - canonical project root
        - session metadata

    Does not own:
        - lifecycle orchestration
        - persistence
        - execution
        - registry coordination
        - agent behavior
    """

    session_id: str
    project_id: str
    workspace_id: str | None
    runtime_id: str | None
    root_path: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        for field_name in (
            "session_id",
            "project_id",
            "root_path",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"{field_name} must str"
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} required"
                )

        for field_name in (
            "workspace_id",
            "runtime_id",
        ):
            value = getattr(
                self,
                field_name,
            )

            if value is None:
                continue

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"{field_name} must str or None"
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} cannot be empty"
                )

        canonical_root = str(
            Path(
                self.root_path
            ).expanduser().resolve()
        )

        object.__setattr__(
            self,
            "root_path",
            canonical_root,
        )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    def ready(
        self,
    ) -> bool:
        return bool(
            self.session_id
            and self.project_id
            and self.root_path
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "runtime_id": self.runtime_id,
            "root_path": self.root_path,
            "metadata": dict(
                self.metadata
            ),
            "ready": self.ready(),
        }


__all__ = [
    "ProjectSessionDescriptor",
]
