"""
=========================================================

Prompt Composer

Responsibility:

    - Compose multiple prompt sections
    - Produce final prompt for LLM

Not responsible:

    - Rendering variables
    - Loading templates
    - Calling LLM

=========================================================
"""

from __future__ import annotations


class PromptComposer:
    """
    Compose multiple prompt sections.
    """

    def compose(
        self,
        *sections: str,
    ) -> str:
        parts = []

        for section in sections:
            if not section:
                continue

            text = section.strip()

            if text:
                parts.append(text)

        return "\n\n".join(parts)


__all__ = [
    "PromptComposer",
]
