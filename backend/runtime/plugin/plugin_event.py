from __future__ import annotations


from enum import Enum
from typing import Callable, Any



class RuntimePluginEventType(
    Enum,
):
    """
    Runtime plugin event types.
    """


    INSTALL = "install"

    ENABLE = "enable"

    DISABLE = "disable"

    UNLOAD = "unload"



class RuntimePluginEvent:
    """
    Runtime plugin event.


    Responsibility:

        - describe plugin event


    Not Responsible:

        - dispatch
        - lifecycle transition
    """


    VERSION = "1.0"



    def __init__(
        self,
        event_type: RuntimePluginEventType,
        plugin_name: str,
        payload: dict[str, Any] | None = None,
    ) -> None:

        if not plugin_name:
            raise ValueError(
                "plugin name required"
            )


        self.event_type = event_type

        self.plugin_name = plugin_name

        self.payload = (
            payload
            or {}
        )



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

            "event":
                self.event_type.value,

            "plugin":
                self.plugin_name,

            "ready":
                self.ready(),
        }



class RuntimePluginEventDispatcher:
    """
    Runtime plugin event dispatcher.


    Responsibility:

        - register handlers
        - dispatch events


    Not Responsible:

        - plugin lifecycle
        - plugin execution
    """


    VERSION = "1.0"



    def __init__(
        self,
    ) -> None:

        self.handlers = {}



    def register(
        self,
        event_type: RuntimePluginEventType,
        handler: Callable[
            [RuntimePluginEvent],
            Any,
        ],
    ) -> None:

        if not callable(
            handler
        ):
            raise TypeError(
                "handler required"
            )


        self.handlers.setdefault(
            event_type,
            [],
        ).append(
            handler
        )



    def dispatch(
        self,
        event: RuntimePluginEvent,
    ) -> list[Any]:

        results = []

        for handler in (
            self.handlers.get(
                event.event_type,
                [],
            )
        ):
            results.append(
                handler(event)
            )

        return results



    def ready(
        self,
    ) -> bool:

        return True



    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name":
                self.__class__.__name__,

            "version":
                self.VERSION,

            "events":
                tuple(
                    key.value
                    for key
                    in self.handlers
                ),

            "ready":
                self.ready(),
        }



__all__ = [
    "RuntimePluginEventType",
    "RuntimePluginEvent",
    "RuntimePluginEventDispatcher",
]
