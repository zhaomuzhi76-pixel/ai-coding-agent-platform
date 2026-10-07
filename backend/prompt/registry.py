"""
=========================================================

Prompt Registry

Responsibility:

    - Register prompt templates
    - Lookup prompt templates

Not responsible:

    - Load prompt files
    - Render prompt
    - Cache
    - Prompt execution

=========================================================
"""

from __future__ import annotations

from typing import Dict, List

from backend.prompt.models import (
    PromptTemplate,
)


class PromptRegistry:
    """
    Prompt registry.
    """

    def __init__(self):
        self._prompts: Dict[
            str,
            PromptTemplate,
        ] = {}

    def register(
        self,
        prompt: PromptTemplate,
    ) -> None:
        """
        Register a prompt.
        """

        self._prompts[
            prompt.name
        ] = prompt

    def unregister(
        self,
        name: str,
    ) -> None:
        """
        Remove a prompt.
        """

        self._prompts.pop(
            name,
            None,
        )

    def get(
        self,
        name: str,
    ) -> PromptTemplate:
        """
        Get prompt.
        """

        if name not in self._prompts:
            raise KeyError(
                f"Prompt not registered: {name}"
            )

        return self._prompts[name]

    def exists(
        self,
        name: str,
    ) -> bool:
        return name in self._prompts

    def list(
        self,
    ) -> List[str]:
        return sorted(
            self._prompts.keys()
        )

    def clear(
        self,
    ) -> None:
        self._prompts.clear()


prompt_registry = PromptRegistry()


__all__ = [
    "PromptRegistry",
    "prompt_registry",
]
