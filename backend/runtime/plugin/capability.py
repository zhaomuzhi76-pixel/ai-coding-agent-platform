from __future__ import annotations


from dataclasses import dataclass



@dataclass(
    frozen=True,
)
class RuntimeCapability:
    """
    Runtime capability contract.


    Responsibility:

        - define extension capability identity
        - describe provider ownership


    Not Responsible:

        - component lifecycle
        - execution logic
        - business implementation
    """


    name: str

    category: str

    version: str = "1.0"



    def __post_init__(
        self,
    ) -> None:

        if not self.name:
            raise ValueError(
                "capability name required"
            )

        if not self.category:
            raise ValueError(
                "capability category required"
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
            self.name
            and self.category
        )



    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name": self.name,
            "category": self.category,
            "version": self.version,
            "key": self.key(),
            "ready": self.ready(),
        }



__all__ = [
    "RuntimeCapability",
]
