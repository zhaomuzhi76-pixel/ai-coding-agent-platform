"""PaddleOCR 3.x 引擎封装。职责：图片路径 → OcrResult。
兼容 PP-OCRv5 server 模型，支持繁简/古籍/竖排/手写。
环境变量：
  RAG_OCR_ENGINE=3x    强制使用 3.x 引擎（默认自动检测）
  RAG_OCR_MODEL=v5     server 模型（默认）
  RAG_OCR_USE_GPU=0    是否 GPU
"""
from __future__ import annotations
import os
import threading
from typing import Any, Optional

from backend.rag.ingest.ocr.contracts import OcrLine, OcrResult

DEFAULT_LANG = "ch"
# [COMPAT] 3.x PP-OCRv5 单模型，lang 只作提示，不再切换模型
_SUPPORTED_LANG = ("ch", "en", "japan", "korean", "chinese_cht")


class PaddleOcrEngine:
    """PaddleOCR 3.x 引擎（懒加载单例）。"""

    def __init__(self, *, lang: str = DEFAULT_LANG,
                 use_gpu: bool = False,
                 use_angle_cls: bool = True) -> None:
        self._lang = lang
        self._use_gpu = use_gpu
        self._use_angle_cls = use_angle_cls
        self._ocr: Optional[Any] = None
        self._lock = threading.Lock()
        # [MEM_FIX] PaddleOCR 3.x 有内存泄漏，每 N 页重置引擎
        self._pages_since_reset = 0
        self._reset_every = int(os.environ.get("RAG_OCR_RESET_EVERY", "50"))

    @property
    def lang(self) -> str:
        return self._lang

    def ready(self) -> bool:
        return self._ocr is not None

    def _ensure_ocr(self) -> Any:
        if self._ocr is not None:
            return self._ocr
        with self._lock:
            if self._ocr is not None:
                return self._ocr
            from paddleocr import PaddleOCR
            # [3.x] 实例化参数：使用 PP-OCRv5 server 模型
            kwargs: dict = {
                "use_textline_orientation": self._use_angle_cls,
                # [OPT] 关闭最贵的 UVDoc（文档矫正，扫描件用不上）
                "use_doc_unwarping": False,
                # [OPT] 关闭文档方向分类（首尾页已知）
                "use_doc_orientation_classify": False,
            }
            if self._use_gpu:
                kwargs["device"] = "gpu"
            # PP-OCRv5 server 模型（检测+识别均用 server 版）
            # [TUNE] 环境变量可选 server / mobile
            mode = os.environ.get("RAG_OCR_MODEL", "mobile")
            if mode == "server":
                kwargs["text_detection_model_name"] = "PP-OCRv5_server_det"
                kwargs["text_recognition_model_name"] = "PP-OCRv5_server_rec"
            else:
                kwargs["text_detection_model_name"] = "PP-OCRv5_mobile_det"
                kwargs["text_recognition_model_name"] = "PP-OCRv5_mobile_rec"
            self._ocr = PaddleOCR(**kwargs)
            return self._ocr

    def recognize(self, image_path: str) -> OcrResult:
        if not image_path or not os.path.isfile(image_path):
            raise FileNotFoundError(image_path)
        ocr = self._ensure_ocr()
        try:
            # [3.x] ocr.ocr() 返回 list[Result] 或 dict-like
            raw = ocr.ocr(image_path)
        except Exception as e:
            raise RuntimeError(
                f"PaddleOCR 识别失败: {type(e).__name__}: {e}") from e
        lines = self._parse_3x(raw)
        # [MEM_FIX] 定期释放引擎（防泄漏）
        self._pages_since_reset += 1
        if self._reset_every > 0 and self._pages_since_reset >= self._reset_every:
            self._release_engine()

        return OcrResult(
            lines=tuple(lines),
            meta={"engine": "paddleocr-3x-v5server",
                  "lang": self._lang,
                  "image": os.path.basename(image_path)})

    def _release_engine(self) -> None:
        """[真正的释放] 销毁 PaddleOCR 对象 + 清 CUDA + GC。
        注意：只 empty_cache 不销毁对象，模型仍占显存！
        """
        import gc
        with self._lock:
            ocr = self._ocr
            self._ocr = None   # 关键：切断引用
        # 显式销毁
        try:
            del ocr
        except Exception:
            pass
        # Paddle 清缓存
        try:
            import paddle
            if paddle.is_compiled_with_cuda():
                paddle.device.cuda.empty_cache()
                # 清理 CUDA 内存池
                try:
                    paddle.device.cuda.synchronize()
                except Exception:
                    pass
        except Exception:
            pass
        # PyTorch 清缓存
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
        except Exception:
            pass
        gc.collect()
        self._pages_since_reset = 0


    @staticmethod
    def _parse_3x(raw: Any) -> list:
        """3.x 返回结构：list[Result]，Result 含 rec_texts/rec_scores/dt_polys。"""
        out: list = []
        if not raw:
            return out
        # 3.x 可能返回 list[Result] 或 list[dict]
        items = raw if isinstance(raw, list) else [raw]
        for page in items:
            # Result 对象转 dict
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
                if not txt:
                    continue
                conf = float(scores[i]) if i < len(scores) else 0.0
                box_raw = boxes[i] if i < len(boxes) else []
                box = tuple(
                    (float(p[0]), float(p[1]))
                    for p in box_raw
                    if isinstance(p, (list, tuple)) and len(p) >= 2)
                out.append(OcrLine(
                    text=txt,
                    confidence=max(0.0, min(1.0, conf)),
                    box=box))
        return out


def make_paddle_engine(*, lang: str = DEFAULT_LANG,
                       use_gpu: bool = False) -> PaddleOcrEngine:
    return PaddleOcrEngine(lang=lang, use_gpu=use_gpu)



def _parse_item(item):
    """[COMPAT] 兼容 2.x 单条解析，供旧代码调用。3.x 不会用到。"""
    if not isinstance(item, (list, tuple)) or len(item) < 2:
        return None
    box_raw, payload = item[0], item[1]
    text = ""
    conf = 0.0
    if isinstance(payload, (list, tuple)) and len(payload) >= 2:
        text = str(payload[0] or "")
        try: conf = float(payload[1])
        except (TypeError, ValueError): conf = 0.0
    elif isinstance(payload, str):
        text = payload
    if not text.strip():
        return None
    return OcrLine(
        text=text.strip(),
        confidence=max(0.0, min(1.0, conf)),
        box=())

__all__ = ["PaddleOcrEngine", "make_paddle_engine",
           "DEFAULT_LANG", "_SUPPORTED_LANG", "_parse_item"]
