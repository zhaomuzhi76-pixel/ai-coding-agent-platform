from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.identity import (
    IdentityProtocol,
)

from backend.core.protocols.capability import (
    CapabilityProtocol,
)

from backend.core.protocols.ready import (
    ReadyProtocol,
)

from backend.core.protocols.dumpable import (
    DumpableProtocol,
)


@runtime_checkable
class CoreComponentProtocol(
    IdentityProtocol,
    CapabilityProtocol,
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical core component contract.

    Owns:
        - identity capability
        - capability declaration
        - readiness
        - snapshot export

    Does not own:
        - construction
        - lifecycle control
        - execution
        - persistence
        - transport
    """

    pass


__all__ = [
    "CoreComponentProtocol",
]
