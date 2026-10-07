from __future__ import annotations


class CodeModificationEdit:
    """
    Apply one exact source-text edit.

    Owns:
        - exact old-text matching
        - deterministic replacement construction

    Does not own:
        - LLM proposal generation
        - proposal parsing
        - safety policy
        - patch execution
    """

    VERSION = "1.0"

    def apply(
        self,
        *,
        source: str,
        old: str,
        new: str,
    ) -> str:
        if not isinstance(source, str):
            raise TypeError("source must str")

        if not isinstance(old, str) or not old:
            raise ValueError("old text required")

        if not isinstance(new, str):
            raise TypeError("new text must str")

        count = source.count(old)

        if count != 1:
            raise ValueError(
                f"old text must occur exactly once, got {count}"
            )

        replacement = source.replace(
            old,
            new,
            1,
        )

        if replacement == source:
            raise ValueError(
                "edit produced no source change"
            )

        return replacement

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "CodeModificationEdit",
]
