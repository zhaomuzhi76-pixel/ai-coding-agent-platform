"""
=========================================================

Prompt Manager

Responsibility:

    - Unified Prompt Engine entry
    - Load, register and render prompts

Not responsible:

    - Prompt execution
    - LLM invocation
    - Prompt caching
    - Prompt hot reload

=========================================================
"""

from __future__ import annotations

from pathlib import Path

from backend.prompt.loader import (
    PromptLoader,
)

from backend.prompt.registry import (
    PromptRegistry,
)

from backend.prompt.renderer import (
    PromptRenderer,
)


class PromptManager:
    """
    Unified Prompt Engine.
    """

    def __init__(
        self,
        template_dir: str | Path | None = None,
    ):
        self.loader = PromptLoader(
            template_dir
        )

        self.registry = PromptRegistry()

        self.renderer = PromptRenderer()

    def load(
        self,
        prompt_name: str,
    ):
        if self.registry.exists(
            prompt_name
        ):
            return self.registry.get(
                prompt_name
            )

        prompt = self.loader.load(
            prompt_name
        )

        self.registry.register(
            prompt
        )

        return prompt

    def render(
        self,
        prompt_name: str,
        **kwargs,
    ) -> str:
        """
        Load and render prompt.
        """

        prompt = self.load(
            prompt_name
        )

        return self.renderer.render(
            prompt.template,
            **kwargs,
        )

    def exists(
        self,
        prompt_name: str,
    ) -> bool:
        return self.registry.exists(
            prompt_name
        )

    def clear(
        self,
    ):
        self.registry.clear()


prompt_manager = PromptManager()


__all__ = [
    "PromptManager",
    "prompt_manager",
]
