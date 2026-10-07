from __future__ import annotations

from backend.application.capability.manager_factory import (
    ApplicationCapabilityManagerFactory,
)
from backend.application.capability.registry import (
    ApplicationCapabilityRegistry,
)
from backend.application.capability.registry_factory import (
    ApplicationCapabilityRegistryFactory,
)
from backend.application.modules.contracts import (
    ApplicationModuleProtocol,
)
from backend.application.modules.infrastructure import (
    ApplicationInfrastructureModule,
)
from backend.application.modules.infrastructure_composition_factory import (
    ApplicationInfrastructureCompositionFactory,
)
from backend.application.modules.registry import (
    ApplicationModuleRegistry,
)
from backend.application.modules.tools import (
    ApplicationToolModule,
)
from backend.application.capability.tool_composition_factory import (
    ApplicationToolCompositionFactory,
)


class ApplicationModuleRegistryFactory:
    """
    Application module registry assembly boundary.

    Owns:
        - module construction
        - module validation
        - registry assembly

    Does not own:
        - module implementation
        - runtime execution
    """

    VERSION = "3.0"

    def __init__(
        self,
        *,
        runtime_construction: object | None = None,
        capability_registry: ApplicationCapabilityRegistry | None = None,
    ) -> None:
        self.runtime_construction = (
            runtime_construction
        )

        self.capability_registry = (
            capability_registry
            if capability_registry is not None
            else ApplicationCapabilityRegistryFactory().create()
        )

        self.runtime_construction = runtime_construction

        if not isinstance(
            self.capability_registry,
            ApplicationCapabilityRegistry,
        ):
            raise TypeError(
                "invalid capability registry"
            )

    def create(
        self,
    ) -> ApplicationModuleRegistry:

        capability_manager = (
            ApplicationCapabilityManagerFactory()
            .create(
                registry=self.capability_registry,
            )
        )

        infrastructure_composition = (
            ApplicationInfrastructureCompositionFactory()
            .create(
                runtime_construction=(
                    self.runtime_construction
                ),
            )
        )

        tool_composition = (
            ApplicationToolCompositionFactory()
            .create(
                manager=capability_manager,
            )
        )

        modules: tuple[
            ApplicationModuleProtocol,
            ...,
        ] = (
            ApplicationInfrastructureModule(
                infrastructure_composition,
            ),
            ApplicationToolModule(
                tool_composition,
            ),
        )

        self._validate_modules(
            modules,
        )

        registry = ApplicationModuleRegistry(
            modules=modules,
        )
        if not registry.created():
            raise RuntimeError(
                "application module registry construction failed"
            )

        return registry

    def ready(
        self,
    ) -> bool:
        return self.capability_registry.ready()

    @staticmethod
    def _validate_modules(
        modules: tuple[
            ApplicationModuleProtocol,
            ...,
        ],
    ) -> None:

        names: list[str] = []

        for module in modules:
            if not isinstance(
                module,
                ApplicationModuleProtocol,
            ):
                raise TypeError(
                    "invalid application module"
                )

            names.append(
                module.name,
            )

        if len(names) != len(set(names)):
            raise RuntimeError(
                "duplicate application module name"
            )


__all__ = [
    "ApplicationModuleRegistryFactory",
]
