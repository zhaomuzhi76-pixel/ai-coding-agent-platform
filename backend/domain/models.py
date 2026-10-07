"""Domain data models (domain-agnostic)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class DomainEntity:
    entity_type: str
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "name": self.name,
            "attributes": dict(self.attributes),
        }


@dataclass
class DomainTerm:
    term_type: str
    name: str
    definition: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "term_type": self.term_type,
            "name": self.name,
            "definition": self.definition,
            "attributes": dict(self.attributes),
        }
