"""
=========================================================

Prompt Loader

Responsibility:

    - Load prompt template from disk

Not responsible:

    - Render variables
    - Registry
    - Cache
    - Prompt management

=========================================================
"""

from __future__ import annotations

from pathlib import Path

from backend.prompt.models import (
    PromptTemplate,
)


class PromptLoader:
    """
    Load prompt templates from templates directory.
    """

    def __init__(
        self,
        template_dir: str | Path | None = None,
    ):
        if template_dir is None:
            template_dir = (
                Path(__file__).parent
                / "templates"
            )

        self.template_dir = Path(template_dir)

    def load(
        self,
        name: str,
    ) -> PromptTemplate:
        """
        Load a prompt template.
        """

        path = self.template_dir / f"{name}.md"

        if not path.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {path}"
            )

        content = path.read_text(
            encoding="utf-8"
        )

        return PromptTemplate(
            name=name,
            template=content,
        )


__all__ = [
    "PromptLoader",
]
