"""L2 源文件智能裁剪器。

工业级：LLM 上下文有限，不能塞 500 行。
从 task 提取符号名 → AST 定位 → 只返回相关片段 + import 区。

不重复职责：
  - 符号定义/关系 → codebase/graph
  - 文件读写 → workspace/file_ops
  - 本模块只做"按符号裁剪文本"
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass


# 常见英文/中文停用词，排除后剩下的才当候选符号
_STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "to", "of", "in",
    "on", "at", "for", "by", "with", "and", "or", "not", "that",
    "this", "it", "be", "do", "does", "did", "has", "have", "had",
    "print", "logger", "info", "def", "class", "import", "from",
    "把", "改", "成", "为", "里", "的", "函数", "变成", "替换",
    "修改", "改为", "使用", "用", "到",
})


@dataclass(frozen=True)
class TrimResult:
    text: str
    hit_symbols: tuple[str, ...]
    hit_count: int
    trimmed: bool
    original_lines: int
    kept_lines: int


def extract_candidates(task: str) -> list[str]:
    """从任务描述提取可能的符号名（函数名/类名/标识符）。"""
    tokens = re.findall(
        r"[a-zA-Z_][a-zA-Z0-9_]{1,60}", task or "",
    )
    out: list[str] = []
    seen = set()
    for t in tokens:
        low = t.lower()
        if low in _STOPWORDS or len(t) < 2:
            continue
        if low in seen:
            continue
        seen.add(low)
        out.append(t)
    return out


def _collect_symbols(source: str) -> dict[str, tuple[int, int]]:
    """AST 扫描：符号名 → (起始行, 结束行)，1-based。"""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    out: dict[str, tuple[int, int]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            end = getattr(node, "end_lineno", None) or node.lineno
            out[node.name] = (node.lineno, end)
    return out


def _merge_ranges(
    ranges: list[tuple[int, int]], gap: int = 3,
) -> list[tuple[int, int]]:
    """合并重叠或相邻的区间。"""
    if not ranges:
        return []
    ranges = sorted(ranges)
    merged = [ranges[0]]
    for s, e in ranges[1:]:
        ls, le = merged[-1]
        if s <= le + gap:
            merged[-1] = (ls, max(le, e))
        else:
            merged.append((s, e))
    return merged


class SourceTrimmer:
    VERSION = "1.0"

    def __init__(
        self,
        *,
        head_lines: int = 25,       # 保留文件头部（docstring + imports）
        ctx_before: int = 4,        # 目标符号前保留行数
        ctx_after: int = 2,         # 目标符号后保留行数
        max_total_lines: int = 200, # 裁剪后总上限（超了再截）
    ) -> None:
        self.head_lines = head_lines
        self.ctx_before = ctx_before
        self.ctx_after = ctx_after
        self.max_total_lines = max_total_lines

    def trim(self, source: str, task: str) -> TrimResult:
        if not source:
            return TrimResult("", (), 0, False, 0, 0)
        lines = source.split("\n")
        total = len(lines)

        # 短文件不裁剪
        if total <= self.max_total_lines:
            return TrimResult(
                source, (), 0, False, total, total,
            )

        candidates = extract_candidates(task)
        if not candidates:
            # 无法识别符号 → 只保留头部
            return self._head_only(lines, total)

        symbols = _collect_symbols(source)
        cand_lower = {c.lower(): c for c in candidates}

        # 命中符号
        hits: list[tuple[str, int, int]] = []
        for name, (start, end) in symbols.items():
            if name.lower() in cand_lower:
                hits.append((name, start, end))

        if not hits:
            return self._head_only(lines, total)

        # 合并区间
        ranges = [
            (max(1, s - self.ctx_before),
             min(total, e + self.ctx_after))
            for _, s, e in hits
        ]
        merged = _merge_ranges(ranges, gap=3)

        # 头部区间（保留 imports）
        head_end = min(total, self.head_lines)
        if merged and merged[0][0] <= head_end + 1:
            merged[0] = (1, max(merged[0][1], head_end))
        else:
            merged.insert(0, (1, head_end))

        # 拼装
        chunks: list[str] = []
        hit_names = tuple(name for name, _, _ in hits)
        for idx, (s, e) in enumerate(merged):
            if idx > 0:
                gap = s - merged[idx - 1][1] - 1
                if gap > 0:
                    chunks.append(f"... ({gap} lines skipped) ...")
            chunks.append("\n".join(lines[s - 1:e]))

        body = "\n".join(chunks)
        body_lines = body.count("\n") + 1
        if body_lines > self.max_total_lines:
            # 硬截断
            keep = body.split("\n")[: self.max_total_lines]
            body = "\n".join(keep) + "\n... (truncated) ..."
            body_lines = self.max_total_lines

        return TrimResult(
            text=body,
            hit_symbols=hit_names,
            hit_count=len(hits),
            trimmed=True,
            original_lines=total,
            kept_lines=body_lines,
        )

    def _head_only(self, lines: list[str], total: int) -> TrimResult:
        head = "\n".join(lines[: self.head_lines])
        return TrimResult(
            text=head + f"\n... ({total - self.head_lines} more lines) ...",
            hit_symbols=(),
            hit_count=0,
            trimmed=True,
            original_lines=total,
            kept_lines=self.head_lines,
        )


__all__ = ["SourceTrimmer", "TrimResult", "extract_candidates"]
