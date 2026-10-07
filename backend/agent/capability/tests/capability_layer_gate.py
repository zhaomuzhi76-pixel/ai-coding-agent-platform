from __future__ import annotations

from backend.agent.capability.capability_composition import (
    CapabilityComposition,
)
from backend.agent.capability.capability_descriptor import (
    CapabilityDescriptor,
)
from backend.agent.capability.capability_registry import (
    CapabilityRegistry,
)


class ReadyCapability:
    def __init__(self, name: str) -> None:
        self._name = name
        self._ready = True

    def name(self) -> str:
        return self._name

    def ready(self) -> bool:
        return self._ready


class ToggleCapability(ReadyCapability):
    def set_ready(self, value: bool) -> None:
        self._ready = value


def main() -> int:
    descriptor = CapabilityDescriptor(
        name="execution",
        description="execution capability",
    )

    assert descriptor.ready()
    assert descriptor.dump()["ready"] is True

    registry = CapabilityRegistry()
    ready = ReadyCapability("execution.dispatch")
    registry.register(ready)

    assert registry.get(
        "execution.dispatch"
    ) is ready

    assert registry.names() == (
        "execution.dispatch",
    )

    duplicate_failed = False

    try:
        registry.register(
            ReadyCapability("execution.dispatch")
        )
    except ValueError:
        duplicate_failed = True

    assert duplicate_failed

    toggle = ToggleCapability(
        "execution.runtime"
    )
    toggle.set_ready(False)
    registry.register(toggle)

    assert registry.ready() is False

    toggle.set_ready(True)

    assert registry.ready() is True

    composition = CapabilityComposition(
        registry
    )

    assert composition.ready()
    assert set(
        composition.names()
    ) == {
        "execution.dispatch",
        "execution.runtime",
    }

    invalid_name_failed = False

    try:
        registry.register(
            ReadyCapability("   ")
        )
    except ValueError:
        invalid_name_failed = True

    assert invalid_name_failed

    print("CAPABILITY_LAYER_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
