"""系统资源监控端点。返回 CPU/内存/GPU 实时状态。
独立插件，不修改任何现有路由。GPU 用 nvidia-smi（不装 pynvml）。
"""
from __future__ import annotations
import subprocess
from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter(prefix="/api/system", tags=["system-monitor"])


def _cpu_mem() -> Dict[str, Any]:
    try:
        import psutil
        vm = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=0.1)
        load = list(psutil.getloadavg())
        return {
            "cpu": {
                "percent": round(cpu_pct, 1),
                "cores": psutil.cpu_count(logical=True),
                "load": [round(x, 2) for x in load],
            },
            "memory": {
                "total_gb": round(vm.total / 1024 ** 3, 1),
                "used_gb": round(vm.used / 1024 ** 3, 1),
                "available_gb": round(vm.available / 1024 ** 3, 1),
                "percent": round(vm.percent, 1),
            },
        }
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def _gpu() -> Dict[str, Any]:
    """nvidia-smi 查询，不依赖 pynvml。"""
    try:
        out = subprocess.check_output(
            ["nvidia-smi",
             "--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            text=True, timeout=3).strip()
        parts = [p.strip() for p in out.split(",")]
        if len(parts) >= 5:
            return {
                "ok": True,
                "name": parts[0],
                "vram_used_mb": int(float(parts[1])),
                "vram_total_mb": int(float(parts[2])),
                "util": int(float(parts[3])),
                "temp_c": int(float(parts[4])),
                "vram_percent": round(int(float(parts[1])) * 100 / max(1, int(float(parts[2]))), 1),
            }
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}"}
    return {"ok": False, "error": "no data"}


def _procs() -> List[Dict[str, Any]]:
    """关键进程占用（backend / ollama / reranker）。"""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(["pid", "name", "cmdline", "cpu_percent", "memory_info"]):
            try:
                cmd = " ".join(p.info.get("cmdline") or [])
                if any(k in cmd for k in ("python -m backend", "ollama serve",
                                           "reranker_server", "paddle")):
                    procs.append({
                        "pid": p.info["pid"],
                        "cmd": cmd[:80],
                        "cpu": round(p.info.get("cpu_percent") or 0, 1),
                        "rss_mb": round((p.info.get("memory_info").rss if p.info.get("memory_info") else 0) / 1024 / 1024, 1),
                    })
            except Exception:
                continue
        return procs[:8]
    except Exception:
        return []


@router.get("/health")
def system_health() -> Dict[str, Any]:
    base = _cpu_mem()
    base["gpu"] = _gpu()
    base["processes"] = _procs()
    return {"ok": True, "data": base}

def _gpu_processes() -> List[Dict[str, Any]]:
    """列出占用 GPU 的所有进程。
    [FALLBACK_NAME_V2] 关键修复：
      1. used_memory 可能返回 "N/A" → 不跳过，当作未知
      2. process_name 可能返回 "[Not Found]" → 用 /proc 反查
      3. vram_mb 拿不到时，从总显存减其他进程推算（可选）
    """
    out: List[Dict[str, Any]] = []
    try:
        raw = subprocess.check_output(
            ["nvidia-smi",
             "--query-compute-apps=pid,process_name,used_memory",
             "--format=csv,noheader"],
            text=True, timeout=5).strip()
        for line in raw.split("\n"):
            if not line.strip():
                continue
            parts = [x.strip() for x in line.split(",")]
            if len(parts) < 3:
                continue
            # ── pid（必须能解析）
            try:
                pid = int(parts[0])
            except (ValueError, TypeError):
                continue
            # ── used_memory（可能是 "N/A"）
            used_mb = 0
            try:
                used_mb = int(parts[2])
            except (ValueError, TypeError):
                used_mb = 0   # [V2] 关键：不跳过
            # ── process_name（可能是 "[Not Found]"）
            name = parts[1]
            if ("[Not Found]" in name or "[N/A]" in name
                    or not name.strip() or name.startswith("[")):
                name = ""
                for _fp in (f"/proc/{pid}/comm", f"/proc/{pid}/cmdline"):
                    try:
                        with open(_fp, "rb") as _f:
                            _c = _f.read().replace(b"\x00", b" ").decode(
                                "utf-8", errors="ignore").strip()
                        if _c:
                            name = _c.split()[0]
                            break
                    except Exception:
                        pass
                if not name:
                    name = f"pid-{pid}"
            # ── 进程详情
            info: Dict[str, Any] = {
                "pid": pid, "name": name, "vram_mb": used_mb,
            }
            try:
                import psutil
                proc = psutil.Process(pid)
                info["cmd"] = " ".join(proc.cmdline())[:200]
                info["user"] = proc.username()
                info["rss_mb"] = round(
                    proc.memory_info().rss / 1024 / 1024, 1)
                info["cpu_percent"] = proc.cpu_percent(interval=0.05)
                info["create_time"] = proc.create_time()
                info["status"] = proc.status()
            except Exception:
                info["cmd"] = ""
                info["user"] = ""
                info["rss_mb"] = 0
            out.append(info)
    except Exception as e:
        import logging as _lg
        _lg.getLogger(__name__).warning("[gpu-procs] 查询失败: %r", e)
    return out

@router.get("/gpu-detail")
def gpu_detail() -> Dict[str, Any]:
    """GPU 详细面板：每进程占显存 + 总量 + 利用率。"""
    base = _gpu()
    base["processes"] = _gpu_processes()
    # 汇总
    total_vram = base.get("vram_total_mb", 0)
    used_vram = base.get("vram_used_mb", 0)
    proc_vram = sum(p.get("vram_mb", 0) for p in base["processes"])
    # [VRAM_ATTRIBUTE] WSL 下 nvidia-smi 不返回每进程显存
    # → 唯一进程时全归属；多进程时按 RSS 比例分摊
    proc_vram = sum(p.get("vram_mb", 0) for p in base.get("processes", []))
    unattributed = max(0, used_vram - proc_vram)
    if unattributed > 0 and base.get("processes"):
        if len(base["processes"]) == 1:
            # 唯一进程 → 全归属
            base["processes"][0]["vram_mb"] = unattributed
            base["processes"][0]["vram_attributed"] = True
            proc_vram = unattributed
            unattributed = 0
        else:
            # 多进程 → 按 RSS 比例分摊
            total_rss = sum(p.get("rss_mb", 0)
                            for p in base["processes"]) or 1
            for p in base["processes"]:
                share = int(unattributed
                            * p.get("rss_mb", 0) / total_rss)
                p["vram_mb"] = p.get("vram_mb", 0) + share
                p["vram_attributed"] = True
            proc_vram = sum(p.get("vram_mb", 0)
                            for p in base["processes"])
            unattributed = max(0, used_vram - proc_vram)

    base["summary"] = {
        "vram_total_mb": total_vram,
        "vram_used_mb": used_vram,
        "vram_percent": base.get("vram_percent", 0),
        "process_count": len(base["processes"]),
        "process_vram_mb": proc_vram,
        "other_vram_mb": unattributed,
    }
    return {"ok": True, "data": base}

def _all_processes(sort_by: str = "cpu", limit: int = 30) -> List[Dict[str, Any]]:
    """列出进程，按 cpu 或 memory 排序，返回 top N。
    sort_by: "cpu" | "memory"
    """
    try:
        import psutil
    except ImportError:
        return []
    try:
        items: List[Dict[str, Any]] = []
        # 先预热 cpu_percent（第一次调用总是 0）
        procs = list(psutil.process_iter(
            ["pid", "name", "cmdline", "username",
             "cpu_percent", "memory_info", "create_time", "status"]))
        for p in procs:
            try:
                p.cpu_percent(interval=None)
            except Exception:
                pass
        # [FIX] 采样窗口 0.8s（之前 0.15s 太短，空闲系统读数全 0）
        import time as _t
        _t.sleep(0.8)
        for p in procs:
            try:
                info = p.info
                mi = info.get("memory_info")
                items.append({
                    "pid": info.get("pid"),
                    "name": info.get("name") or "?",
                    "cmd": " ".join(info.get("cmdline") or [])[:200],
                    "user": info.get("username") or "",
                    "cpu_percent": round(p.cpu_percent(interval=None) or 0, 1),
                    "rss_mb": round((mi.rss if mi else 0) / 1024 / 1024, 1),
                    "create_time": info.get("create_time") or 0,
                    "status": info.get("status") or "?",
                })
            except Exception:
                continue
        # 排序
        if sort_by == "memory":
            items.sort(key=lambda x: x["rss_mb"], reverse=True)
        else:
            items.sort(key=lambda x: x["cpu_percent"], reverse=True)
        return items[:limit]
    except Exception:
        return []


@router.get("/processes")
def list_processes(sort: str = "cpu", limit: int = 30) -> Dict[str, Any]:
    """进程排行：sort=cpu|memory，limit 默认 30。"""
    sort = (sort or "cpu").lower()
    if sort not in ("cpu", "memory"):
        sort = "cpu"
    if limit <= 0 or limit > 200:
        limit = 30
    procs = _all_processes(sort_by=sort, limit=limit)
    return {"ok": True, "data": {
        "sort": sort, "limit": limit,
        "count": len(procs), "processes": procs,
    }}

@router.post("/release-gpu")
def release_gpu() -> Dict[str, Any]:
    """[GPU_RELEASE] 手动释放 Paddle/CUDA 显存。"""
    freed = []
    try:
        import paddle
        if paddle.is_compiled_with_cuda():
            paddle.device.cuda.empty_cache()
            freed.append("paddle")
    except Exception:
        pass
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            freed.append("torch")
    except Exception:
        pass
    try:
        import gc
        gc.collect()
        freed.append("gc")
    except Exception:
        pass
    # 返回当前显存
    used = 0
    try:
        import subprocess
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used",
             "--format=csv,noheader,nounits"], text=True, timeout=3)
        used = int(out.strip().split("\n")[0])
    except Exception:
        pass
    return {"ok": True, "data": {
        "freed": freed, "vram_used_mb": used,
        "note": "如需彻底释放，可重启后端进程",
    }}

@router.post("/cleanup-zombies")
def cleanup_zombies(dry_run: bool = False) -> Dict[str, Any]:
    """[L5] 僵尸清理：进程 + job + draft + checkpoint + tombstone + 向量。
    默认 dry_run=False（真清），传 ?dry_run=true 只看不动。
    """
    try:
        from backend.rag.ingest.jobs.zombie_cleaner import full_scan
        return {"ok": True, "data": full_scan(dry_run=dry_run)}
    except Exception as e:
        import traceback; traceback.print_exc()
        return {"ok": False, "error": str(e)}

