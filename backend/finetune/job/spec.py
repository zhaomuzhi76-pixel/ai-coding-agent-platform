"""训练任务规格（L0 · 纯数据）。

JobSpec 描述"提交一次训练需要什么"，**不含训练参数**（那是 FinetuneConfig）。

职责：
    - 定义任务提交所需字段（recipe / base_model / dataset / output_dir）
    - 序列化 / 反序列化
    - 校验

不负责：
    - 训练参数（FinetuneConfig 管）
    - 任务状态（state 管）
    - 持久化（store 管）

命名具体化：
    JobSpec 而非 Spec —— 避免与其它领域通用名冲突
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_JOB_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


@dataclass(frozen=True, slots=True)
class JobSpec:
    recipe_name: str
    base_model: str
    dataset_path: str
    output_dir: str
    job_name: str = ""
    description: str = ""
    tags: tuple = ()
    num_epochs: int = 0
    batch_size: int = 0
    learning_rate: float = 0.0
    max_seq_len: int = 0

    def __post_init__(self) -> None:
        for n in ("recipe_name", "base_model", "dataset_path", "output_dir"):
            v = getattr(self, n)
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"JobSpec.{n} required")
        if self.job_name and not _NAME_RE.match(self.job_name):
            raise ValueError("JobSpec.job_name invalid format")
        if not isinstance(self.tags, tuple):
            raise TypeError("JobSpec.tags must be tuple")

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_name": self.recipe_name,
            "base_model": self.base_model,
            "dataset_path": self.dataset_path,
            "output_dir": self.output_dir,
            "job_name": self.job_name,
            "description": self.description,
            "tags": list(self.tags),
            "num_epochs": self.num_epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "max_seq_len": self.max_seq_len,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "JobSpec":
        if not isinstance(d, dict):
            raise TypeError("JobSpec.from_dict expects dict")
        return cls(
            recipe_name=str(d.get("recipe_name", "")),
            base_model=str(d.get("base_model", "")),
            dataset_path=str(d.get("dataset_path", "")),
            output_dir=str(d.get("output_dir", "")),
            job_name=str(d.get("job_name", "")),
            description=str(d.get("description", "")),
            tags=tuple(str(t) for t in (d.get("tags") or ())),
            num_epochs=int(d.get("num_epochs", 0) or 0),
            batch_size=int(d.get("batch_size", 0) or 0),
            learning_rate=float(d.get("learning_rate", 0.0) or 0.0),
            max_seq_len=int(d.get("max_seq_len", 0) or 0),
        )

    def display_name(self) -> str:
        return self.job_name or f"{self.recipe_name}-{self.base_model.split('/')[-1]}"


def create_job_spec(
    recipe_name: str,
    base_model: str,
    dataset_path: str,
    output_dir: str,
    **kwargs: Any,
) -> JobSpec:
    return JobSpec(
        recipe_name=recipe_name,
        base_model=base_model,
        dataset_path=dataset_path,
        output_dir=output_dir,
        job_name=str(kwargs.get("job_name", "")),
        description=str(kwargs.get("description", "")),
        tags=tuple(str(t) for t in (kwargs.get("tags") or ())),
        num_epochs=int(kwargs.get("num_epochs", 0) or 0),
        batch_size=int(kwargs.get("batch_size", 0) or 0),
        learning_rate=float(kwargs.get("learning_rate", 0.0) or 0.0),
        max_seq_len=int(kwargs.get("max_seq_len", 0) or 0),
    )


__all__ = ["JobSpec", "create_job_spec"]
