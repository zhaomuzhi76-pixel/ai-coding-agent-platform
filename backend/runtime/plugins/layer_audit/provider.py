"""Layer Audit Provider：对外只暴露能力。"""
from __future__ import annotations

from typing import Callable, Dict

from backend.runtime.plugins.layer_audit.plugin import LayerAuditPlugin


class LayerAuditProvider:
    def __init__(self) -> None:
        self._plugin = LayerAuditPlugin()

    def capabilities(self) -> Dict[str, Callable]:
        return {
            "layer_audit.audit": self._plugin.audit,
            "layer_audit.audit_paths": self._plugin.audit_paths,
            "layer_audit.render": self._plugin.render,
            "layer_audit.render_paths": self._plugin.render_paths,
            "layer_audit.cross_layer": self._plugin.cross_layer,
        }
