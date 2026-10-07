"""Adapter 部署器（D5-L1 · ollama create 封装）。

职责：
    - build_deploy_plan：生成 Modelfile + 部署命令（不执行）
    - run_deploy：subprocess 调 ollama create（同步 → to_thread）
    - 支持超时 + 日志回调

不负责：
    - Modelfile 内容（modelfile 管）
    - adapter 元数据（spec / registry 管）
    - 挂载到 providers（mount 管）
\n\nCompat shim. See ._deployer_parts."""
from __future__ import annotations
from ._deployer_parts import *  # noqa
from ._deployer_parts import (AdapterSpec, Any, Callable, DEFAULT_TIMEOUT_SEC, DeployPlan, DeployResult, OLLAMA_BIN, Path, __all__, _run_sync, _suggest_name, annotations, asyncio, build_deploy_plan, build_modelfile, dataclass, field, is_ollama_available, run_deploy, run_merged_gguf_deploy, shutil, subprocess, time,)  # noqa
