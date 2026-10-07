"""一次性引导：准备 llama.cpp + 隔离 venv（transformers 4.44）。

重要设计变更（v2）：
    旧版用 `pip install --target /tmp/tf4x` —— 不隔离依赖解析，
    会污染主环境的 torch / transformers / huggingface_hub，导致 ABI 崩溃。
    新版用 `python -m venv` 完全隔离，主环境零副作用。

职责：
    - ensure_llama_cpp()：clone llama.cpp 到 ~/.biancheng（幂等）
    - ensure_tf4x_venv()：建 venv + 装 transformers 4.44（幂等）
    - ensure_all()：两步合一

不负责：
    - merge / convert（merger / gguf_converter 管）
    - ollama create（deployer 管）
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import subprocess
import sys
from pathlib import Path
from typing import Callable

LLAMA_CPP_DIR = Path.home() / ".biancheng" / "llama.cpp"
TF4X_VENV_DIR = Path.home() / ".biancheng" / "tf4x-venv"
TF4X_VERSION = "4.44.2"
LLAMA_CPP_REPO = "https://github.com/ggerganov/llama.cpp.git"

_LogFn = Callable[[str], None] | None


def _log(on_log: _LogFn, msg: str) -> None:
    if on_log is None:
        return
    try:
        on_log(msg)
    except Exception as e:
        swallow("finetune.deploy.env_bootstrap:39", e)


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def ensure_llama_cpp(on_log: _LogFn = None) -> Path:
    converter = LLAMA_CPP_DIR / "convert_hf_to_gguf.py"
    if converter.is_file():
        _log(on_log, "[env] llama.cpp 已就绪")
        return LLAMA_CPP_DIR
    _log(on_log, "[env] 克隆 llama.cpp ...")
    LLAMA_CPP_DIR.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", LLAMA_CPP_REPO, str(LLAMA_CPP_DIR)],
        check=True, capture_output=True, text=True,
    )
    if not converter.is_file():
        raise RuntimeError("llama.cpp clone 失败")
    _log(on_log, "[env] llama.cpp 就绪")
    return LLAMA_CPP_DIR


def ensure_tf4x_venv(on_log: _LogFn = None) -> Path:
    """建 ~/.biancheng/tf4x-venv 并装 transformers 4.44。

    完全隔离：
        - venv 自带独立 site-packages
        - 主环境的 torch/transformers 零影响
    """
    py = _venv_python(TF4X_VENV_DIR)
    marker = TF4X_VENV_DIR / "pyvenv.cfg"

    if not marker.is_file():
        _log(on_log, f"[env] 创建 venv: {TF4X_VENV_DIR}")
        TF4X_VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
        # --system-site-packages：继承主环境的 torch/peft/datasets 等重包，
        # 只隔离 transformers（主 5.17 / venv 4.44 冲突）与它的私有依赖
        subprocess.run(
            [sys.executable, "-m", "venv", "--system-site-packages",
             str(TF4X_VENV_DIR)],
            check=True, capture_output=True, text=True,
        )

    # 幂等检查：装过 transformer 4.44 就不再动
    probe = subprocess.run(
        [str(py), "-c", "import transformers; print(transformers.__version__)"],
        capture_output=True, text=True,
    )
    if probe.returncode == 0 and TF4X_VERSION in probe.stdout:
        _log(on_log, f"[env] tf4x-venv 已就绪 (transformers {TF4X_VERSION})")
        return TF4X_VENV_DIR

    _log(on_log, f"[env] venv 装 transformers=={TF4X_VERSION}（隔离，不重装 torch）...")
    subprocess.run(
        [str(py), "-m", "pip", "install", "-q", "--upgrade", "pip"],
        check=True, capture_output=True, text=True,
    )
    # transformers --no-deps：主环境 torch/peft/safetensors/numpy 通过
    # --system-site-packages 继承，避免重装
    subprocess.run(
        [str(py), "-m", "pip", "install", "-q", "--no-deps",
         f"transformers=={TF4X_VERSION}"],
        check=True, capture_output=True, text=True,
    )
    # 只装 transformers 4.44 私有需要的（主环境是 5.x 的版本，需降级隔离）
    subprocess.run(
        [str(py), "-m", "pip", "install", "-q",
         "huggingface-hub>=0.23,<0.30",
         "tokenizers>=0.19,<0.20"],
        check=True, capture_output=True, text=True,
    )
    _log(on_log, "[env] tf4x-venv 就绪")
    return TF4X_VENV_DIR


def ensure_all(on_log: _LogFn = None) -> dict:
    llama = ensure_llama_cpp(on_log)
    venv = ensure_tf4x_venv(on_log)
    return {"llama_cpp": str(llama), "tf4x_venv": str(venv)}


def tf4x_python() -> Path:
    """返回 tf4x venv 里的 python 可执行文件路径。"""
    return _venv_python(TF4X_VENV_DIR)


__all__ = [
    "ensure_llama_cpp", "ensure_tf4x_venv", "ensure_all", "tf4x_python",
    "LLAMA_CPP_DIR", "TF4X_VENV_DIR",
]
