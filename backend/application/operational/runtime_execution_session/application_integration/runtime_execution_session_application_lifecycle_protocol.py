from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RuntimeExecutionSessionApplicationLifecycleProtocol(
    Protocol,
):
    """
    Application lifecycle capability.

    Owns:
        - lifecycle delegation boundary
    """

    def start(
        self,
        *,
        context: dict[str, object],
        project_session_service: object,
    ) -> object:
        ...

    def stop(
        self,
        *,
        context: dict[str, object],
    ) -> None:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...
