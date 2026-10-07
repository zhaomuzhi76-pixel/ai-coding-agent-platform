"""
=========================================================

Prompt Models

Responsibility:

    - Define Prompt data model
    - Store prompt metadata
    - expose stable model contract

Not responsible:

    - Load template
    - Render variables
    - Read files
    - Manage registry
    - Execute prompts

=========================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class PromptTemplate:
    """
    First-class prompt template model.

    The model owns prompt identity and metadata only.
    Template loading and rendering remain external responsibilities.
    """

    name: str
    template: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    tags: list[str] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    def ready(self) -> bool:
        """
        Return whether the prompt model is structurally usable.
        """
        return bool(
            self.name.strip()
            and self.version.strip()
            and isinstance(self.template, str)
        )

    def dump(self) -> dict[str, Any]:
        """
        Return the canonical serializable prompt model.
        """
        return asdict(self)


__all__ = [
    "PromptTemplate",
]
