"""契约层：规则 ID、检查结果、层报告（纯数据）。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


RULE_IDS: tuple[str, ...] = (
    "line_limit",        # 1. 单文件 ≤ 230 行
    "no_exit",           # 2. 不使用 exit
    "layer_order",       # 3. 分层依赖方向
    "no_duplicate",      # 4. 无重复职责
    "plugin_pattern",    # 5. 插件化新增
    "tmpfs_test",        # 6. 测试不占硬盘
    "codex_style",       # 7. codex 风格
    "claude_style",      # 8. claude 风格
    "aliyun_style",      # 9. 阿里云风格
    "dify_ref",          # 10. Dify 参考
    "one_cmd",           # 11. 一条命令支持
)


@dataclass(frozen=True)
class CheckResult:
    rule_id: str
    ok: bool
    file: str = ""
    message: str = ""
    severity: str = "error"   # error | warn

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id, "ok": self.ok,
            "file": self.file, "message": self.message,
            "severity": self.severity,
        }


@dataclass
class LayerReport:
    layer: str
    files_scanned: int = 0
    results: list[CheckResult] = field(default_factory=list)
    fixes: list[str] = field(default_factory=list)

    def add(self, r: CheckResult) -> None:
        self.results.append(r)

    @property
    def errors(self) -> list[CheckResult]:
        return [r for r in self.results if not r.ok
                and r.severity == "error"]

    @property
    def warnings(self) -> list[CheckResult]:
        return [r for r in self.results if not r.ok
                and r.severity == "warn"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> dict[str, Any]:
        by_rule: dict[str, dict[str, int]] = {}
        for r in self.results:
            slot = by_rule.setdefault(r.rule_id, {"pass": 0, "fail": 0})
            slot["pass" if r.ok else "fail"] += 1
        return {
            "layer": self.layer,
            "files_scanned": self.files_scanned,
            "ok": self.ok,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "by_rule": by_rule,
            "fixes": list(self.fixes),
        }


__all__ = ["RULE_IDS", "CheckResult", "LayerReport"]
