from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class SessionLog:
    """
    Append-only JSONL 事件流（Codex 风格）。

    每个 workspace 一份日志：~/.biancheng/projects/{hash}/session.jsonl
    用于审计、调试、事实重放。
    """

    VERSION = "1.0"

    def __init__(self, workspace: str) -> None:
        import hashlib
        key = str(Path(workspace).expanduser().resolve())
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
        root = Path.home() / ".biancheng" / "projects" / digest
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / "session.jsonl"

    def append(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        record = {
            "ts": time.time(),
            "type": event_type,
            **payload,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def replay(self, limit: int = 1000) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return events[-limit:]

    def stats(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"events": 0, "path": str(self.path)}
        n = sum(1 for _ in open(self.path, encoding="utf-8"))
        return {"events": n, "path": str(self.path),
                "size": self.path.stat().st_size}


__all__ = ["SessionLog"]
