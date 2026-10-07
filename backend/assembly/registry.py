from __future__ import annotations

from backend.assembly.contracts import (
    AssemblyModuleProtocol,
)


class AssemblyRegistry:
    """
    System assembly module registry.

    Readiness means registered modules satisfy the assembly
    contract and are structurally usable by the pipeline.
    It does not require business/startup execution to have
    happened already.
    """

    VERSION = "1.1"

    def __init__(self) -> None:
        self._modules: dict[
            str,
            AssemblyModuleProtocol,
        ] = {}

    def register(
        self,
        module: AssemblyModuleProtocol,
    ) -> None:
        if not isinstance(
            module,
            AssemblyModuleProtocol,
        ):
            raise TypeError(
                "invalid assembly module"
            )

        if module.name in self._modules:
            raise ValueError(
                f"assembly module already exists: {module.name}"
            )

        self._modules[module.name] = module

    def resolve(
        self,
        name: str,
    ) -> AssemblyModuleProtocol:
        try:
            return self._modules[name]
        except KeyError as error:
            raise LookupError(
                f"assembly module not found: {name}"
            ) from error

    def names(self) -> tuple[str, ...]:
        return tuple(self._modules)

    def ready(self) -> bool:
        for module in self._modules.values():
            if not isinstance(
                getattr(module, "name", None),
                str,
            ):
                return False

            if not module.name.strip():
                return False

            if not isinstance(
                getattr(module, "version", None),
                str,
            ):
                return False

            if not module.version.strip():
                return False

            if not callable(
                getattr(module, "build", None)
            ):
                return False

            if not callable(
                getattr(module, "ready", None)
            ):
                return False

            if not callable(
                getattr(module, "dump", None)
            ):
                return False

        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "modules": self.names(),
            "ready": self.ready(),
        }


__all__ = [
    "AssemblyRegistry",
]
