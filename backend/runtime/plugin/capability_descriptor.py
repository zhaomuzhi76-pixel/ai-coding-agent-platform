from __future__ import annotations


from dataclasses import dataclass



@dataclass(
    frozen=True,
)
class RuntimeCapabilityDescriptor:
    """
    Capability declaration from plugin manifest.


    Responsibility:

        - describe plugin capability metadata
        - provide capability identity


    Not Responsible:

        - loading implementation
        - lifecycle management
        - execution
    """


    category: str

    name: str

    version: str = "1.0"

    entry: str = ""



    def __post_init__(
        self,
    ) -> None:

        if not self.category:
            raise ValueError(
                "capability category required"
            )


        if not self.name:
            raise ValueError(
                "capability name required"
            )



    def key(
        self,
    ) -> str:

        return (
            f"{self.category}.{self.name}"
        )



    def ready(
        self,
    ) -> bool:

        return bool(
            self.category
            and self.name
            and self.entry
        )



    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "category": self.category,
            "name": self.name,
            "version": self.version,
            "entry": self.entry,
            "key": self.key(),
            "ready": self.ready(),
        }



__all__ = [
    "RuntimeCapabilityDescriptor",
]
