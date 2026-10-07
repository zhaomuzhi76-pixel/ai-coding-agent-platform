"""PaddleOCR 并发引擎。职责：多页图并发识别 → 多个 OcrResult。
不依赖 PaddleOCR 原生批量接口（2.7.x 有 det=false 限制），
改用 ThreadPoolExecutor 并发单页推理（Paddle C++ 层释放 GIL）。"""
from __future__ import annotations
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, List, Optional

from backend.rag.ingest.ocr.contracts import OcrResult
from backend.rag.ingest.ocr.paddle_engine import (
    _parse_item, _SUPPORTED_LANG)

DEFAULT_WORKERS = 1


class BatchPaddleEngine:
    """并发 OCR 引擎：一次送 N 张路径，线程池并发返回 N 个结果。"""
    def __init__(self, *, lang: str = "ch", use_gpu: bool = False,
                 use_angle_cls: bool = True,
                 workers: int = DEFAULT_WORKERS) -> None:
        if lang not in _SUPPORTED_LANG:
            raise ValueError(f"lang must be in {_SUPPORTED_LANG}")
        if workers < 1:
            workers = 1
        self._lang = lang
        self._use_gpu = use_gpu
        self._use_angle_cls = use_angle_cls
        self._workers = workers
        self._ocr: Optional[Any] = None
        self._lock = threading.Lock()
        # [MEM_FIX] 定期重置引擎
        self._pages_since_reset = 0
        self._reset_every = int(os.environ.get("RAG_OCR_RESET_EVERY", "50"))

    def ready(self) -> bool:
        return self._ocr is not None

    def _ensure_ocr(self) -> Any:
        if self._ocr is not None:
            return self._ocr
        with self._lock:
            if self._ocr is not None:
                return self._ocr
            from paddleocr import PaddleOCR
            # [3.x] 用 device 代替 use_gpu
            kwargs: dict = {
                "use_textline_orientation": self._use_angle_cls,
                "use_doc_unwarping": False,
                "use_doc_orientation_classify": False,
            }
            if self._use_gpu:
                kwargs["device"] = "gpu"
            # 模型名（与 paddle_engine 保持一致）
            mode = __import__("os").environ.get("RAG_OCR_MODEL", "mobile")
            if mode == "server":
                kwargs["text_detection_model_name"] = "PP-OCRv5_server_det"
                kwargs["text_recognition_model_name"] = "PP-OCRv5_server_rec"
            else:
                kwargs["text_detection_model_name"] = "PP-OCRv5_mobile_det"
                kwargs["text_recognition_model_name"] = "PP-OCRv5_mobile_rec"
            self._ocr = PaddleOCR(**kwargs)
            return self._ocr

    def recognize_batch(self, paths: List[str]) -> List[OcrResult]:
        """并发识别 N 张图。返回与输入同序的结果列表。"""
        if not paths:
            return []
        out: List[Optional[OcrResult]] = [None] * len(paths)
        valid = [(i, p) for i, p in enumerate(paths)
                 if p and os.path.isfile(p)]
        if not valid:
            return [self._err(p) for p in paths]

        # 关键：先初始化（避免并发首次加载模型）
        ocr = self._ensure_ocr()

        # 线程池并发单页推理
        workers = min(self._workers, len(valid))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            future_map = {
                ex.submit(self._single, ocr, p): (i, p)
                for i, p in valid
            }
            for fut in as_completed(future_map):
                idx, path = future_map[fut]
                try:
                    out[idx] = fut.result()
                except Exception as e:
                    out[idx] = self._err(
                        path, f"{type(e).__name__}: {e}")

        return [r if r is not None else self._err(paths[i])
                for i, r in enumerate(out)]

    def _single(self, ocr: Any, path: str) -> OcrResult:
        try:
            raw = ocr.ocr(path)
            return self._to_result(raw, path)
        except Exception as e:
            return self._err(path, f"{type(e).__name__}: {e}")

    def _to_result(self, raw: Any, path: str) -> OcrResult:
        """[3.x] 解析 PP-OCRv5 返回结构。"""
        lines = []
        items = raw if isinstance(raw, list) else [raw]
        for page in items:
            page_dict = None
            if hasattr(page, "json"):
                try: page_dict = page.json.get("res", {})
                except Exception: page_dict = None
            if page_dict is None and isinstance(page, dict):
                page_dict = page.get("res", page)
            if not isinstance(page_dict, dict):
                continue
            texts = page_dict.get("rec_texts") or []
            scores = page_dict.get("rec_scores") or []
            boxes = page_dict.get("dt_polys") or page_dict.get("rec_polys") or []
            for i, txt in enumerate(texts):
                txt = str(txt or "").strip()
                if not txt: continue
                from backend.rag.ingest.ocr.contracts import OcrLine
                conf = float(scores[i]) if i < len(scores) else 0.0
                box_raw = boxes[i] if i < len(boxes) else []
                box = tuple(
                    (float(p[0]), float(p[1]))
                    for p in box_raw
                    if isinstance(p, (list, tuple)) and len(p) >= 2)
                lines.append(OcrLine(
                    text=txt,
                    confidence=max(0.0, min(1.0, conf)),
                    box=box))
        return OcrResult(
            lines=tuple(lines),
            meta={"engine": "paddleocr-3x-concurrent",
                  "lang": self._lang,
                  "image": os.path.basename(path)})

    def _err(self, path: Optional[str], msg: str = "missing") -> OcrResult:
        return OcrResult(lines=(), meta={
            "engine": "paddleocr-concurrent", "error": msg,
            "image": os.path.basename(path or "")})


def make_batch_engine(*, lang: str = "ch",
                      use_gpu: bool = False) -> BatchPaddleEngine:
    import os as _os
    workers = int(_os.environ.get("RAG_OCR_WORKERS", DEFAULT_WORKERS))
    return BatchPaddleEngine(lang=lang, use_gpu=use_gpu, workers=workers)


__all__ = ["BatchPaddleEngine", "make_batch_engine", "DEFAULT_WORKERS"]
