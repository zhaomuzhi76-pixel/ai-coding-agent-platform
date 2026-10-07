"""LLM 调用记录 —— JSONL 追加，线程安全"""
import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

STORE = Path(os.environ.get(
    "BIANCHENG_LLM_CALLS",
    str(Path.home() / ".biancheng" / "llm_calls.jsonl"),
))
_lock = threading.Lock()
MAX_LINES = 100_000  # 保留最近 10 万条


def _ensure() -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)


def record_call(
    provider: str,
    model: str,
    *,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    latency_ms: int = 0,
    success: bool = True,
    error: str = "",
    online: bool = True,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    _ensure()
    entry = {
        "id": uuid.uuid4().hex[:12],
        "ts": time.time(),
        "provider": provider,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "latency_ms": latency_ms,
        "success": success,
        "error": error[:200] if error else "",
        "online": online,
        "extra": extra or {},
    }
    with _lock:
        with STORE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        _maybe_rotate()
    return entry


def _maybe_rotate() -> None:
    try:
        if STORE.stat().st_size < 20 * 1024 * 1024:  # 20MB 以内不处理
            return
        lines = STORE.read_text(encoding="utf-8").splitlines()
        if len(lines) > MAX_LINES:
            STORE.write_text("\n".join(lines[-MAX_LINES:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def list_calls(
    limit: int = 200,
    since: Optional[float] = None,
    provider: str = "",
    model: str = "",
) -> List[Dict[str, Any]]:
    if not STORE.exists():
        return []
    out: List[Dict[str, Any]] = []
    with STORE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if since and d.get("ts", 0) < since:
                continue
            if provider and d.get("provider") != provider:
                continue
            if model and d.get("model") != model:
                continue
            out.append(d)
    return out[-limit:]


def clear_calls() -> int:
    if not STORE.exists():
        return 0
    n = sum(1 for _ in STORE.open("r", encoding="utf-8"))
    STORE.write_text("", encoding="utf-8")
    return n
