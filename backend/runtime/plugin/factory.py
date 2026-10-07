from __future__ import annotations


from inspect import isclass


class RuntimeComponentFactory:
    """
    Runtime plugin component factory.


    Responsibility:

        - resolve plugin component
        - instantiate extension


    Not Responsible:

        - business capability
        - plugin discovery
        - lifecycle
    """


    VERSION = "2.0"


    def __init__(
        self,
        registry,
    ) -> None:

        if registry is None:
            raise ValueError(
                "plugin registry required"
            )

        self.registry = registry



    def create(
        self,
        category: str,
        name: str,
        *args,
        **kwargs,
    ):

        component = self.registry.resolve(
            category,
            name,
        )

        return self._create(
            component,
            *args,
            **kwargs,
        )



    def _create(
        self,
        component,
        *args,
        **kwargs,
    ):

        if isclass(component):
            return component(
                *args,
                **kwargs,
            )

        if callable(component):
            return component(
                *args,
                **kwargs,
            )

        return component



    def ready(
        self,
    ) -> bool:

        return self.registry.ready()



    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }



__all__ = [
    "RuntimeComponentFactory",
]
