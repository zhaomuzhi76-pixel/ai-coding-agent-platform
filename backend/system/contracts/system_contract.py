from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Protocol, runtime_checkable


class SystemState(str, Enum):
    """System-level lifecycle state."""

    CREATED = "created"
    STARTING = "starting"
    READY = "ready"
    FAILED = "failed"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass(frozen=True)
class SystemReadiness:
    """Immutable aggregate readiness snapshot."""

    ready: bool
    state: SystemState
    reason: str | None = None


@dataclass(frozen=True)
class SystemHealth:
    """Immutable aggregate system health snapshot."""

    healthy: bool
    state: SystemState
    components: Mapping[str, bool]
    reason: str | None = None


@dataclass(frozen=True)
class SystemSnapshot:
    """Immutable system state snapshot."""

    state: SystemState
    readiness: SystemReadiness
    health: SystemHealth


@runtime_checkable
class SystemComponentProtocol(Protocol):
    """Observation boundary for an assembled subsystem."""

    @property
    def name(self) -> str:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> Mapping[str, Any]:
        ...


@runtime_checkable
class SystemExtensionProtocol(Protocol):
    """Extension boundary for system-level plugins."""

    @property
    def name(self) -> str:
        ...

    def attach(self, context: Any) -> None:
        ...

    def detach(self) -> None:
        ...

    def ready(self) -> bool:
        ...


@runtime_checkable
class SystemLifecycleProtocol(Protocol):
    """System lifecycle coordination contract."""

    @property
    def state(self) -> SystemState:
        ...

    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...

    def fail(self) -> None:
        ...

    def ready(self) -> bool:
        ...


__all__ = [
    "SystemState",
    "SystemReadiness",
    "SystemHealth",
    "SystemSnapshot",
    "SystemComponentProtocol",
    "SystemExtensionProtocol",
    "SystemLifecycleProtocol",
]
