"""Layer Audit 插件入口：只接线。"""
from __future__ import annotations

from typing import List

from backend.runtime.plugins.layer_audit.audit_models import AuditReport
from backend.runtime.plugins.layer_audit.audit_renderer import render_report
from backend.runtime.plugins.layer_audit.cross_file_analyzer import build_report
from backend.runtime.plugins.layer_audit.cross_layer_analyzer import (
    render_cross_layer,
)
from backend.runtime.plugins.layer_audit.scanner import scan, scan_paths


class LayerAuditPlugin:
    name = "layer_audit"
    version = "1.1.0"

    def audit(self, root: str, hard: int = 230) -> AuditReport:
        return build_report(root, scan(root), hard=hard)

    def audit_paths(self, paths: List[str], root: str,
                    hard: int = 230) -> AuditReport:
        return build_report(root, scan_paths(paths, root), hard=hard)

    def render(self, root: str, hard: int = 230) -> str:
        return render_report(self.audit(root, hard=hard))

    def render_paths(self, paths: List[str], root: str,
                     hard: int = 230) -> str:
        return render_report(self.audit_paths(paths, root, hard=hard))

    def cross_layer(self, paths: List[str], root: str,
                    hard: int = 230) -> str:
        report = self.audit_paths(paths, root, hard=hard)
        return render_cross_layer(report)
