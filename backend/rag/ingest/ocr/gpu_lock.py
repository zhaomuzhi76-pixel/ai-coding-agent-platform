"""跨进程 GPU 独占锁。原则：谁做任务谁独占 GPU。
机制：
  1. 文件锁 + holder 标记（~/.cache/agent_knowledge/gpu.lock）
  2. acquire 时主动驱逐其他组件（Ollama/Reranker）
  3. 等待显存回收后才返回
  4. release 时清空 holder（不主动恢复，让下一个任务抢）
"""
from __future__ import annotations
import json
import logging
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

LOCK_PATH = Path(os.path.expanduser("~/.cache/agent_knowledge/gpu.lock"))
OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
RERANKER_BASE = os.environ.get(
    "RERANKER_URL",
    f"http://127.0.0.1:{os.environ.get('RERANKER_PORT', '9033')}")


def _read_holder() -> str:
    try:
        if LOCK_PATH.exists():
            data = json.loads(LOCK_PATH.read_text())
            return data.get("holder", "")
    except Exception:
        pass
    return ""


def _write_holder(holder: str, need_mb: int = 0) -> None:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(json.dumps({
        "holder": holder,
        "need_mb": need_mb,
        "ts": time.time(),
    }))


def _free_vram_mb() -> int:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.free",
             "--format=csv,noheader,nounits"],
            text=True, timeout=3)
        return int(out.strip().split("\n")[0])
    except Exception:
        return -1


def _release_ollama() -> int:
    """卸载 Ollama 所有已加载模型。"""
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE}/api/ps", timeout=2) as r:
            models = json.loads(r.read()).get("models", [])
        n = 0
        for m in models:
            name = m.get("name") or m.get("model")
            if not name: continue
            body = json.dumps({"model": name, "keep_alive": 0}).encode()
            req = urllib.request.Request(
                f"{OLLAMA_BASE}/api/generate", data=body,
                headers={"Content-Type": "application/json"}, method="POST")
            try:
                urllib.request.urlopen(req, timeout=3).read()
                n += 1
            except Exception:
                pass
        if n:
            logger.info("[gpu-lock] 已驱逐 Ollama %d 个模型", n)
        return n
    except Exception:
        return 0


def _release_reranker() -> bool:
    try:
        req = urllib.request.Request(f"{RERANKER_BASE}/unload", method="POST")
        with urllib.request.urlopen(req, timeout=3) as r:
            ok = r.status == 200
        if ok:
            logger.info("[gpu-lock] 已驱逐 Reranker")
        return ok
    except Exception:
        return False


def _evict(holder: str) -> None:
    """按 holder 名字驱逐对应组件。"""
    if holder == "ollama":
        _release_ollama()
    elif holder == "reranker":
        _release_reranker()
    elif holder == "ocr":
        # OCR 让位给其他 → 不主动杀，记录日志
        logger.info("[gpu-lock] OCR 让位，等它主动释放")


def acquire(owner: str, need_mb: int = 3500, wait_s: float = 30.0) -> bool:
    """抢占 GPU 独占锁。"""
    logger.info("[gpu-lock] %s 请求 GPU（需 %dMB）", owner, need_mb)

    # 1. 检查 holder
    cur = _read_holder()
    if cur and cur != owner:
        logger.info("[gpu-lock] 当前 holder=%s，驱逐中...", cur)
        _evict(cur)
        time.sleep(1.5)
    elif cur == owner:
        return True

    # 2. 主动驱逐其他（保险起见全部检查）
    if owner != "ollama":
        _release_ollama()
    if owner != "reranker":
        _release_reranker()

    # 3. 等显存回收
    deadline = time.time() + wait_s
    while time.time() < deadline:
        free = _free_vram_mb()
        if free >= need_mb:
            _write_holder(owner, need_mb)
            logger.info("[gpu-lock] %s 获得 GPU（空闲 %dMB）", owner, free)
            return True
        time.sleep(0.5)

    free = _free_vram_mb()
    logger.warning("[gpu-lock] %s 超时未获得足够显存（%d < %d）",
                    owner, free, need_mb)
    return False


def release(owner: str) -> None:
    """释放锁（把 holder 清空，让下一个任务抢）。"""
    if _read_holder() == owner:
        _write_holder("", 0)
        logger.info("[gpu-lock] %s 释放锁（空闲 %dMB）",
                     owner, _free_vram_mb())


def holder() -> str:
    return _read_holder()


def status() -> dict:
    return {
        "holder": _read_holder(),
        "free_mb": _free_vram_mb(),
    }


__all__ = ["acquire", "release", "holder", "status"]
