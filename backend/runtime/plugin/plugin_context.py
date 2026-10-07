from __future__ import annotations


from dataclasses import dataclass, field
from typing import Any



@dataclass
class RuntimePluginContext:
    """
    Runtime plugin execution context.


    Responsibility:

        - provide plugin runtime environment
        - expose runtime metadata
        - provide capability/service lookup


    Not Responsible:

        - plugin lifecycle
        - plugin loading
        - plugin business logic
    """


    VERSION = "1.0"


    plugin_name: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    services: dict[str, Any] = field(
        default_factory=dict
    )

    capabilities: dict[str, Any] = field(
        default_factory=dict
    )



    def get_service(
        self,
        name: str,
    ) -> Any:

        if not name:
            raise ValueError(
                "service name required"
            )

        return self.services.get(
            name
        )



    def get_capability(
        self,
        name: str,
    ) -> Any:

        if not name:
            raise ValueError(
                "capability name required"
            )

        return self.capabilities.get(
            name
        )



    def register_service(
        self,
        name: str,
        service: Any,
    ) -> None:

        if not name:
            raise ValueError(
                "service name required"
            )

        self.services[name] = service



    def register_capability(
        self,
        name: str,
        capability: Any,
    ) -> None:

        if not name:
            raise ValueError(
                "capability name required"
            )

        self.capabilities[name] = capability



    def ready(
        self,
    ) -> bool:

        return bool(
            self.plugin_name
        )



    def dump(
        self,
    ) -> dict[str, object]:

        return {

            "name":
                self.__class__.__name__,


            "version":
                self.VERSION,


            "plugin_name":
                self.plugin_name,


            "services":
                tuple(
                    self.services.keys()
                ),


            "capabilities":
                tuple(
                    self.capabilities.keys()
                ),


            "ready":
                self.ready(),
        }



__all__ = [
    "RuntimePluginContext",
]
