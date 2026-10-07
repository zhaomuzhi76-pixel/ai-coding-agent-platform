"""Mixin 2 of PrefixTuningBackend."""
from __future__ import annotations
class _Mixin2:
    def dump(self) -> dict:
        return {
            "name": self.name,
            "ready": self.ready(),
            "note": "prefix tuning via peft+transformers",
        }
