from __future__ import annotations

import ast
from difflib import SequenceMatcher


class CodeModificationProposalGuard:
    """
    Safety gate for LLM-generated source replacements.

    Owns:
        - replacement sanity validation
        - source similarity protection
        - syntax validation

    Does not own:
        - proposal generation
        - patch execution
        - file persistence
        - runtime execution
    """

    VERSION = "1.0"
    DEFAULT_SIMILARITY = 0.60

    def validate(
        self,
        *,
        source: str,
        replacement: str,
        allow_large_change: bool = False,
    ) -> None:
        if not isinstance(source, str):
            raise TypeError("source must str")

        if not isinstance(replacement, str):
            raise TypeError("replacement must str")

        if not replacement.strip():
            raise ValueError("empty replacement")

        if source == replacement:
            raise ValueError("no-op replacement")

        self._syntax(replacement)

        if allow_large_change:
            return

        similarity = SequenceMatcher(
            None,
            source,
            replacement,
        ).ratio()

        if similarity < self.DEFAULT_SIMILARITY:
            raise ValueError(
                "replacement differs too substantially "
                "from source"
            )

    @staticmethod
    def _syntax(source: str) -> None:
        try:
            ast.parse(source)
        except SyntaxError as error:
            raise ValueError(
                f"replacement syntax invalid: {error}"
            ) from error

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "similarity_threshold": self.DEFAULT_SIMILARITY,
        }


__all__ = [
    "CodeModificationProposalGuard",
]
