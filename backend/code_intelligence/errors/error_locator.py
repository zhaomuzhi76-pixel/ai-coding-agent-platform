from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.code_intelligence.errors.error_parser import (
    ParsedError,
)


class ErrorLocator:
    """
    把 ParsedError 定位到具体文件 + 上下文。

    输出：
        - target_file: 相对路径（错误叶子节点）
        - target_line: 1-based
        - context_lines: 前后 N 行
        - related_files: 调用栈中其他文件（去重）
        - stack_files: 调用栈全部文件（含绝对路径）
    """

    VERSION = "1.1"
    RESPONSIBILITY = ("error_location_resolution",)

    CONTEXT_RADIUS = 15

    def locate(
        self,
        error: ParsedError,
        *,
        workspace: str,
    ) -> dict[str, Any]:
        root = Path(workspace).expanduser().resolve()
        if not root.is_dir():
            return {"success": False, "error": "workspace_invalid"}

        target = self._resolve_file(error.file, root)
        if target is None:
            return {
                "success": False,
                "error": "file_not_found",
                "searched": error.file,
            }

        try:
            source = target.read_text(
                encoding="utf-8", errors="ignore"
            )
        except OSError as exc:
            return {"success": False, "error": str(exc)}

        lines = source.split("\n")
        line_no = error.line or 1
        line_no = max(1, min(line_no, len(lines)))

        start = max(0, line_no - 1 - self.CONTEXT_RADIUS)
        end = min(len(lines), line_no + self.CONTEXT_RADIUS)

        context = "\n".join(
            f"{i + 1:>5}: {ln}"
            for i, ln in enumerate(lines[start:end], start=start)
        )

        # 遍历 stack，收集所有涉及的文件
        stack_files: list[str] = []
        related: list[str] = []
        for frame in error.stack:
            f = frame.get("file")
            if not f:
                continue
            p = self._resolve_file(f, root)
            if not p:
                continue
            try:
                rel = str(p.relative_to(root))
            except ValueError:
                rel = str(p)
            if rel not in stack_files:
                stack_files.append(rel)
            if p != target and rel not in related:
                related.append(rel)

        return {
            "success": True,
            "target_file": str(target.relative_to(root)),
            "target_line": line_no,
            "target_function": error.function,
            "context_lines": context,
            "full_source": source,
            "related_files": related[:5],
            "stack_files": stack_files[:10],
        }

    @staticmethod
    def _resolve_file(
        raw: str | None,
        root: Path,
    ) -> Path | None:
        """
        严格解析：
            1. 绝对路径 + 存在 → 返回
            2. 相对路径 + 存在 → 返回
            3. 否则 None（不 basename 兜底）
        """
        if not raw or not isinstance(raw, str):
            return None
        raw = raw.strip()
        if not raw:
            return None

        p = Path(raw)
        if p.is_absolute():
            if p.exists() and p.is_file():
                return p
            return None

        candidate = (root / raw).resolve()
        if candidate.exists() and candidate.is_file():
            return candidate
        return None

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "context_radius": self.CONTEXT_RADIUS,
        }


__all__ = ["ErrorLocator"]
