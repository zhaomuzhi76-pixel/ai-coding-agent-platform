"""文件行数检查：单文件不得超过 230 行。"""
from __future__ import annotations

import fnmatch
from pathlib import Path

from backend.project_rules.rule_types import Rule, RuleResult


class FileSizeChecker:
    rule_id = "file_size_max_230"

    def run(self, root_path: str, rule: Rule) -> RuleResult:
        root = Path(root_path)
        max_lines = int(rule.args.get("max_lines", 230))
        skips = tuple(rule.args.get("skip_patterns", ()))
        exts = tuple(rule.args.get("extensions", ()))

        findings: list[str] = []
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if exts and p.suffix not in exts:
                continue
            rel = p.relative_to(root).as_posix()
            if any(fnmatch.fnmatch(rel, s) or s in rel for s in skips):
                continue
            try:
                n = sum(1 for _ in p.open("r", encoding="utf-8", errors="ignore"))
            except OSError:
                continue
            if n > max_lines:
                findings.append(f"{rel}: {n} lines > {max_lines}")

        return RuleResult(
            rule_id=rule.id,
            passed=not findings,
            findings=tuple(findings),
        )


CHECKER = FileSizeChecker()
