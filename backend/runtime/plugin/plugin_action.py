from __future__ import annotations


from dataclasses import dataclass
from typing import Callable



@dataclass(
    frozen=True,
)
class RuntimePluginAction:

    """
    Plugin action descriptor.

    Responsibility:

        - describe plugin operation


    Not Responsible:

        - execute business logic
        - plugin lifecycle
        - capability loading
    """

    name: str

    handler: Callable



class RuntimePluginActionRegistry:
    """
    Plugin action registry.

    Responsibility:

        - register plugin actions
        - resolve actions


    Not Responsible:

        - action execution
        - plugin management
    """


    VERSION = "1.0"



    def __init__(
        self,
    ) -> None:

        self._actions: dict[
            str,
            RuntimePluginAction,
        ] = {}



    def register(
        self,
        action: RuntimePluginAction,
    ) -> None:

        if action is None:
            raise ValueError(
                "action required"
            )

        if action.name in self._actions:
            raise ValueError(
                "action already exists"
            )

        self._actions[
            action.name
        ] = action



    def resolve(
        self,
        name: str,
    ) -> RuntimePluginAction:

        if name not in self._actions:
            raise KeyError(
                "action not found"
            )

        return self._actions[
            name
        ]



    def exists(
        self,
        name: str,
    ) -> bool:

        return (
            name in self._actions
        )



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

            "actions":
                tuple(
                    self._actions.keys()
                ),

            "ready":
                self.ready(),
        }



__all__ = [
    "RuntimePluginAction",
    "RuntimePluginActionRegistry",
]
