"""数据集管理器（D4-L1 · 上传编排 + 单例）。

职责：
    - 上传编排：接收字节 → 写临时文件 → 校验 → 通过则转正 + 落元数据
    - 查询：list / get / stats
    - 删除：文件 + 元数据双清
    - 单例：get_dataset_manager()

不负责：
    - HTTP 协议（api 管）
    - 内容校验逻辑（validator 管）
    - 文件/元数据读写细节（storage 管）

上传流程：
    1. name 校验（spec 管）
    2. 生成 dataset_id
    3. 写临时文件 → validate_jsonl
    4. 若 ok：转正到 ~/.biancheng/datasets/<id>.jsonl
    5. 若 !ok：删临时文件，抛 ValueError（带 issues）
    6. 落元数据
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from .spec import DatasetSpec, create_dataset_spec
from .validator import validate_jsonl, ValidationReport
from . import storage as _st


class DatasetManager:
    VERSION = "1.0"

    def __init__(self) -> None:
        _st.ensure_dataset_dir()

    # ── 上传 ──
    def upload(
        self,
        name: str,
        content: bytes,
        *,
        description: str = "",
        tags: list | None = None,
    ) -> DatasetSpec:
        """上传数据集：校验 → 转正 → 落元数据。

        校验失败抛 ValueError（含 issues）。
        """
        if not isinstance(content, (bytes, bytearray)):
            raise TypeError("content must bytes")
        if not content:
            raise ValueError("empty content")

        # 1. 写临时文件校验
        tmp = tempfile.NamedTemporaryFile(
            "wb", suffix=".jsonl", delete=False,
        )
        try:
            tmp.write(bytes(content))
            tmp.close()
            report: ValidationReport = validate_jsonl(tmp.name)
        finally:
            try: Path(tmp.name).unlink()
            except OSError: pass

        if not report.ok:
            first = report.issues[0] if report.issues else None
            detail = (
                f"line {first.line_no}: {first.message}"
                if first else "unknown validation error"
            )
            raise ValueError(
                f"dataset validation failed: {detail} "
                f"(errors={report.error_count})"
            )

        # 2. 先生成 id → 写文件 → 拿到真实 path
        from .spec import new_dataset_id, DATASET_ID_PREFIX
        dataset_id = new_dataset_id()
        path = _st.save_dataset_file(dataset_id, bytes(content))

        # 3. 用真实 path 构造 spec（frozen）
        spec = create_dataset_spec(
            name=name,
            path=path,
            description=description,
            sample_count=report.sample_count,
            size_bytes=report.size_bytes,
            tags=tags,
        )
        # 用真实 dataset_id 覆盖（create_dataset_spec 自带新 id，需重造）
        spec = DatasetSpec(
            dataset_id=dataset_id,
            name=spec.name,
            path=spec.path,
            format=spec.format,
            description=spec.description,
            sample_count=spec.sample_count,
            size_bytes=spec.size_bytes,
            created_at=spec.created_at,
            tags=spec.tags,
        )
        _st.save_dataset_metadata(spec)
        return spec

    def update(
        self,
        dataset_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        tags: list | None = None,
    ) -> DatasetSpec:
        """更新 dataset 元数据（name/description/tags）。找不到抛 KeyError。"""
        spec = _st.update_dataset_metadata(
            dataset_id, name=name, description=description, tags=tags,
        )
        if spec is None:
            raise KeyError(f"dataset not found: {dataset_id}")
        return spec

    # ── 查询 ──
    def list(self, limit: int = 100) -> list[dict]:
        return _st.list_dataset_metadata(limit=limit)

    def get(self, dataset_id: str) -> DatasetSpec | None:
        return _st.load_dataset_metadata(dataset_id)

    def validate_upload(
        self, content: bytes,
    ) -> ValidationReport:
        """预校验（不落盘）。供前端"先看报告再确认"。"""
        if not isinstance(content, (bytes, bytearray)):
            raise TypeError("content must bytes")
        tmp = tempfile.NamedTemporaryFile(
            "wb", suffix=".jsonl", delete=False,
        )
        try:
            tmp.write(bytes(content))
            tmp.close()
            return validate_jsonl(tmp.name)
        finally:
            try: Path(tmp.name).unlink()
            except OSError: pass

    # ── 删除 ──
    def delete(self, dataset_id: str) -> bool:
        meta_gone = _st.delete_dataset_metadata(dataset_id)
        file_gone = _st.delete_dataset_file(dataset_id)
        return meta_gone or file_gone

    def reset(self) -> None:
        _st.reset_dataset_metadata()
        # 清文件
        try:
            for p in _st.ensure_dataset_dir().glob("*.jsonl"):
                p.unlink()
        except OSError:
            pass

    def stats(self) -> dict:
        rows = _st.list_dataset_metadata(limit=10000)
        total_samples = sum(int(r.get("sample_count") or 0) for r in rows)
        total_bytes = sum(int(r.get("size_bytes") or 0) for r in rows)
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "datasets": len(rows),
            "total_samples": total_samples,
            "total_bytes": total_bytes,
            "dir": str(_st.ensure_dataset_dir()),
        }

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return self.stats()


# ── 单例 ──
_manager: DatasetManager | None = None


def get_dataset_manager() -> DatasetManager:
    global _manager
    if _manager is None:
        _manager = DatasetManager()
    return _manager


def reset_dataset_manager() -> None:
    """测试用：清单例。"""
    global _manager
    _manager = None


__all__ = [
    "DatasetManager",
    "get_dataset_manager",
    "reset_dataset_manager",
]
