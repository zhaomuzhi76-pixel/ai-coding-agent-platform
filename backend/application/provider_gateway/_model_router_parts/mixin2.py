"""Mixin 2 of ModelRouter."""
from __future__ import annotations
from .part1 import (Any, Dict,)  # noqa: F401
class _Mixin2:
    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "override_model": self._override_model,
            "agent_routing": {
                role: [r.to_dict() for r in chain]
                for role, chain in self._config.agent_routing.items()
            },
            "call_count": self.call_count,
            "fallback_count": self.fallback_count,
        }
