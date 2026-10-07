#!/usr/bin/env python3
"""[L3 看门狗] 独立进程，监控 GPU + job 超时：
  1. 后端不存活 且 显存 > 1GB → 清理 GPU
  2. 日志 30 分钟无变化 → 清理
  3. 显存 > 6GB 且 util=0% 持续 5 分钟 → 清理
  4. job 超时 → 清理
关键：所有 GPU 清理都在【子进程】里做，避免看门狗自己占 GPU。
"""
import logging
import os
import signal
import subprocess
import time

BASE_DIR = "/home/computer01/xiangmu02/biancheng_aiagentpro"
LOG_FILE = f"{BASE_DIR}/logs/backend.log"
WATCH_LOG = "/tmp/gpu_watchdog.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [watchdog] %(levelname)s %(message)s",
    handlers=[logging.FileHandler(WATCH_LOG), logging.StreamHandler()])

HIGH_VRAM_MB = 1024
CRIT_VRAM_MB = 6000
IDLE_STRIKES = 10
CHECK_INTERVAL = 30
LOG_STALE_SEC = 1800
ZOMBIE_CLEAN_INTERVAL = 3600

_last_log_size = 0
_last_log_change = time.time()
_idle_count = 0
_stuck_strikes = {}
_last_zombie_clean = 0


def _run_subprocess(args, timeout=30):
    """子进程执行，避免当前进程 import paddle/torch 占 GPU。"""
    try:
        r = subprocess.run(args, capture_output=True, text=True,
                           timeout=timeout, cwd=BASE_DIR)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, "", repr(e)


def gpu_status():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,utilization.gpu",
             "--format=csv,noheader,nounits"],
            text=True, timeout=5).strip().split("\n")[0]
        p = [x.strip() for x in out.split(",")]
        return int(p[0]), int(p[1])
    except Exception:
        return -1, -1


def list_gpu_pids():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-compute-apps=pid,process_name",
             "--format=csv,noheader,nounits"],
            text=True, timeout=5).strip()
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


def backend_alive():
    try:
        out = subprocess.check_output(
            ["pgrep", "-f", "python -m backend"], text=True)
        return bool(out.strip())
    except Exception:
        return False


def check_log_progress():
    global _last_log_size, _last_log_change
    try:
        sz = os.path.getsize(LOG_FILE)
    except Exception:
        return True
    if sz != _last_log_size:
        _last_log_size = sz
        _last_log_change = time.time()
        return True
    return not (time.time() - _last_log_change > LOG_STALE_SEC)


def check_job_timeouts():
    try:
        cmd = (
            "import sys; "
            f"sys.path.insert(0, {BASE_DIR!r}); "
            "from backend.rag.ingest.jobs.job_watchdog import get_tracker; "
            "import json; "
            "print(json.dumps(get_tracker().list_stuck()))"
        )
        rc, out, err = _run_subprocess(["python3", "-c", cmd], timeout=10)
        if rc == 0 and out:
            import json
            return json.loads(out)
    except Exception:
        pass
    return {}


def maybe_clean_zombies():
    global _last_zombie_clean
    if time.time() - _last_zombie_clean < ZOMBIE_CLEAN_INTERVAL:
        return
    _last_zombie_clean = time.time()
    cmd = (
        "import sys, json; "
        f"sys.path.insert(0, {BASE_DIR!r}); "
        "from backend.rag.ingest.jobs.zombie_cleaner import full_scan; "
        "r = full_scan(dry_run=False); "
        "print(json.dumps({k: v.get('killed', v.get('marked', v.get('deleted', 0))) "
        "for k, v in r.items() if isinstance(v, dict)}))"
    )
    rc, out, err = _run_subprocess(["python3", "-c", cmd], timeout=60)
    if rc == 0:
        logging.info("[zombie-clean] %s", out)
    else:
        logging.debug("[zombie-clean] 失败: %s", err[:200])


def kill_gpu_zombies(reason: str):
    """杀 GPU 进程（子进程执行）。"""
    killed = []
    for pid, name in list_gpu_pids():
        if any(p in name for p in ("Xorg", "Xwayland", "gnome", "kwin")):
            continue
        try:
            os.kill(pid, signal.SIGKILL)
            killed.append((pid, name))
            logging.warning("[%s] 杀 GPU PID=%d (%s)", reason, pid, name)
        except Exception as e:
            logging.debug("kill %d: %r", pid, e)
    # 子进程清 CUDA 缓存
    clean_cmd = (
        "import sys; "
        f"sys.path.insert(0, {BASE_DIR!r}); "
        "try:\n"
        "    from backend.rag.ingest.ocr.gpu_self_heal import heal_on_startup\n"
        "    heal_on_startup()\n"
        "except Exception: pass\n"
    )
    _run_subprocess(["python3", "-c", clean_cmd], timeout=30)
    return killed


def main():
    global _idle_count, _stuck_strikes
    logging.info("GPU 看门狗启动，每 %ds 检查", CHECK_INTERVAL)

    # [BOOT_CLEAN] 启动时立即清僵尸（子进程）
    maybe_clean_zombies()
    _last_zombie_clean = 0  # 强制启动时执行一次
    maybe_clean_zombies()

    # [BOOT_GPU] 启动时清僵尸 GPU（子进程）
    kill_gpu_zombies("boot")

    while True:
        try:
            vram, util = gpu_status()
            alive = backend_alive()
            log_ok = check_log_progress()
            stuck_jobs = check_job_timeouts()

            # 场景 4：job 超时
            for jid, reason in stuck_jobs.items():
                _stuck_strikes[jid] = _stuck_strikes.get(jid, 0) + 1
                if _stuck_strikes[jid] >= 2:
                    logging.warning("[job-timeout] %s: %s", jid, reason)
                    kill_gpu_zombies(f"job-timeout:{jid}")
                    cmd = (
                        "import sys; "
                        f"sys.path.insert(0, {BASE_DIR!r}); "
                        "from backend.rag.ingest.jobs.job_watchdog import get_tracker; "
                        f"get_tracker().cleanup({jid!r})"
                    )
                    _run_subprocess(["python3", "-c", cmd], timeout=10)
                    _stuck_strikes.pop(jid, None)
            for jid in list(_stuck_strikes.keys()):
                if jid not in stuck_jobs:
                    _stuck_strikes.pop(jid, None)

            # 场景 1：后端死但显存占
            if not alive and vram > HIGH_VRAM_MB:
                logging.warning("后端已死但显存=%dMB，清理", vram)
                kill_gpu_zombies("backend-dead")
                _idle_count = 0
                time.sleep(CHECK_INTERVAL)
                continue

            # 场景 2：日志 30min 无变化
            if alive and not log_ok and vram > HIGH_VRAM_MB:
                logging.warning("日志 30min 无变化但显存=%dMB", vram)
                kill_gpu_zombies("backend-stuck")
                _idle_count = 0
                time.sleep(CHECK_INTERVAL)
                continue

            # 场景 3：显存 > 6GB 且 util=0% 连续
            if vram > CRIT_VRAM_MB and util == 0 and alive:
                _idle_count += 1
                logging.info("显存=%dMB util=0%% (%d/%d)",
                             vram, _idle_count, IDLE_STRIKES)
                if _idle_count >= IDLE_STRIKES:
                    logging.warning("5min util=0%%，清理")
                    kill_gpu_zombies("idle-gpu")
                    _idle_count = 0
            else:
                _idle_count = 0

            # 定时清僵尸
            maybe_clean_zombies()

        except Exception as e:
            logging.exception("循环异常: %r", e)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
