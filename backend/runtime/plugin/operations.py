from __future__ import annotations


from backend.runtime.plugin.plugin_lifecycle import (
    RuntimePluginLifecycle,
)


from backend.runtime.plugin.plugin_action import (
    RuntimePluginActionRegistry,
)



class RuntimePluginOperations:
    """
    Plugin operation orchestration boundary.

    Responsibility:

        - coordinate plugin operations
        - expose lifecycle operations


    Not Responsible:

        - discovery
        - loading
        - capability execution
        - business logic
    """


    VERSION = "1.0"



    def __init__(
        self,
        lifecycle: RuntimePluginLifecycle,
        action_registry: RuntimePluginActionRegistry,
    ) -> None:


        if lifecycle is None:
            raise ValueError(
                "lifecycle required"
            )


        if action_registry is None:
            raise ValueError(
                "action registry required"
            )


        self.lifecycle = lifecycle

        self.action_registry = (
            action_registry
        )



    def register(
        self,
        plugin_name: str,
    ) -> None:

        self.lifecycle.register(
            plugin_name
        )



    def install(
        self,
        plugin_name: str,
    ) -> None:

        self.lifecycle.install(
            plugin_name
        )



    def enable(
        self,
        plugin_name: str,
    ) -> None:

        self.lifecycle.enable(
            plugin_name
        )



    def disable(
        self,
        plugin_name: str,
    ) -> None:

        self.lifecycle.disable(
            plugin_name
        )



    def unload(
        self,
        plugin_name: str,
    ) -> None:

        self.lifecycle.unload(
            plugin_name
        )



    def ready(
        self,
    ) -> bool:

        return (
            self.lifecycle.ready()
            and
            self.action_registry.ready()
        )



    def dump(
        self,
    ) -> dict[str, object]:

        return {

            "name":
                self.__class__.__name__,

            "version":
                self.VERSION,

            "lifecycle":
                self.lifecycle.dump(),

            "actions":
                self.action_registry.dump(),

            "ready":
                self.ready(),
        }



__all__ = [
    "RuntimePluginOperations",
]
