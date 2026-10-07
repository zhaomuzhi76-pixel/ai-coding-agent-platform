"""tmpfs 测试检查：测试临时目录必须在 /dev/shm 或 /tmp 下。"""
from __future__ import annotations

import os
from pathlib import Path

from backend.project_rules.rule_types import Rule, RuleResult


class TmpfsOnlyChecker:
    rule_id = "tmpfs_only"

    def run(self, root_path: str, rule: Rule) -> RuleResult:
        allow = tuple(rule.args.get("allow_paths", ()))
        forbid = tuple(rule.args.get("forbid_paths", ()))

        findings: list[str] = []
        # 检查当前进程的 TMPDIR
        tmpdir = os.environ.get("TMPDIR", "")
        if tmpdir:
            if forbid and any(tmpdir.startswith(f) for f in forbid):
                findings.append(
                    f"TMPDIR={tmpdir} 在禁止路径下，应设在 {allow}"
                )
            if allow and not any(tmpdir.startswith(a) for a in allow):
                findings.append(
                    f"TMPDIR={tmpdir} 不在允许路径 {allow}"
                )

        # 检查测试脚本目录（若有）
        scripts = Path(root_path) / "scripts"
        if scripts.is_dir():
            for sh in scripts.glob("*test*.sh"):
                text = sh.read_text(encoding="utf-8", errors="ignore")
                if "mktemp" in text and "/dev/shm" not in text and "/tmp" not in text:
                    findings.append(
                        f"{sh.name}: mktemp 未指定 tmpfs 路径"
                    )

        return RuleResult(
            rule_id=rule.id,
            passed=not findings,
            findings=tuple(findings),
        )


CHECKER = TmpfsOnlyChecker()
