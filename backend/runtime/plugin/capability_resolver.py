from __future__ import annotations


from backend.runtime.plugin.capability import (
    RuntimeCapability,
)


from backend.runtime.plugin.capability_registry import (
    RuntimeCapabilityRegistry,
)



class RuntimeCapabilityResolver:
    """
    Runtime capability resolver.


    Responsibility:

        - resolve capability implementation
        - hide registry details


    Not Responsible:

        - plugin loading
        - component lifecycle
        - business logic
    """


    VERSION = "1.0"



    def __init__(
        self,
        registry: RuntimeCapabilityRegistry,
    ) -> None:

        if registry is None:
            raise ValueError(
                "capability registry required"
            )

        self.registry = registry



    def resolve(
        self,
        category: str,
        name: str,
        version: str = "1.0",
    ) -> object:


        capability = RuntimeCapability(
            category=category,
            name=name,
            version=version,
        )


        return self.registry.resolve(
            capability,
            version,
        )



    def ready(
        self,
    ) -> bool:

        return self.registry.ready()



    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name":
                self.__class__.__name__,

            "version":
                self.VERSION,

            "ready":
                self.ready(),
        }



__all__ = [
    "RuntimeCapabilityResolver",
]
