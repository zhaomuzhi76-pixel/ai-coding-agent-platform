"""HF 模型目录 → GGUF（用隔离 transformers 4.44 + llama.cpp 转换脚本）。"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

from .env_bootstrap import LLAMA_CPP_DIR

_LogFn = Callable[[str], None] | None


def _log(on_log: _LogFn, msg: str) -> None:
    if on_log is None:
        return
    try:
        on_log(msg)
    except Exception as e:
        swallow("finetune.deploy.gguf_converter:22", e)


def _sync_tokenizer_from_cache(hf_dir: Path, base_model: str) -> None:
    """把 base 模型的原始 tokenizer 文件覆盖到 hf_dir（兼容 llama.cpp）。"""
    cache_root = Path.home() / ".cache" / "huggingface" / "hub"
    slug = "models--" + base_model.replace("/", "--")
    snaps = cache_root / slug / "snapshots"
    if not snaps.is_dir():
        return
    candidates = sorted([p for p in snaps.iterdir() if p.is_dir()])
    if not candidates:
        return
    base_snap = candidates[-1]
    for name in (
        "tokenizer.json", "tokenizer_config.json",
        "vocab.json", "merges.txt", "special_tokens_map.json",
    ):
        src = base_snap / name
        if src.is_file():
            try:
                (hf_dir / name).write_bytes(src.read_bytes())
            except Exception as e:
                swallow("finetune.deploy.gguf_converter:45", e)


def convert_hf_to_gguf(
    hf_dir: str,
    out_path: str,
    *,
    base_model: str = "",
    outtype: str = "f16",
    on_log: _LogFn = None,
) -> Path:
    """调用 llama.cpp convert_hf_to_gguf.py。返回 GGUF Path。"""
    src = Path(hf_dir)
    dst = Path(out_path)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if base_model:
        _log(on_log, "[gguf] 覆盖 tokenizer（base 原版）")
        _sync_tokenizer_from_cache(src, base_model)

    converter = LLAMA_CPP_DIR / "convert_hf_to_gguf.py"
    if not converter.is_file():
        raise RuntimeError(f"llama.cpp convert script 不存在: {converter}")

    _log(on_log, f"[gguf] 转换 {src} → {dst}")
    # 用隔离 venv 的 python（不污染主环境）
    from .env_bootstrap import tf4x_python
    py = str(tf4x_python())
    if not Path(py).is_file():
        raise RuntimeError(f"tf4x venv python 不存在: {py}")

    proc = subprocess.run(
        [py, str(converter), str(src),
         "--outfile", str(dst), "--outtype", outtype],
        capture_output=True, text=True, timeout=600,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-400:]
        raise RuntimeError(f"convert_hf_to_gguf 失败: {tail}")
    if not dst.is_file():
        raise RuntimeError(f"GGUF 未生成: {dst}")
    _log(on_log, f"[gguf] ✅ {dst.name} ({dst.stat().st_size // 1024 // 1024} MB)")
    return dst


__all__ = ["convert_hf_to_gguf"]
