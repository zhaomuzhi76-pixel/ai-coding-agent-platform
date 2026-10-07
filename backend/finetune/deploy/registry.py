"""Adapter 注册表（D5-L1）。

职责：
    - 扫描 ~/.biancheng/finetune/*/adapter/ 目录自动发现 adapter
    - SQLite 持久化 AdapterSpec（表 finetune_adapters）
    - 单例 get_adapter_registry()

不负责：
    - 生成 Modelfile（modelfile 管）
    - 执行部署（deployer 管）
    - 挂载到 providers（mount 管）
\n\nCompat shim. See ._registry_parts."""
from __future__ import annotations
from ._registry_parts import *  # noqa
from ._registry_parts import (AdapterMethod, AdapterRegistry, AdapterSpec, AdapterTarget, Any, MergeMode, Path, _DB_DIR, _DB_PATH, _FINETUNE_DIR, __all__, _dir_size_bytes, _ensure_schema, _infer_base_model, _infer_method, _infer_source_job_id, _registry, annotations, create_adapter_spec, delete_adapter_spec, get_adapter_registry, json, list_adapter_specs, load_adapter_spec, reset_adapter_registry, reset_adapter_specs, save_adapter_spec, scan_local_adapters, sqlite3, time,)  # noqa
