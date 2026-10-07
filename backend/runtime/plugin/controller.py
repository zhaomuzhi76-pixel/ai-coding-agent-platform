from __future__ import annotations


from backend.runtime.plugin.operations import (
    RuntimePluginOperations,
)



class RuntimePluginController:
    """
    Plugin management facade.

    Responsibility:

        - expose plugin management API
        - coordinate operations


    Not Responsible:

        - plugin discovery
        - plugin loading
        - capability execution
        - business logic
    """


    VERSION = "1.0"



    def __init__(
        self,
        operations: RuntimePluginOperations,
    ) -> None:


        if operations is None:
            raise ValueError(
                "operations required"
            )


        self.operations = operations



    def register(
        self,
        plugin_name: str,
    ) -> None:

        self.operations.register(
            plugin_name
        )



    def install(
        self,
        plugin_name: str,
    ) -> None:

        self.operations.install(
            plugin_name
        )



    def enable(
        self,
        plugin_name: str,
    ) -> None:

        self.operations.enable(
            plugin_name
        )



    def disable(
        self,
        plugin_name: str,
    ) -> None:

        self.operations.disable(
            plugin_name
        )



    def unload(
        self,
        plugin_name: str,
    ) -> None:

        self.operations.unload(
            plugin_name
        )



    def ready(
        self,
    ) -> bool:

        return self.operations.ready()



    def dump(
        self,
    ) -> dict[str, object]:

        return {

            "name":
                self.__class__.__name__,

            "version":
                self.VERSION,

            "operations":
                self.operations.dump(),

            "ready":
                self.ready(),
        }



__all__ = [
    "RuntimePluginController",
]
