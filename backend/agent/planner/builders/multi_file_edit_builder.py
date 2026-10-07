from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.agent.planner.builders.base import BaseStepBuilder
from backend.agent.planner.models.plan_step import PlanStep


_EXCLUDE_PARTS = frozenset({
    "node_modules", ".git", ".venv", "venv", "__pycache__",
    ".idea", ".vscode", "dist", "build", "target",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
})

_MAX_FILES = 200
_MAX_SYMBOL_FILES = 15


class MultiFileEditBuilder(BaseStepBuilder):
    """
    Build ONE multi_file_modify step.

    Three-tier file selection (first non-empty wins):
        1. explicit `pattern`  -> glob (e.g. "所有 .py" workload)
        2. symbol retrieval    -> prompt mentions a symbol/class/function
        3. default             -> all .py (fallback for generic tasks)

    The executor makes a single LLM call and reuses the template
    across all selected files.
    """

    VERSION = "3.0"
    RESPONSIBILITY = ("multi_file_edit_plan_step_builder",)

    def build(
        self,
        context: dict[str, Any] | None = None,
    ) -> list[PlanStep]:
        context = context or {}

        workspace = context.get("workspace") or "."
        pattern = context.get("pattern")
        instruction = (
            context.get("message")
            or context.get("instruction")
            or ""
        )

        root = Path(workspace).expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"workspace not a directory: {root}")

        files, strategy = self._select_files(
            workspace=str(root),
            pattern=pattern,
            instruction=instruction,
            root=root,
        )

        if not files:
            raise ValueError(
                f"no files selected (strategy={strategy})"
            )

        print(
            f"[multi-file-builder] strategy={strategy} "
            f"matched={len(files)} files",
            flush=True,
        )
        for f in files[:5]:
            print(f"[multi-file-builder]   - {f}", flush=True)
        if len(files) > 5:
            print(
                f"[multi-file-builder]   ... {len(files) - 5} more",
                flush=True,
            )

        return [self._make_step(files, instruction)]

    def _select_files(
        self,
        *,
        workspace: str,
        pattern: Any,
        instruction: str,
        root: Path,
    ) -> tuple[list[str], str]:
        # ── 1. 明确 pattern ─────────────────────────
        if isinstance(pattern, str) and pattern.strip():
            files = self._scan(root, pattern.strip())
            if files:
                return files, f"pattern:{pattern.strip()}"

        # ── 2. 符号检索 ─────────────────────────────
        try:
            files = self._retrieve_by_symbols(workspace, instruction)
        except Exception as error:
            print(
                f"[multi-file-builder] symbol retrieval failed: {error}",
                flush=True,
            )
            files = []
        if files:
            return files, "symbol-retrieval"

        # ── 3. 默认：全部 .py ────────────────────────
        files = self._scan(root, "**/*.py")
        return files, "default:all-py"

    @staticmethod
    def _retrieve_by_symbols(
        workspace: str,
        prompt: str,
    ) -> list[str]:
        if not prompt.strip():
            return []

        # 延迟 import，避免构建期循环依赖
        from backend.code_intelligence.runtime import (
            SymbolRetriever,
            get_workspace_holder,
        )

        holder = get_workspace_holder()
        index = holder.get_index(workspace)
        if not index:
            return []

        result = SymbolRetriever().retrieve(
            prompt=prompt,
            index=index,
            max_files=_MAX_SYMBOL_FILES,
        )

        tokens = result.get("tokens", [])
        files = result.get("files", [])
        print(
            f"[multi-file-builder] symbol tokens={tokens} "
            f"files={len(files)}",
            flush=True,
        )
        return files

    @staticmethod
    def _scan(root: Path, pattern: str) -> list[str]:
        out: list[str] = []
        try:
            iterator = root.glob(pattern)
        except Exception as error:
            raise ValueError(
                f"invalid glob pattern {pattern!r}: {error}"
            ) from error

        for path in iterator:
            try:
                if not path.is_file():
                    continue
                if path.stat().st_size == 0:
                    continue
                rel = path.relative_to(root)
            except (OSError, ValueError):
                continue

            if set(rel.parts) & _EXCLUDE_PARTS:
                continue

            out.append(str(rel))
            if len(out) >= _MAX_FILES:
                break

        out.sort()
        return out

    @staticmethod
    def _make_step(
        files: list[str],
        instruction: str,
    ) -> PlanStep:
        return PlanStep.create(
            executor_type="multi_file_modify",
            description=f"批量修改 {len(files)} 个文件",
            parameters={
                "files": files,
                "instruction": instruction,
                "message": instruction,
            },
        )

    def validate(
        self,
        steps: list[PlanStep],
    ) -> bool:
        if not steps:
            return False
        for step in steps:
            if not isinstance(step, PlanStep):
                return False
            if step.executor_type != "multi_file_modify":
                return False
        return True

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = ["MultiFileEditBuilder"]
