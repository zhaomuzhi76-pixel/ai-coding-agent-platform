"""PEFT LoRA adapter 合并到基础模型（fp16，隔离 transformers 4.44 子进程）。

为什么用子进程：
    - backend 主进程已 import transformers 5.x（用于训练）
    - 5.x 的 lazy import 在异步线程里会触发 BloomPreTrainedModel 等模块解析崩溃
    - 隔离到子进程 + PYTHONPATH=/tmp/tf4x 前缀，强制用 transformers 4.44
    - 主进程只编排，不接触模型加载
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable


_LogFn = Callable[[str], None] | None

_SUBPROCESS_SCRIPT = r'''
import sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

adapter_dir = sys.argv[1]
base_model  = sys.argv[2]
out_dir     = sys.argv[3]
dtype_str   = sys.argv[4] if len(sys.argv) > 4 else "float16"
dtype = getattr(torch, dtype_str, torch.float16)

print(f"[merge] 加载 base: {base_model}", flush=True)
model = AutoModelForCausalLM.from_pretrained(
    base_model, torch_dtype=dtype, trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)

print(f"[merge] 加载 adapter: {adapter_dir}", flush=True)

# ── 早检：只支持 LoRA 类（有权重可合并）；Prefix/Prompt/P-Tuning 拒绝 ──
import json as _json, sys as _sys
_cfg_path = f"{adapter_dir}/adapter_config.json"
try:
    with open(_cfg_path) as _f:
        _cfg = _json.load(_f)
except Exception as _e:
    print(f"[merge] 无法读 adapter_config.json: {_e}", flush=True)
    _sys.exit(2)

_pt = str(_cfg.get("peft_type", "")).upper()
if _pt not in ("LORA", "ADALORA", "IA3"):
    msg = (
        f"Prefix-Tuning / Prompt-Tuning 类 adapter 无法合并到 GGUF："
        f"  peft_type={_pt} 的 virtual tokens 属于输入层，不是权重增量。"
        f"  ollama 不支持动态注入 prefix → 只有 LoRA 类可部署。"
    )
    print(f"[merge] REJECT: {msg}", flush=True)
    _sys.exit(3)

model = PeftModel.from_pretrained(model, adapter_dir)

print("[merge] merge_and_unload", flush=True)
model = model.merge_and_unload()

print(f"[merge] 保存到 {out_dir}", flush=True)
model.save_pretrained(out_dir, safe_serialization=True)
tokenizer.save_pretrained(out_dir)
print("[merge] OK", flush=True)
'''


def _log(on_log: _LogFn, msg: str) -> None:
    if on_log is None:
        return
    try:
        on_log(msg)
    except Exception as e:
        swallow("finetune.deploy.merger:78", e)


def merge_adapter(
    adapter_dir: str,
    base_model: str,
    out_dir: str,
    *,
    dtype: str = "float16",
    on_log: _LogFn = None,
) -> Path:
    """子进程加载 base(fp16) + LoRA adapter → merge_and_unload → 保存。

    返回合并后的 HF 目录 Path。
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 用主环境 python：merge 需要 peft 0.21 + transformers 5.x 组合，
    # 而 tf4x venv 是 transformers 4.44（只服务 llama.cpp convert），
    # peft 0.21 与 4.44 不兼容（"text_config" in Qwen2Config 崩溃）
    py = sys.executable

    _log(on_log, f"[merge] 子进程合并 {adapter_dir} → {out_path}")
    proc = subprocess.run(
        [py, "-c", _SUBPROCESS_SCRIPT,
         str(adapter_dir), str(base_model), str(out_path), dtype],
        capture_output=True, text=True, timeout=900,
    )

    # 转发 stdout 到 on_log
    for line in (proc.stdout or "").splitlines():
        _log(on_log, line)

    if proc.returncode == 3:
        # 子进程已识别"非 LoRA 类"，直接抛清晰错误
        raise RuntimeError(
            "本 adapter 类型不支持部署：只有 LoRA 类可合并到 GGUF。"
            "Prefix-Tuning / Prompt-Tuning 的 virtual tokens 属于输入层，"
            "无法合并到权重，也无法注入 ollama。"
        )
    if proc.returncode != 0:
        # stdout 里含 [merge] REJECT: 消息，优先展示
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        tail = (out[-800:] + "\n---\n" + err[-400:])[-1200:]
        raise RuntimeError(f"merge 失败: {tail}")

    if not (out_path / "model.safetensors").is_file() and \
       not (out_path / "pytorch_model.bin").is_file():
        raise RuntimeError(f"merge 未产出权重文件: {out_path}")

    return out_path


__all__ = ["merge_adapter"]
