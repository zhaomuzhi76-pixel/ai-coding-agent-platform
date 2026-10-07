"""Adapter 规格（D5-L0 · 纯数据）。"""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

ADAPTER_ID_PREFIX = "adp-"
_NAME_RE = re.compile(r"^[A-Za-z0-9_\-\u4e00-\u9fa5]{1,80}$")
_OLLAMA_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.\-:]{0,63}$")


class AdapterMethod(str, Enum):
    LORA = "lora"
    PREFIX = "prefix"


class AdapterTarget(str, Enum):
    OLLAMA = "ollama"
    PEFT_MERGED = "peft_merged"


class MergeMode(str, Enum):
    ADAPTER_ONLY = "adapter_only"
    MERGED = "merged"
    MERGED_GGUF = "merged_gguf"


def new_adapter_id() -> str:
    return ADAPTER_ID_PREFIX + uuid.uuid4().hex[:12]


@dataclass(frozen=True, slots=True)
class AdapterSpec:
    adapter_id: str
    name: str
    base_model: str
    adapter_path: str
    method: AdapterMethod
    target: AdapterTarget = AdapterTarget.OLLAMA
    merge_mode: MergeMode = MergeMode.ADAPTER_ONLY
    ollama_model_name: str = ""
    source_job_id: str = ""
    size_bytes: int = 0
    created_at: float = field(default_factory=time.time)
    description: str = ""
    tags: tuple = ()

    def __post_init__(self) -> None:
        if not isinstance(self.adapter_id, str) or not self.adapter_id:
            raise ValueError("AdapterSpec.adapter_id required")
        if not self.adapter_id.startswith(ADAPTER_ID_PREFIX):
            raise ValueError(
                "AdapterSpec.adapter_id must start with " + repr(ADAPTER_ID_PREFIX)
            )
        if not isinstance(self.name, str) or not _NAME_RE.match(self.name.strip()):
            raise ValueError("AdapterSpec.name invalid format")
        if not isinstance(self.base_model, str) or not self.base_model.strip():
            raise ValueError("AdapterSpec.base_model required")
        if not isinstance(self.adapter_path, str) or not self.adapter_path.strip():
            raise ValueError("AdapterSpec.adapter_path required")
        if not isinstance(self.method, AdapterMethod):
            raise TypeError("AdapterSpec.method must AdapterMethod")
        if not isinstance(self.target, AdapterTarget):
            raise TypeError("AdapterSpec.target must AdapterTarget")
        if not isinstance(self.merge_mode, MergeMode):
            raise TypeError("AdapterSpec.merge_mode must MergeMode")
        if self.ollama_model_name and not _OLLAMA_NAME_RE.match(self.ollama_model_name):
            raise ValueError("AdapterSpec.ollama_model_name invalid")
        if self.size_bytes < 0:
            raise ValueError("AdapterSpec.size_bytes must be >= 0")
        if not isinstance(self.tags, tuple):
            raise TypeError("AdapterSpec.tags must be tuple")

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "name": self.name,
            "base_model": self.base_model,
            "adapter_path": self.adapter_path,
            "method": self.method.value,
            "target": self.target.value,
            "merge_mode": self.merge_mode.value,
            "ollama_model_name": self.ollama_model_name,
            "source_job_id": self.source_job_id,
            "size_bytes": int(self.size_bytes),
            "created_at": float(self.created_at),
            "description": self.description,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AdapterSpec":
        if not isinstance(d, dict):
            raise TypeError("AdapterSpec.from_dict expects dict")
        try: method = AdapterMethod(str(d.get("method", "lora")))
        except ValueError: method = AdapterMethod.LORA
        try: target = AdapterTarget(str(d.get("target", "ollama")))
        except ValueError: target = AdapterTarget.OLLAMA
        try: merge_mode = MergeMode(str(d.get("merge_mode", "adapter_only")))
        except ValueError: merge_mode = MergeMode.ADAPTER_ONLY
        return cls(
            adapter_id=str(d.get("adapter_id", "")),
            name=str(d.get("name", "")),
            base_model=str(d.get("base_model", "")),
            adapter_path=str(d.get("adapter_path", "")),
            method=method, target=target, merge_mode=merge_mode,
            ollama_model_name=str(d.get("ollama_model_name", "")),
            source_job_id=str(d.get("source_job_id", "")),
            size_bytes=int(d.get("size_bytes", 0)),
            created_at=float(d.get("created_at", time.time())),
            description=str(d.get("description", "")),
            tags=tuple(str(t) for t in (d.get("tags") or ())),
        )


def create_adapter_spec(
    name: str,
    base_model: str,
    adapter_path: str,
    *,
    method: AdapterMethod = AdapterMethod.LORA,
    target: AdapterTarget = AdapterTarget.OLLAMA,
    merge_mode: MergeMode = MergeMode.ADAPTER_ONLY,
    ollama_model_name: str = "",
    source_job_id: str = "",
    size_bytes: int = 0,
    description: str = "",
    tags: list | tuple | None = None,
) -> AdapterSpec:
    return AdapterSpec(
        adapter_id=new_adapter_id(),
        name=name, base_model=base_model, adapter_path=adapter_path,
        method=method, target=target, merge_mode=merge_mode,
        ollama_model_name=ollama_model_name,
        source_job_id=source_job_id,
        size_bytes=size_bytes, description=description,
        tags=tuple(str(t) for t in (tags or ())),
    )


def validate_adapter_spec(spec: AdapterSpec) -> list[str]:
    errs: list[str] = []
    if not isinstance(spec, AdapterSpec):
        return ["not an AdapterSpec"]
    from pathlib import Path
    p = Path(spec.adapter_path)
    if not p.exists():
        errs.append("adapter_path not exist: " + str(p))
    if spec.target == AdapterTarget.OLLAMA and not spec.ollama_model_name:
        errs.append("target=ollama but ollama_model_name empty")
    return errs


__all__ = [
    "AdapterSpec", "AdapterMethod", "AdapterTarget", "MergeMode",
    "ADAPTER_ID_PREFIX", "new_adapter_id", "create_adapter_spec",
    "validate_adapter_spec",
]
