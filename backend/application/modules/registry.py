from __future__ import annotations
from backend.core.observability.silent import swallow

from backend.application.modules.contracts import (
    ApplicationModuleProtocol,
)


class ApplicationModuleRegistry:
    """
    Application module registry boundary.

    Owns:
        - module registration
        - module lookup
        - module lifecycle delegation
        - module readiness inspection

    Does not own:
        - module construction
        - module implementation
    """

    VERSION = "3.2"

    def __init__(
        self,
        modules: tuple[
            ApplicationModuleProtocol,
            ...,
        ],
    ) -> None:
        self._modules: dict[
            str,
            ApplicationModuleProtocol,
        ] = {}
        self._started = False

        for module in modules:
            self.register(module)

    def register(
        self,
        module: ApplicationModuleProtocol,
    ) -> None:
        if not isinstance(
            module,
            ApplicationModuleProtocol,
        ):
            raise TypeError(
                "invalid application module"
            )

        if module.name in self._modules:
            raise RuntimeError(
                f"duplicate module: {module.name}"
            )

        self._modules[module.name] = module

    def resolve(
        self,
        name: str,
    ) -> ApplicationModuleProtocol:
        try:
            return self._modules[name]
        except KeyError as exc:
            raise KeyError(
                f"application module not found: {name}"
            ) from exc

    def names(
        self,
    ) -> tuple[str, ...]:
        return tuple(self._modules.keys())

    def created(
        self,
    ) -> bool:
        return all(
            isinstance(
                module,
                ApplicationModuleProtocol,
            )
            for module in self._modules.values()
        )

    def start(
        self,
    ) -> None:
        if self._started:
            raise RuntimeError(
                "application module registry already started"
            )

        started: list[ApplicationModuleProtocol] = []

        try:
            for module in self._modules.values():
                module.start()
                started.append(module)
        except Exception:
            for module in reversed(started):
                try:
                    module.stop()
                except Exception as e:
                    swallow("application.modules.registry:107", e)
            self._started = False
            raise

        self._started = True

    def stop(
        self,
    ) -> None:
        if not self._started:
            return

        try:
            for module in reversed(
                tuple(self._modules.values())
            ):
                module.stop()
        finally:
            self._started = False

    def build(
        self,
        context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        active_context = (
            {}
            if context is None
            else dict(context)
        )
        result: dict[str, object] = {}

        for module in self._modules.values():
            built = module.build(
                active_context
            )

            if not isinstance(
                built,
                dict,
            ):
                raise TypeError(
                    "application module build result invalid"
                )

            result.update(built)

        return result

    def ready(
        self,
    ) -> bool:
        return (
            self._started
            and all(
                module.ready()
                for module in self._modules.values()
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "started": self._started,
            "ready": self.ready(),
            "modules": [
                module.dump()
                for module in self._modules.values()
            ],
        }


__all__ = [
    "ApplicationModuleRegistry",
]
