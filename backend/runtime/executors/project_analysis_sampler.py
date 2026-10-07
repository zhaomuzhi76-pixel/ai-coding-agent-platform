from __future__ import annotations

from pathlib import Path
from typing import Any


class ProjectAnalysisSampler:
    """从项目抽取关键文件样本（README + 入口 + Top 符号文件）。"""

    VERSION = "1.0"
    SAMPLE_LINES = 80

    ENTRY_FILES = ("main.py", "app.py", "server.py", "__main__.py")
    README_FILES = (
        "README.md", "README.rst", "readme.md",
        "pyproject.toml", "package.json",
    )

    def sample(
        self,
        root: Path,
        *,
        max_files: int = 12,
    ) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        seen: set[str] = set()

        for name in self.README_FILES:
            self._add(root, name, seen, out, head=2000)

        for name in self.ENTRY_FILES:
            self._add(root, name, seen, out, head=self.SAMPLE_LINES)

        try:
            from backend.code_intelligence.runtime import (
                get_workspace_holder,
            )
            index = get_workspace_holder().get_index(str(root))
            ranked = sorted(
                [it for it in index if it.get("symbols")],
                key=lambda x: -len(x.get("symbols", [])),
            )
            for item in ranked[:max_files]:
                rel = item["path"]
                if rel in seen:
                    continue
                self._add(root, rel, seen, out, head=self.SAMPLE_LINES)
                if len(out) >= max_files:
                    break
        except Exception as error:
            print(
                f"[sampler] index sample failed: {error}",
                flush=True,
            )

        return out

    def _add(
        self,
        root: Path,
        rel: str,
        seen: set[str],
        out: list[dict[str, str]],
        *,
        head: int,
    ) -> None:
        if rel in seen:
            return
        p = root / rel
        if not p.exists() or not p.is_file():
            return
        seen.add(rel)
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            out.append({
                "path": rel,
                "content": "\n".join(text.split("\n")[:head]),
            })
        except OSError:
            pass

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = ["ProjectAnalysisSampler"]
