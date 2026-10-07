"""Part 2 of registry.py."""
from __future__ import annotations
from backend.core.observability.silent import swallow

from .part1 import (AdapterMethod, AdapterSpec, AdapterTarget, Path, _DB_PATH, _FINETUNE_DIR, create_adapter_spec, json, sqlite3,)  # noqa
from .part1 import _dir_size_bytes  # noqa
from .part1 import delete_adapter_spec  # noqa
from .part1 import list_adapter_specs  # noqa
from .part1 import load_adapter_spec  # noqa
from .part1 import reset_adapter_specs  # noqa
from .part1 import save_adapter_spec  # noqa

def _infer_base_model(job_dir: Path) -> str:
    """从 job 目录里的 metadata 里推 base_model。"""
    for name in ("metadata.json", "job.json", "spec.json"):
        p = job_dir / name
        if not p.is_file():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict):
            spec = d.get("spec") or d
            base = spec.get("base_model") or d.get("base_model")
            if isinstance(base, str) and base.strip():
                return base.strip()
    # 兜底：读 adapter/adapter_config.json（PEFT 训练输出必有此文件）
    cfg = job_dir / "adapter" / "adapter_config.json"
    if cfg.is_file():
        try:
            d = json.loads(cfg.read_text(encoding="utf-8"))
            bm = d.get("base_model_name_or_path")
            if isinstance(bm, str) and bm.strip():
                return bm.strip()
        except Exception as e:
            swallow("finetune.deploy._registry_parts.part2:37", e, level="warn")
    return ""

def _infer_method(adapter_dir: Path) -> "AdapterMethod":
    """从 adapter_config.json 的 peft_type 推断 AdapterMethod。"""
    cfg = adapter_dir / "adapter_config.json"
    if not cfg.is_file():
        return AdapterMethod.LORA
    try:
        import json as _json
        d = _json.loads(cfg.read_text(encoding="utf-8"))
        pt = str(d.get("peft_type", "")).upper()
        if pt == "PREFIX_TUNING":
            return AdapterMethod.PREFIX
        if pt == "LORA":
            return AdapterMethod.LORA
    except Exception as e:
        swallow("finetune.deploy._registry_parts.part2:54", e, level="warn")
    return AdapterMethod.LORA

def _infer_source_job_id(job_dir: Path) -> str:
    """推断 source_job_id：目录名 → 记录文件 → store 反查。"""
    # 1. 目录名已是 job_id
    if job_dir.name.startswith("job-"):
        return job_dir.name

    # 2. 读 job 目录下可能存在的记录文件
    for name in ("job.json", "record.json", "spec.json", "metadata.json"):
        f = job_dir / name
        if not f.is_file():
            continue
        try:
            import json as _json
            d = _json.loads(f.read_text(encoding="utf-8"))
            jid = d.get("job_id") or (d.get("spec") or {}).get("job_id")
            if isinstance(jid, str) and jid.startswith("job-"):
                return jid
        except Exception:
            continue

    # 3. 从 store 反查：spec_json 里含 job_name / output_dir
    try:
        import sqlite3 as _sql
        with _sql.connect(_DB_PATH) as conn:
            rows = conn.execute(
                "SELECT job_id FROM finetune_jobs "
                "WHERE spec_json LIKE ? "
                "ORDER BY created_at DESC LIMIT 5",
                (f"%{job_dir.name}%",),
            ).fetchall()
            for (jid,) in rows:
                if isinstance(jid, str) and jid.startswith("job-"):
                    return jid
    except Exception as e:
        swallow("finetune.deploy._registry_parts.part2:91", e, level="warn")

    return ""

def scan_local_adapters(
    root: Path | None = None,
    register: bool = True,
) -> list[AdapterSpec]:
    """扫描 ~/.biancheng/finetune/<job_id>/adapter/ 目录。

    约定目录结构（训练输出）：
        ~/.biancheng/finetune/<job_id>/
            adapter/
                adapter_config.json
                adapter_model.safetensors  (或 adapter_model.bin)
                ...
    若同时存在 job 的 metadata，可反推 base_model。
    """
    base = root or _FINETUNE_DIR
    if not base.exists():
        return []

    found: list[AdapterSpec] = []
    for job_dir in sorted(base.iterdir()):
        if not job_dir.is_dir():
            continue
        adapter_dir = job_dir / "adapter"
        if not adapter_dir.is_dir():
            continue
        # 是否真 adapter（看关键文件）
        has_peft = (
            (adapter_dir / "adapter_config.json").is_file()
            or (adapter_dir / "adapter_model.safetensors").is_file()
            or (adapter_dir / "adapter_model.bin").is_file()
        )
        if not has_peft:
            continue

        size = _dir_size_bytes(adapter_dir)
        base_model = _infer_base_model(job_dir)
        name = job_dir.name
        source_job_id = _infer_source_job_id(job_dir)
        method = _infer_method(adapter_dir)

        # 去重：同 adapter_path 已有注册 → 复用旧 adapter_id
        existing = None
        try:
            with sqlite3.connect(_DB_PATH) as conn:
                row = conn.execute(
                    "SELECT adapter_id FROM finetune_adapters "
                    "WHERE adapter_path = ? LIMIT 1",
                    (str(adapter_dir),),
                ).fetchone()
                if row:
                    existing = load_adapter_spec(row[0])
        except Exception:
            existing = None

        if existing is not None:
            # AdapterSpec 是 frozen dataclass → 用 replace 重建
            from dataclasses import replace as _dc_replace
            spec = _dc_replace(
                existing,
                base_model=(base_model or existing.base_model or "unknown"),
                size_bytes=size,
                method=method,
            )
        else:
            spec = create_adapter_spec(
                name=name,
                base_model=base_model or "unknown",
                adapter_path=str(adapter_dir),
                method=method,
                target=AdapterTarget.OLLAMA,
                source_job_id=source_job_id,
                size_bytes=size,
                description="auto-discovered",
            )
        found.append(spec)
        if register:
            try: save_adapter_spec(spec)
            except Exception: pass
    return found

class AdapterRegistry:
    VERSION = "1.0"
    def save(self, spec): save_adapter_spec(spec)
    def load(self, aid): return load_adapter_spec(aid)
    def list(self, limit=100): return list_adapter_specs(limit=limit)
    def delete(self, aid): return delete_adapter_spec(aid)
    def reset(self): reset_adapter_specs()
    def scan(self, register=True): return scan_local_adapters(register=register)
    def ready(self): return True
    def dump(self):
        return {"name": type(self).__name__, "version": self.VERSION}

_registry: AdapterRegistry | None = None

def get_adapter_registry() -> AdapterRegistry:
    global _registry
    if _registry is None:
        _registry = AdapterRegistry()
    return _registry
