"""根据 root 自动生成 rules 配置（零硬编码）。"""
from __future__ import annotations

from pathlib import Path

from backend.project_rules.discovery import (
    detect_extensions, detect_layers, detect_scan_roots,
)
from backend.project_rules.rule_types import Rule


def build_rules(root: Path) -> list[Rule]:
    scans = detect_scan_roots(root)
    exts = detect_extensions(root)
    layers = detect_layers(root)

    return [
        Rule(id="file_size_max_230", severity="error",
             category="file", description="单文件 ≤ 230 行",
             args={"extensions": exts, "max_lines": 230}),
        Rule(id="no_duplicate_responsibility", severity="error",
             category="architecture", description="职责重复",
             args={"scan_roots": scans, "extensions": exts}),
        Rule(id="plugin_pattern", severity="error",
             category="architecture", description="插件化新增", args={}),
        Rule(id="tmpfs_only", severity="error",
             category="test", description="测试不落盘", args={}),
        Rule(id="layer_purity", severity="error",
             category="architecture", description="分层依赖",
             args={"layers": layers}),
        Rule(id="no_exit", severity="error",
             category="style", description="库禁 exit", args={}),
        Rule(id="style_reference", severity="warn",
             category="style", description="工业级风格参考", args={}),
    ]


__all__ = ["build_rules"]
