"""Line Refactor Provider：对外只暴露能力。"""
from __future__ import annotations

from typing import Callable, Dict

from backend.runtime.plugins.line_refactor.plugin import LineRefactorPlugin


class LineRefactorProvider:
    def __init__(self) -> None:
        self._plugin = LineRefactorPlugin()

    def capabilities(self) -> Dict[str, Callable]:
        return {
            "line_refactor.plan": self._plugin.plan,
            "line_refactor.render_plan": self._plugin.render_plan,
            "line_refactor.apply": self._plugin.apply,
            "line_refactor.diagnose": self._plugin.diagnose,
        }
