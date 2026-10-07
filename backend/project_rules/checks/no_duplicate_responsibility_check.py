"""职责重复检查 —— 语义分析版（零硬编码）。

不只看名字：用 AST 指纹 + Jaccard 相似度判定"真职责重复"。

判定：
  · 语义相似度 ≥ high_sim  → 真重复（error）
  · low_sim ≤ sim < high_sim → 疑似（warn）
  · sim < low_sim          → 不同职责，不报
  · 目标是 re-export        → 跳过

配置优先级（零硬编码）：
  · rule.args.high_similarity / low_similarity / min_shared_files
  · 环境变量 PROJECT_RULES_HIGH_SIM / LOW_SIM / MIN_SHARED
  · 默认: 0.85 / 0.50 / 5
"""
from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Any

from backend.project_rules.rule_types import Rule, RuleResult


# ── 语言规范判定（非名单） ──────────────────────

def _is_private_or_magic(name: str) -> bool:
    if name.startswith("_"):
        return True
    if name.startswith("__") and name.endswith("__"):
        return True
    return False


def _is_backup(p: Path) -> bool:
    n = p.name
    if n.endswith(".bak"):
        return True
    if ".bak" in n and n.rfind(".bak") > n.rfind("."):
        return True
    if n.startswith(".") and n.endswith(("~", ".swp", ".tmp")):
        return True
    return False


# ── AST 指纹（语义不依赖名字） ──────────────────

def _class_fp(node: ast.ClassDef) -> set[str]:
    fp: set[str] = set()
    for c in node.body:
        if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = tuple(a.arg for a in c.args.args if a.arg != "self")
            fp.add(f"m:{c.name}/{len(args)}")
        elif isinstance(c, ast.AnnAssign):
            if isinstance(c.target, ast.Name):
                fp.add(f"f:{c.target.id}")
        elif isinstance(c, ast.Assign):
            for t in c.targets:
                if isinstance(t, ast.Name):
                    fp.add(f"f:{t.id}")
    return fp


def _func_fp(node: ast.AST) -> set[str]:
    fp: set[str] = set()
    args = getattr(node, "args", None)
    if args is None:
        return fp
    names = [a.arg for a in getattr(args, "args", []) if a.arg != "self"]
    fp.update(f"a:{a}" for a in names)
    kw = getattr(args, "kwonlyargs", []) or []
    fp.update(f"k:{a.arg}" for a in kw)
    return fp


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _is_reexport(src: str, name: str) -> bool:
    """文件是否只是从别处引入 name（无独立定义）。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for a in node.names:
                if (a.asname or a.name) == name:
                    return True
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return True
    return False


# ── 配置 ─────────────────────────────────────────

def _cfg(rule: Rule) -> tuple[float, float, int]:
    args = rule.args or {}
    hi = args.get("high_similarity")
    lo = args.get("low_similarity")
    ms = args.get("min_shared_files")
    if not isinstance(hi, (int, float)):
        hi = float(os.environ.get("PROJECT_RULES_HIGH_SIM", 0.85))
    if not isinstance(lo, (int, float)):
        lo = float(os.environ.get("PROJECT_RULES_LOW_SIM", 0.50))
    if not isinstance(ms, int):
        v = os.environ.get("PROJECT_RULES_MIN_SHARED", "5").strip()
        ms = int(v) if v.isdigit() else 5
    return float(hi), float(lo), int(ms)


# ── Checker ──────────────────────────────────────

class NoDuplicateResponsibilityChecker:
    rule_id = "no_duplicate_responsibility"

    def run(self, root_path: str, rule: Rule) -> RuleResult:
        from backend.project_rules.discovery import (
            detect_extensions, detect_scan_roots, should_skip,
        )
        root = Path(root_path)
        raw_roots = rule.args.get("scan_roots") or \
            detect_scan_roots(root)
        raw_exts = rule.args.get("extensions") or \
            detect_extensions(root)
        exts = tuple(raw_exts)
        hi, lo, min_shared = _cfg(rule)

        # bucket[name] = [(rel_path, fingerprint, is_reexport)]
        buckets: dict[str, list[tuple[str, set[str], bool]]] = {}

        for base_name in raw_roots:
            base = root / base_name
            if not base.is_dir():
                continue
            for p in base.rglob("*"):
                if not p.is_file() or p.suffix not in exts:
                    continue
                if should_skip(p) or _is_backup(p):
                    continue
                try:
                    src = p.read_text(encoding="utf-8")
                    tree = ast.parse(src)
                except (OSError, SyntaxError):
                    continue
                rel = p.relative_to(root).as_posix()
                for node in tree.body:
                    if isinstance(node, ast.ClassDef):
                        nm = node.name
                        if _is_private_or_magic(nm):
                            continue
                        buckets.setdefault(nm, []).append(
                            (rel, _class_fp(node),
                             _is_reexport(src, nm)),
                        )
                    elif isinstance(node, (ast.FunctionDef,
                                           ast.AsyncFunctionDef)):
                        nm = node.name
                        if _is_private_or_magic(nm):
                            continue
                        buckets.setdefault(nm, []).append(
                            (rel, _func_fp(node),
                             _is_reexport(src, nm)),
                        )

        real: list[str] = []      # 真重复（error）
        suspect: list[str] = []   # 疑似（warn）
        common: list[str] = []    # 通用名（info）

        for name, items in sorted(buckets.items()):
            # 过滤 re-export
            defined = [it for it in items if not it[2]]
            if len(defined) <= 1:
                continue

            max_sim = 0.0
            pair = ("", "")
            for i in range(len(defined)):
                for j in range(i + 1, len(defined)):
                    sim = _jaccard(defined[i][1], defined[j][1])
                    if sim > max_sim:
                        max_sim = sim
                        pair = (defined[i][0], defined[j][0])

            if max_sim >= hi:
                real.append(
                    f"[{max_sim:.0%}] {name} in {pair[0]} ↔ {pair[1]}"
                )
            elif max_sim >= lo:
                suspect.append(
                    f"[{max_sim:.0%}] {name} in {pair[0]} ↔ {pair[1]}"
                )
            elif len(defined) >= min_shared:
                common.append(f"{name} × {len(defined)} (不同职责)")

        return RuleResult(
            rule_id=self.rule_id,
            passed=len(real) == 0,
            findings=(
                tuple(real[:30])
                + tuple(f"[疑似] {s}" for s in suspect[:15])
                + tuple(f"[通用名] {c}" for c in common[:10])
            ),
        )


CHECKER = NoDuplicateResponsibilityChecker()

__all__ = ["NoDuplicateResponsibilityChecker", "CHECKER"]
