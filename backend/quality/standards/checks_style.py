"""规则 7/8/9/10：codex / claude / 阿里云 / dify 参考。"""
from __future__ import annotations

from pathlib import Path

from backend.quality.standards.contracts import CheckResult


# 每风格：关键词列表（出现在文件里即算引用）
_STYLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "codex_style": (
        "boundary", "diff_verif", "codex", "step_commit",
        "apply_patch",
    ),
    "claude_style": (
        "adr", "claude", "repo_map", "call_tracer",
        "search_replace", "edit_block",
    ),
    "aliyun_style": (
        "aliyun", "rule_review", "test_generator",
        "docstring_writer", "completion",
    ),
    "dify_ref": (
        "dify", "workflow", "human_input", "workflow_node",
    ),
}


def _scan(path: Path, keywords: tuple[str, ...]) -> bool:
    try:
        src = path.read_text(encoding="utf-8").lower()
    except OSError:
        return False
    return any(kw in src for kw in keywords)


def check_style(
    rule_id: str, path: Path, rel: str,
) -> CheckResult:
    kws = _STYLE_KEYWORDS.get(rule_id, ())
    ok = _scan(path, kws)
    if ok:
        return CheckResult(rule_id, True, rel, "referenced")
    return CheckResult(
        rule_id, True, rel,
        f"（{rule_id} 未在本文件引用，非强制）",
        severity="warn",
    )


def run_style(path: Path, rel: str) -> list[CheckResult]:
    return [
        check_style(rid, path, rel)
        for rid in ("codex_style", "claude_style",
                    "aliyun_style", "dify_ref")
    ]


__all__ = ["check_style", "run_style"]
