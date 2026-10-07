from __future__ import annotations

from backend.workspace.project.registry.project_registry_contract import (
    ProjectRegistryContract,
)


class ApplicationProjectSessionComposition:
    """
    Application facade over the assembly-owned project/session graph.

    Owns:
        - application-facing composition access
        - assembled component projection

    Does not own:
        - workspace construction
        - project/session construction
        - registry construction
        - runtime construction
        - lifecycle implementation
    """

    VERSION = "3.0"

    REQUIRED_KEYS = (
        "project_registry",
        "session_registry",
        "session_registry_binding",
        "session_lifecycle",
        "session_service",
        "session_model_factory",
        "session_runtime_factory",
        "project_factory",
        "project_runtime_factory",
    )

    def __init__(
        self,
        *,
        assembly: dict[str, object],
    ) -> None:
        if not isinstance(assembly, dict):
            raise TypeError(
                "project session assembly must dict"
            )

        missing = tuple(
            key
            for key in self.REQUIRED_KEYS
            if assembly.get(key) is None
        )
        if missing:
            raise RuntimeError(
                "project session assembly missing: "
                + ", ".join(missing)
            )

        self._assembly = dict(assembly)

    def create(self) -> dict[str, object]:
        return dict(self._assembly)

    def current(self) -> dict[str, object]:
        return dict(self._assembly)

    def project_registry(self) -> ProjectRegistryContract:
        return self._require_typed(
            "project_registry",
            ProjectRegistryContract,
        )

    def session_registry(self) -> object:
        return self._require("session_registry")

    def session_binding(self) -> object:
        return self._require(
            "session_registry_binding"
        )

    def lifecycle(self) -> object:
        return self._require(
            "session_lifecycle"
        )

    def service(self) -> object:
        return self._require(
            "session_service"
        )

    def session_factory(self) -> object:
        return self._require(
            "session_model_factory"
        )

    def runtime_factory(self) -> object:
        return self._require(
            "session_runtime_factory"
        )

    def ready(self) -> bool:
        if any(
            self._assembly.get(key) is None
            for key in self.REQUIRED_KEYS
        ):
            return False

        return all(
            self._component_ready(
                self._assembly[key]
            )
            for key in self.REQUIRED_KEYS
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "components": tuple(
                self._assembly.keys()
            ),
        }

    def _require(self, name: str) -> object:
        component = self._assembly.get(name)
        if component is None:
            raise RuntimeError(
                f"composition component unavailable: {name}"
            )
        return component

    def _require_typed(
        self,
        name: str,
        contract,
    ):
        component = self._require(name)
        if not isinstance(component, contract):
            raise TypeError(
                f"{name} contract violation"
            )
        return component

    @staticmethod
    def _component_ready(
        component: object,
    ) -> bool:
        checker = getattr(
            component,
            "ready",
            None,
        )
        return bool(
            callable(checker)
            and checker()
        )


__all__ = [
    "ApplicationProjectSessionComposition",
]
