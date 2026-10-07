"""生成后规则校验的快照器：把 changes 应用到 tmpfs 快照。

职责单一：不跑 checker，不解析规则。
被 rules_verifier 调用（通道 B）。
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import shutil
from pathlib import Path

_SKIP = frozenset({".git", "node_modules", "__pycache__",
                   ".venv", "venv", "dist", "build"})


def apply_snapshot(src: Path, dst: Path, changes: list[dict]) -> None:
    """复制 src → dst，再把 changes 文本替换应用上去。"""
    _copy_tree(src, dst)
    for c in changes:
        if not isinstance(c, dict):
            continue
        f = str(c.get("file") or c.get("path") or "")
        if not f:
            continue
        target = dst / f
        if not target.is_file():
            continue
        try:
            orig = target.read_text(encoding="utf-8")
        except OSError:
            continue
        new = apply_change_content(orig, c)
        if new is not None:
            try:
                target.write_text(new, encoding="utf-8")
            except OSError:
                pass


def apply_change_content(orig: str, c: dict) -> str | None:
    """把单条 change 应用到原文；无法应用返回 None。"""
    k = str(c.get("kind") or "")
    if k == "edit":
        out = orig
        for e in (c.get("edits") or []):
            if not isinstance(e, dict):
                continue
            old = str(e.get("old") or "")
            new = str(e.get("new") or "")
            if old and old in out:
                out = out.replace(old, new, 1)
        return out
    t = c.get("text")
    if isinstance(t, str):
        return t
    return None


def _copy_tree(src: Path, dst: Path) -> None:
    for item in src.iterdir():
        if item.name in _SKIP:
            continue
        target = dst / item.name
        try:
            if item.is_dir():
                shutil.copytree(item, target, symlinks=True,
                                ignore_dangling_symlinks=True)
            else:
                shutil.copy2(item, target)
        except Exception as e:
            swallow("agent.orchestration.rules_snapshot:71", e)


__all__ = ["apply_snapshot", "apply_change_content"]
