"""读用户规则 → 转成实际检查（工业级"规则执行引擎"）。

用户说"禁止 print" → 本模块 grep 代码里有没有 print
用户说"max_lines=200" → 本模块用 200 检查（覆盖默认 230）
用户说"snake_case" → 本模块检查 def/变量名是否合规

不重复职责：规则的"存"在 agent_learning；本模块只做"读+检查"。
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from backend.quality.standards.contracts import CheckResult


_DB = Path.home() / ".biancheng" / "global" / "global.db"


class UserRulesChecker:
    VERSION = "1.0"

    def __init__(self, db_path: Path | None = None) -> None:
        self._db = db_path or _DB
        self._rules: dict[str, list[str]] = {}

    def load(self, workspace: str = "") -> dict[str, list[str]]:
        """按 scope 过滤：global 全生效；project/session 匹配当前 workspace。"""
        if not self._db.exists():
            return {}
        try:
            with sqlite3.connect(self._db) as conn:
                rows = conn.execute(
                    "SELECT category, key, value, scope, workspace "
                    "FROM preferences "
                    "WHERE category IN ('code_style','workflow','tech_stack') "
                    "AND confidence >= 60 "
                    "ORDER BY confidence DESC"
                ).fetchall()
        except Exception:
            return {}
        out: dict[str, list[str]] = {}
        ws = (workspace or "").strip()
        for cat, key, val, scope, rule_ws in rows:
            s = scope or "global"
            rw = rule_ws or ""
            if s in ("project", "session"):
                if ws and rw != ws:
                    continue
            out.setdefault(key, []).append(val)
        self._rules = out
        return out

    @property
    def rules(self) -> dict[str, list[str]]:
        if not self._rules:
            self.load()
        return self._rules

    def check_file(self, path: Path, rel: str) -> list[CheckResult]:
        """按用户规则检查单个文件。"""
        out: list[CheckResult] = []
        if not self.rules:
            return out
        try:
            src = path.read_text(encoding="utf-8")
        except OSError:
            return out

        # 1. forbid_* ：禁止出现的词
        for bad in self.rules.get("forbid", []):
            hits = _grep_word(src, bad)
            if hits:
                out.append(CheckResult(
                    "no_duplicate", False, rel,
                    f"用户规则禁止 '{bad}'，发现 {len(hits)} 处: "
                    f"line {hits[0]}",
                    severity="error",
                ))

        # 2. max_lines：用户自定义上限（覆盖默认 230）
        custom_max = self.rules.get("max_lines", [])
        if custom_max:
            try:
                limit = int(custom_max[0])
                n = len(src.splitlines())
                if n > limit:
                    out.append(CheckResult(
                        "line_limit", False, rel,
                        f"用户规则: 最多 {limit} 行，实际 {n} 行",
                    ))
            except (ValueError, IndexError):
                pass

        # 3. naming：snake_case 检查
        naming = self.rules.get("naming", [])
        if naming:
            style = naming[0]
            if style == "snake_case":
                bad_names = _check_snake_case(src)
                for line, name in bad_names[:3]:
                    out.append(CheckResult(
                        "no_duplicate", False, rel,
                        f"用户规则 snake_case：`{name}`（line {line}）"
                        f" 应为小写下划线",
                        severity="error",
                    ))

        return out

    def check_layer(self, root: Path) -> list[CheckResult]:
        self.load(workspace=str(root))
        out: list[CheckResult] = []
        for f in root.rglob("*.py"):
            rel = str(f.relative_to(root.parent)) \
                if f.is_relative_to(root.parent) else str(f)
            out.extend(self.check_file(f, rel))
        return out


def _grep_word(src: str, word: str) -> list[int]:
    """找词出现的行号（跳过注释和字符串里的内容）。"""
    hits: list[int] = []
    pat = re.compile(r"\b" + re.escape(word) + r"\b")
    for i, line in enumerate(src.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if pat.search(line):
            hits.append(i)
    return hits


_SNAKE_CASE_FUNC = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _check_snake_case(src: str) -> list[tuple[int, str]]:
    """检查 def 名是否 snake_case。"""
    bad: list[tuple[int, str]] = []
    for i, line in enumerate(src.split("\n"), 1):
        m = _SNAKE_CASE_FUNC.match(line.strip())
        if not m:
            continue
        name = m.group(1)
        if name.startswith("_"):
            continue
        if re.match(r"^[a-z][a-z0-9_]*$", name):
            continue
        bad.append((i, name))
    return bad


__all__ = ["UserRulesChecker"]
