"""CodingRequest: user request contract (frontend -> backend)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CodingRequest:
    """Unified request from frontend.

    - model / locale: user-chosen, backend must honor them
    - files: target files (relative paths)
    - task: natural-language description
    """

    task: str
    files: List[str]
    workspace: str = ""
    model: str = ""
    locale: str = "zh-CN"
    user_id: str = ""
    session_id: Optional[str] = None
    instruction: str = ""
    changes: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not isinstance(self.task, str) or not self.task.strip():
            raise ValueError("task required")
        if not isinstance(self.files, list) or not self.files:
            raise ValueError("files required")
        if not self.workspace or not self.workspace.strip():
            raise ValueError("workspace required")
        if not self.model or not self.model.strip():
            raise ValueError("model required (user must select)")

    def normalized_files(self) -> List[str]:
        seen = set()
        out: List[str] = []
        for f in self.files:
            if not isinstance(f, str):
                continue
            key = f.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(key)
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "files": list(self.files),
            "workspace": self.workspace,
            "model": self.model,
            "locale": self.locale,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "instruction": self.instruction,
            "changes": dict(self.changes) if self.changes else None,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodingRequest":
        return cls(
            task=str(data.get("task", "")),
            files=list(data.get("files", []) or []),
            workspace=str(data.get("workspace", "")),
            model=str(data.get("model", "")),
            locale=str(data.get("locale", "zh-CN")),
            user_id=str(data.get("user_id", "")),
            session_id=data.get("session_id"),
            instruction=str(data.get("instruction", "")),
            changes=data.get("changes"),
            metadata=dict(data.get("metadata", {})),
        )

    def dump(self) -> Dict[str, Any]:
        return self.to_dict()


__all__ = ["CodingRequest"]
