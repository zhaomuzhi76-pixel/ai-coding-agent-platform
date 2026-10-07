from __future__ import annotations

from typing import Any


class ProjectSessionAPIResult:
    """
    API result projection support.

    Owns:
        - session result validation
        - session collection projection
        - generic result projection

    Does not own:
        - business operations
        - lifecycle
        - registry
        - transport
    """

    VERSION = "1.0"

    def session(
        self,
        value: Any,
    ) -> dict[str, object]:
        dump = getattr(
            value,
            "dump",
            None,
        )

        if not callable(dump):
            raise TypeError(
                "adapter returned invalid session"
            )

        result = dump()

        if not isinstance(
            result,
            dict,
        ):
            raise TypeError(
                "session dump must dict"
            )

        return dict(result)

    def sessions(
        self,
        values,
    ) -> list[dict[str, object]]:
        return [
            self.session(value)
            for value in values
        ]

    def generic(
        self,
        value: Any,
    ) -> dict[str, object]:
        if isinstance(
            value,
            dict,
        ):
            return dict(value)

        dump = getattr(
            value,
            "dump",
            None,
        )

        if callable(dump):
            result = dump()

            if isinstance(
                result,
                dict,
            ):
                return dict(result)

        return {
            "result": value,
        }

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProjectSessionAPIResult",
]
