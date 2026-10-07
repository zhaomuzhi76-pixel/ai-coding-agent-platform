"""批量原子 patch 执行 + 失败回滚。

PatchExecutor 单文件；本类负责：
    1. 逐个 execute
    2. 任一失败 → 用已成功的 old_content 逆序恢复
    3. 全成功 → 返回汇总
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List

# 大文件阈值：超过此大小，old_content 落盘（避免 100K 行入内存）
DISK_SPILLOVER_BYTES = 1 * 1024 * 1024


class BatchPatchExecutor:
    VERSION = "1.0"

    def __init__(self, executor: Any) -> None:
        if executor is None:
            raise ValueError("executor required")
        self._executor = executor
        self.batch_count = 0
        self.rollback_count = 0
        self._backup_root = None  # 懒初始化

    def execute_batch(
        self,
        patches: List[Dict[str, Any]],
        *,
        root: str,
        on_chunk: Any = None,
    ) -> Dict[str, Any]:
        self.batch_count += 1

        def _on(ev: Dict[str, Any]) -> None:
            if on_chunk is None:
                return
            try:
                on_chunk(ev)
            except Exception as e:
                swallow("platform.multi_file.batch_executor:47", e)

        if not patches:
            return {"success": False, "error": "empty patches"}

        applied: List[Dict[str, Any]] = []
        results: List[Dict[str, Any]] = []

        total = len(patches)
        for idx, patch in enumerate(patches):
            fname = patch.get("file", "?")
            _on({"file": fname, "status": "start",
                 "index": idx, "total": total})
            result = self._executor.execute(patch, root=root)
            results.append(result)
            if not result.get("success"):
                _on({"file": fname, "status": "failed",
                     "index": idx, "total": total,
                     "error": str(result.get("error", ""))[:200]})
                rolled = self._rollback(applied, root=root)
                return {
                    "success": False,
                    "executed": len(results),
                    "failed_at": patch.get("file"),
                    "results": results,
                    "rolled_back": rolled,
                }
            self._prepare_applied(patch, root=root)
            applied.append(patch)
            _on({"file": fname, "status": "done",
                 "index": idx, "total": total})

        return {
            "success": True,
            "executed": len(results),
            "results": results,
        }

    def _ensure_backup_root(self) -> str:
        if self._backup_root is None:
            self._backup_root = tempfile.mkdtemp(prefix="bc_batch_")
        return self._backup_root

    def _prepare_applied(
        self, patch: Dict[str, Any], *, root: str,
    ) -> None:
        """大文件 old_content 落盘，patch 里加 _backup_path 供 _rollback 读取。"""
        old = patch.get("old_content")
        if not isinstance(old, str):
            return
        if len(old.encode("utf-8")) < DISK_SPILLOVER_BYTES:
            return  # 小文件仍走内存
        try:
            backup_root = self._ensure_backup_root()
            key = str(abs(hash(patch.get("file", ""))))[:12]
            backup_path = os.path.join(backup_root, f"{key}.bak")
            with open(backup_path, "w", encoding="utf-8") as fh:
                fh.write(old)
            patch["_backup_path"] = backup_path
            patch["_old_content_dropped"] = True
            patch["old_content"] = None  # 释放内存
        except Exception:
            patch["_backup_path"] = None

    def _cleanup_backups(self) -> None:
        if self._backup_root is None:
            return
        try:
            shutil.rmtree(self._backup_root, ignore_errors=True)
        except Exception as e:
            swallow("platform.multi_file.batch_executor:117", e)
        self._backup_root = None

    def _rollback(
        self, applied: List[Dict[str, Any]], *, root: str,
    ) -> bool:
        from backend.code_intelligence.patch_writer import PatchWriter
        writer = PatchWriter()
        ok = True
        for patch in reversed(applied):
            try:
                target = os.path.join(root, patch["file"])
                content = patch.get("old_content")
                if content is None and patch.get("_backup_path"):
                    with open(patch["_backup_path"], "r", encoding="utf-8") as fh:
                        content = fh.read()
                if content is None:
                    ok = False
                    continue
                writer.write(target, content)
            except Exception:
                ok = False
        self.rollback_count += 1
        self._cleanup_backups()
        return ok

    def ready(self) -> bool:
        return self._executor is not None

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "batches": self.batch_count,
            "rollbacks": self.rollback_count,
            "spillover_threshold_bytes": DISK_SPILLOVER_BYTES,
        }


__all__ = ["BatchPatchExecutor"]
