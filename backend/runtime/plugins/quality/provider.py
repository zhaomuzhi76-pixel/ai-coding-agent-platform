"""Quality Provider：对外只暴露能力，不暴露实现细节。"""
from __future__ import annotations

from typing import Callable, Dict

from backend.runtime.plugins.quality.plugin import QualityPlugin


class QualityProvider:
    def __init__(self) -> None:
        self._plugin = QualityPlugin()

    def capabilities(self) -> Dict[str, Callable]:
        return {
            "quality.one_shot_gate": self._plugin.run_once,
            "quality.registry": self._plugin.build_registry,
        }
