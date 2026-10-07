from __future__ import annotations

from backend.core.contracts.value import (
    CoreValue,
)

from backend.core.context.context_identity import (
    ContextIdentity,
)

from backend.core.context.context_metadata import (
    ContextMetadata,
)

from backend.core.context.context_state import (
    ContextState,
)


class Context:
    """
    Canonical framework context.

    Owns:
        - identity composition
        - metadata composition
        - state composition

    Does not own:
        - lifecycle
        - storage
        - execution
        - runtime orchestration
    """

    VERSION = "2.1"

    RESPONSIBILITY = (
        "context_identity",
        "context_metadata",
        "context_state",
    )

    def __init__(
        self,
        context_id: str,
        metadata: ContextMetadata | None = None,
    ) -> None:

        self._identity = ContextIdentity(
            context_id.strip()
        )

        self._metadata = (
            metadata
            if metadata is not None
            else ContextMetadata()
        )

        self._state = ContextState()


    @property
    def context_id(
        self,
    ) -> str:
        return self._identity.context_id


    @property
    def metadata(
        self,
    ) -> ContextMetadata:
        return self._metadata


    def set(
        self,
        key: str,
        value: CoreValue,
    ) -> None:
        self._state.set(
            key,
            value,
        )


    def get(
        self,
        key: str,
    ) -> CoreValue | None:
        return self._state.get(
            key
        )


    def contains(
        self,
        key: str,
    ) -> bool:
        return self._state.contains(
            key
        )


    def freeze(
        self,
    ) -> None:
        self._state.freeze()


    def snapshot(
        self,
    ) -> dict[str, CoreValue]:
        return self._state.snapshot()


    def restore(
        self,
        snapshot: dict[str, CoreValue],
    ) -> None:
        self._state.restore(
            snapshot
        )


    def ready(
        self,
    ) -> bool:
        return (
            bool(
                self.context_id
            )
            and self._metadata.ready()
            and self._state.ready()
        )


    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "context_id": self.context_id,
            "metadata": self.metadata.dump(),
            "state": self._state.snapshot(),
            "ready": self.ready(),
        }


__all__ = [
    "Context",
]
