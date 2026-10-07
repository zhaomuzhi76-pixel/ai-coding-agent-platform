from __future__ import annotations

from typing import Any

from backend.code_intelligence.patch.hunk_patch_contract import (
    FileChange,
    Hunk,
    HunkPatch,
)


class HunkApplier:
    """
    把 hunk patch 安全应用到源文件内容。

    严格规则（对齐 Claude Code FileEditTool）：
        1. old_string 必须精确出现在源文件中
        2. old_string 必须唯一（出现次数 == 1）
        3. 逐个应用，任一失败 → 全部回滚
    """

    VERSION = "1.0"
    RESPONSIBILITY = ("hunk_patch_application",)

    def apply_to_source(
        self,
        *,
        source: str,
        hunks: list[Hunk],
    ) -> dict[str, Any]:
        """应用一组 hunk 到 source，返回新内容。"""
        if not isinstance(source, str):
            return {"success": False, "error": "source_must_str"}
        if not hunks:
            return {"success": False, "error": "no_hunks"}

        current = source
        applied: list[dict[str, Any]] = []

        for i, hunk in enumerate(hunks):
            result = self._apply_one(current, hunk, i)
            if not result["success"]:
                return result
            current = result["content"]
            applied.append({
                "index": i,
                "old_len": len(hunk.old_string),
                "new_len": len(hunk.new_string),
            })

        return {
            "success": True,
            "content": current,
            "hunks_applied": len(applied),
            "details": applied,
        }

    def _apply_one(
        self,
        source: str,
        hunk: Hunk,
        index: int,
    ) -> dict[str, Any]:
        if not hunk.ready():
            return {
                "success": False,
                "error": "hunk_not_ready",
                "index": index,
            }

        count = source.count(hunk.old_string)
        if count == 0:
            return {
                "success": False,
                "error": "old_string_not_found",
                "index": index,
                "snippet": hunk.old_string[:80],
            }
        if count > 1:
            return {
                "success": False,
                "error": "old_string_not_unique",
                "index": index,
                "occurrences": count,
                "snippet": hunk.old_string[:80],
            }

        new_content = source.replace(
            hunk.old_string, hunk.new_string, 1,
        )
        return {"success": True, "content": new_content}

    def apply_file_change(
        self,
        *,
        file: str,
        source: str,
        change: FileChange,
    ) -> dict[str, Any]:
        """应用到单个文件。"""
        if change.file != file:
            return {
                "success": False,
                "error": "file_mismatch",
                "expected": file,
                "got": change.file,
            }
        result = self.apply_to_source(
            source=source, hunks=change.hunks,
        )
        if not result["success"]:
            result["file"] = file
            return result
        return {
            "success": True,
            "file": file,
            "before": source,
            "after": result["content"],
            "hunks_applied": result["hunks_applied"],
        }

    def apply_patch_to_files(
        self,
        *,
        patch: HunkPatch,
        sources: dict[str, str],
    ) -> dict[str, Any]:
        """批量应用到多个文件（源内容从 sources 取）。"""
        results: list[dict[str, Any]] = []
        for change in patch.changes:
            src = sources.get(change.file)
            if not isinstance(src, str):
                results.append({
                    "success": False,
                    "file": change.file,
                    "error": "source_unavailable",
                })
                continue
            results.append(
                self.apply_file_change(
                    file=change.file,
                    source=src,
                    change=change,
                )
            )

        all_ok = all(r.get("success") for r in results)
        return {
            "success": all_ok,
            "results": results,
            "files": patch.files(),
        }

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = ["HunkApplier"]
