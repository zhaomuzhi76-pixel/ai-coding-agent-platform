"""OCR 断点续传（按 PDF 内容哈希，跨 job 复用）。
存储：~/.cache/agent_knowledge/ocr_checkpoints/<pdf_hash>.json
环境变量：
  RAG_OCR_NO_RESUME=1  禁用（强制从头）
  RAG_OCR_CKPT_DIR=... 自定义目录
"""
from __future__ import annotations
import threading
import hashlib, json, os, tempfile, time
from pathlib import Path
from typing import Any, Dict, Optional


def _dir() -> Path:
    base = os.environ.get(
        "RAG_OCR_CKPT_DIR",
        os.path.expanduser("~/.cache/agent_knowledge/ocr_checkpoints"))
    p = Path(base); p.mkdir(parents=True, exist_ok=True); return p


def _path(h: str) -> Path: return _dir() / f"{h}.json"


def file_sha256(path: str, block: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(block)
            if not b: break
            h.update(b)
    return h.hexdigest()


def is_disabled() -> bool:
    return os.environ.get("RAG_OCR_NO_RESUME", "0") == "1"


def load(h: str) -> Optional[Dict[str, Any]]:
    p = _path(h)
    if not p.is_file(): return None
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return None


def save(h: str, **fields: Any) -> None:
    """原子写：tmp + replace，防 kill 写坏。"""
    p = _path(h)
    data = load(h) or {}
    data.update(fields); data["updated_at"] = time.time()
    fd, tmp = tempfile.mkstemp(prefix=".ck_", dir=str(p.parent))
    os.close(fd)
    try:
        Path(tmp).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, p)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass


def get_last_page(pdf_path: str) -> int:
    """返回此 PDF 已处理到第几页（1-based）。0=从头。"""
    if is_disabled(): return 0
    try:
        h = file_sha256(pdf_path)
        ck = load(h)
        return int(ck.get("last_page", 0)) if ck else 0
    except Exception:
        return 0


def advance(pdf_path: str, page: int, total: int = 0) -> None:
    if is_disabled(): return
    try:
        h = file_sha256(pdf_path)
        save(h, pdf_hash=h, last_page=int(page),
             total_pages=int(total or 0))
    except Exception:
        pass


def clear_for(pdf_path: str) -> None:
    try: _path(file_sha256(pdf_path)).unlink()
    except OSError: pass


def stats() -> Dict[str, Any]:
    d = _dir(); files = list(d.glob("*.json"))
    return {"dir": str(d), "count": len(files),
            "files": [f.name[:16] for f in files[:10]]}


__all__ = ["get_last_page", "advance", "clear_for",
           "file_sha256", "is_disabled", "stats"]

# ═══════════════════════════════════════════════════════════
# [OcrCheckpoint] 按 job_id 逐页存 OCR 文本（供 PdfSmartParserResume 用）
# 存储：<ckpt_dir>/<job_id>.pages.jsonl
# 每行：{"page_no": N, "text": "..."}
# 与函数式接口（get_last_page 等）共存，后缀 .pages.jsonl 区分
# ═══════════════════════════════════════════════════════════
class OcrCheckpoint:
    """逐页 OCR 断点存储。线程安全，append 后立即 fsync。"""

    def __init__(self, job_id: str) -> None:
        if not job_id:
            raise ValueError("job_id required")
        self._job_id = str(job_id)
        self._lock = threading.Lock()
        self._closed = False
        self._disabled = is_disabled()
        base = os.environ.get(
            "RAG_OCR_CKPT_DIR",
            os.path.expanduser("~/.cache/agent_knowledge/ocr_checkpoints"))
        p = Path(base)
        if not self._disabled:
            try: p.mkdir(parents=True, exist_ok=True)
            except Exception: pass
        self._path = p / f"{self._job_id}.pages.jsonl"

    def read_all(self) -> list:
        if self._disabled or not self._path.is_file():
            return []
        out = []
        try:
            with self._path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            pass
        return out

    def append_page(self, page_no: int, text: str) -> None:
        if self._disabled or self._closed:
            return
        rec = {"page_no": int(page_no), "text": str(text or "")}
        with self._lock:
            try:
                with self._path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False))
                    f.write("\n")
                    f.flush()
                    try: os.fsync(f.fileno())
                    except Exception: pass
            except Exception:
                pass

    def close(self) -> None:
        self._closed = True


__all__.append("OcrCheckpoint")
