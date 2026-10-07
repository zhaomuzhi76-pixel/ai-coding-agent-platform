from __future__ import annotations


from dataclasses import dataclass



@dataclass(frozen=True)
class RuntimePluginDependency:
    """
    Runtime plugin dependency declaration.


    Responsibility:

        - describe one plugin dependency


    Not Responsible:

        - dependency loading
        - version resolving
        - plugin lifecycle
    """


    capability: str

    version: str = ">=1.0"



    def ready(
        self,
    ) -> bool:

        return bool(
            self.capability
        )



    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "capability":
                self.capability,

            "version":
                self.version,

            "ready":
                self.ready(),
        }



class RuntimePluginDependencySet:
    """
    Runtime plugin dependency collection.


    Responsibility:

        - manage plugin dependency declarations
        - validate dependency availability


    Not Responsible:

        - plugin loading
        - capability execution
    """


    VERSION = "1.0"



    def __init__(
        self,
        dependencies: list[
            RuntimePluginDependency
        ] | None = None,
    ) -> None:

        self.dependencies = []

        for dependency in (
            dependencies or []
        ):
            self.add(
                dependency
            )



    def add(
        self,
        dependency: RuntimePluginDependency,
    ) -> None:

        if not isinstance(
            dependency,
            RuntimePluginDependency,
        ):
            raise TypeError(
                "invalid plugin dependency"
            )

        self.dependencies.append(
            dependency
        )



    def validate(
        self,
        capabilities: set[str],
    ) -> bool:

        return all(
            dependency.capability
            in capabilities
            for dependency
            in self.dependencies
        )



    def ready(
        self,
    ) -> bool:

        return all(
            dependency.ready()
            for dependency
            in self.dependencies
        )



    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name":
                self.__class__.__name__,

            "version":
                self.VERSION,

            "dependencies":
                tuple(
                    dependency.capability
                    for dependency
                    in self.dependencies
                ),

            "ready":
                self.ready(),
        }



__all__ = [
    "RuntimePluginDependency",
    "RuntimePluginDependencySet",
]
