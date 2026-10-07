"""PDF OCR 批处理常量 + 内存守卫。独立文件，主类保持 < 230 行。
不做解析（parsers 管）、不做 OCR（ocr 管）。
"""
from __future__ import annotations
from typing import Any, List

# OCR 批处理常量
BLANK_RANGE = 12
DEFAULT_BATCH = 8
RSS_WARN_MB = 2000
RSS_DANGER_MB = 3000


def read_rss_mb() -> float:
    """当前进程 RSS（MB）。异常返回 0。"""
    try:
        with open("/proc/self/statm", "r") as f:
            return int(f.read().split()[1]) * 4096 / 1024 / 1024
    except Exception:
        return 0.0


def release_imgs(imgs: List[Any]) -> None:
    """释放图像批次 + GC。"""
    for img in imgs:
        try: img.close()
        except Exception: pass
    imgs.clear()
    try:
        import gc
        gc.collect()
    except Exception: pass


__all__ = ["BLANK_RANGE", "DEFAULT_BATCH", "RSS_WARN_MB", "RSS_DANGER_MB",
           "read_rss_mb", "release_imgs"]
