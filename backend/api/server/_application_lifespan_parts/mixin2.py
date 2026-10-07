"""Mixin 2 of ApplicationLifespan."""
from __future__ import annotations
class _Mixin2:
    def ready(
        self,
    ) -> bool:
        return self.orchestrator.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "startup": (
                type(self.startup).__name__
                if self.startup is not None
                else None
            ),
            "orchestrator": self.orchestrator.dump(),
            "bootstrap_shutdown_done": (
                self._bootstrap_shutdown_done
            ),
        }
