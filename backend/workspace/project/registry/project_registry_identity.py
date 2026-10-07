from __future__ import annotations

from pathlib import Path


class ProjectRegistryIdentity:
    """
    Registry-local identity normalization boundary.

    Owns:
        - project-id validation
        - canonical root normalization

    Does not own:
        - project registration
        - project lookup
        - project lifecycle
        - workspace runtime
        - persistence
    """

    VERSION = "1.0"

    @staticmethod
    def normalize_id(
        project_id: str,
    ) -> str:
        if not isinstance(
            project_id,
            str,
        ):
            raise TypeError(
                "project_id must str"
            )

        value = project_id.strip()

        if not value:
            raise ValueError(
                "project_id required"
            )

        return value

    @staticmethod
    def canonical_root(
        root_path: str,
    ) -> str:
        if not isinstance(
            root_path,
            str,
        ):
            raise TypeError(
                "root_path must str"
            )

        value = root_path.strip()

        if not value:
            raise ValueError(
                "root_path required"
            )

        return str(
            Path(value)
            .expanduser()
            .resolve()
        )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProjectRegistryIdentity",
]
