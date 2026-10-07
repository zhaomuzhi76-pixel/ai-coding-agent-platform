from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelDescriptor:
    id: str
    provider: str
    display_name: str
    context_window: int

    def to_wire(self, *, is_default: bool) -> dict:
        return {
            "id": self.id,
            "provider": self.provider,
            "displayName": self.display_name,
            "contextWindow": self.context_window,
            "isDefault": is_default,
        }
