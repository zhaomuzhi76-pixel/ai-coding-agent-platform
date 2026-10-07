"""[启动自愈] 清理僵尸 GPU 进程 + 显存 + Ollama 模型。"""
from __future__ import annotations
import logging
import os
import signal
import subprocess

logger = logging.getLogger(__name__)

_PROTECT = {"Xorg", "Xwayland", "gnome-shell", "kwin", "plasma"}




def _real_name(pid: int) -> str:
    """通过 /proc 获取真实进程名（解决 nvidia-smi 显示 [Not Found] 问题）。"""
    for path in [f"/proc/{pid}/comm", f"/proc/{pid}/cmdline"]:
        try:
            with open(path, "rb") as f:
                content = f.read().replace(b"\x00", b" ").decode(
                    "utf-8", errors="ignore").strip()
            if content:
                return content.split()[0] if "/" in content else content
        except Exception:
            continue
    return ""


def _list_gpu_pids() -> list:
    try:
        out = subprocess.check_output(
            ["nvidia-smi",
             "--query-compute-apps=pid,process_name",
             "--format=csv,noheader,nounits"],
            text=True, timeout=5).strip()
        out = out.replace("[Not Found]", "unknown")
        result = []
        for line in out.split("\n"):
            if not line.strip():
                continue
            parts = [x.strip() for x in line.split(",")]
            if len(parts) >= 2:
                try:
                    result.append((int(parts[0]), parts[1]))
                except ValueError:
                    continue
        return result
    except Exception:
        return []


def heal_on_startup() -> dict:
    result = {"scanned": 0, "killed": [], "skipped": [],
              "ollama_unloaded": []}
    pids = _list_gpu_pids()
    result["scanned"] = len(pids)
    my_pid = os.getpid()

    for pid, name in pids:
        if pid == my_pid:
            result["skipped"].append((pid, name, "self")); continue
        if any(p in name for p in _PROTECT):
            result["skipped"].append((pid, name, "protected")); continue
        # 用 /proc 拿真实进程名
        real = _real_name(pid) or name
        real_low = real.lower()
        is_ollama = "llama-server" in real_low or "ollama" in real_low
        is_paddle = ("python" in real_low or "paddle" in real_low
                     or "watchdog" in real_low)
        if not (is_ollama or is_paddle):
            result["skipped"].append((pid, name, "unknown")); continue
        try:
            os.kill(pid, signal.SIGKILL)
            result["killed"].append((pid, name))
            logger.info("[gpu-heal] 杀 PID=%d (%s)", pid, name)
        except Exception as e:
            logger.debug("kill %d: %r", pid, e)

    # Paddle/Torch 清缓存
    try:
        import paddle
        if paddle.is_compiled_with_cuda():
            paddle.device.cuda.empty_cache()
    except Exception:
        pass
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception:
        pass

    # Ollama 卸载所有模型
    try:
        import urllib.request, json
        out = subprocess.check_output(
            ["curl", "-s", "http://127.0.0.1:11434/api/ps"],
            text=True, timeout=3)
        data = json.loads(out)
        for m in data.get("models", []):
            body = json.dumps({"model": m["name"], "keep_alive": 0}).encode()
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate", data=body,
                headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5).read()
            result["ollama_unloaded"].append(m["name"])
    except Exception:
        pass

    return result


__all__ = ["heal_on_startup"]
