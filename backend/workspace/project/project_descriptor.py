from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectDescriptor:
    """
    Immutable logical programming-project identity.

    Owns:
        - project identity
        - project name
        - canonical project root
        - optional workspace identity

    Does not own:
        - filesystem access
        - workspace operations
        - indexing
        - persistence
        - execution
        - agent orchestration
    """

    project_id: str
    name: str
    root_path: str
    workspace_id: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "project_id",
            "name",
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

        if self.workspace_id is not None:
            if not isinstance(
                self.workspace_id,
                str,
            ):
                raise TypeError(
                    "workspace_id must str or None"
                )

            if not self.workspace_id.strip():
                raise ValueError(
                    "workspace_id cannot be empty"
                )

    def ready(self) -> bool:
        return bool(
            self.project_id
            and self.name
            and self.root_path
        )

    def dump(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "root_path": self.root_path,
            "workspace_id": self.workspace_id,
            "ready": self.ready(),
        }


__all__ = [
    "ProjectDescriptor",
]
