"""数据集规格（D4-L0 · 纯数据）。

职责：
    - DatasetSpec：数据集元数据（id / name / path / 格式 / 统计）
    - DatasetFormat 枚举
    - 序列化 / 校验

不负责：
    - 文件读写（storage 管）
    - 内容校验（validator 管）
    - HTTP（api 管）

命名：
    DatasetSpec · 避免与 finetune/config / recipe / job/spec 冲突
"""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

DATASET_ID_PREFIX = "ds-"
DATASET_DIR_NAME = "datasets"
_NAME_RE = re.compile(r"^[A-Za-z0-9_\-\u4e00-\u9fa5]{1,80}$")


class DatasetFormat(str, Enum):
    JSONL = "jsonl"


def new_dataset_id() -> str:
    return DATASET_ID_PREFIX + uuid.uuid4().hex[:12]


@dataclass(frozen=True, slots=True)
class DatasetSpec:
    dataset_id: str
    name: str
    path: str
    format: DatasetFormat = DatasetFormat.JSONL
    description: str = ""
    sample_count: int = 0
    size_bytes: int = 0
    created_at: float = field(default_factory=time.time)
    tags: tuple = ()

    def __post_init__(self) -> None:
        if not isinstance(self.dataset_id, str) or not self.dataset_id:
            raise ValueError("DatasetSpec.dataset_id required")
        if not self.dataset_id.startswith(DATASET_ID_PREFIX):
            raise ValueError(
                f"DatasetSpec.dataset_id must start with {DATASET_ID_PREFIX!r}"
            )
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("DatasetSpec.name required")
        if not _NAME_RE.match(self.name.strip()):
            raise ValueError("DatasetSpec.name invalid format")
        if not isinstance(self.path, str) or not self.path.strip():
            raise ValueError("DatasetSpec.path required")
        if not isinstance(self.format, DatasetFormat):
            raise TypeError("DatasetSpec.format must DatasetFormat")
        if self.sample_count < 0:
            raise ValueError("DatasetSpec.sample_count must be >= 0")
        if self.size_bytes < 0:
            raise ValueError("DatasetSpec.size_bytes must be >= 0")
        if not isinstance(self.tags, tuple):
            raise TypeError("DatasetSpec.tags must be tuple")

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "path": self.path,
            "format": self.format.value,
            "description": self.description,
            "sample_count": int(self.sample_count),
            "size_bytes": int(self.size_bytes),
            "created_at": float(self.created_at),
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DatasetSpec":
        if not isinstance(d, dict):
            raise TypeError("DatasetSpec.from_dict expects dict")
        try:
            fmt = DatasetFormat(str(d.get("format", "jsonl")))
        except ValueError:
            fmt = DatasetFormat.JSONL
        return cls(
            dataset_id=str(d.get("dataset_id", "")),
            name=str(d.get("name", "")),
            path=str(d.get("path", "")),
            format=fmt,
            description=str(d.get("description", "")),
            sample_count=int(d.get("sample_count", 0)),
            size_bytes=int(d.get("size_bytes", 0)),
            created_at=float(d.get("created_at", time.time())),
            tags=tuple(str(t) for t in (d.get("tags") or ())),
        )


def create_dataset_spec(
    name: str,
    path: str,
    *,
    format: DatasetFormat = DatasetFormat.JSONL,
    description: str = "",
    sample_count: int = 0,
    size_bytes: int = 0,
    tags: list | tuple | None = None,
) -> DatasetSpec:
    return DatasetSpec(
        dataset_id=new_dataset_id(),
        name=name,
        path=path,
        format=format,
        description=description,
        sample_count=sample_count,
        size_bytes=size_bytes,
        tags=tuple(str(t) for t in (tags or ())),
    )


__all__ = [
    "DatasetSpec", "DatasetFormat",
    "DATASET_ID_PREFIX", "DATASET_DIR_NAME",
    "new_dataset_id", "create_dataset_spec",
]
