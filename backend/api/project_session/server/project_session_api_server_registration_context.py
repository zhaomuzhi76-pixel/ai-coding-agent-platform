from __future__ import annotations


class ProjectSessionAPIServerRegistrationContextMixin:
    """
    Startup context extraction boundary.

    Owns:
        - startup object validation
        - startup state access
        - application context extraction

    Does not own:
        - project-session construction
        - runtime submission construction
        - route registration
    """

    def _startup_context(
        self,
        startup: object,
    ) -> dict[str, object]:
        if startup is None:
            raise ValueError(
                "startup required"
            )

        state = getattr(
            startup,
            "state",
            None,
        )
        context = getattr(
            state,
            "context",
            None,
        )

        if not isinstance(
            context,
            dict,
        ):
            raise RuntimeError(
                "application startup context unavailable"
            )

        return context


__all__ = [
    "ProjectSessionAPIServerRegistrationContextMixin",
]
