"""OCR 契约。职责：只描述 OCR 输出与引擎接口。
不做识别（paddle_engine 管）、不做 PDF 渲染（pdf_ocr_parser 管）。
与 parsers/contracts 边界：parsers 管"PDF→文本"；本层管"图片→文本"。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Protocol, Tuple

@dataclass(frozen=True)
class OcrLine:
    """OCR 识别出的单行。box 为四角坐标（可选）。"""
    text: str
    confidence: float = 0.0
    box: Tuple[Tuple[float, float], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("OcrLine.text must be str")
        if not isinstance(self.box, tuple):
            raise TypeError("OcrLine.box must be tuple")
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError(
                f"OcrLine.confidence must be 0..1, got {self.confidence}")

@dataclass(frozen=True)
class OcrResult:
    """单张图片的 OCR 结果。"""
    lines: Tuple[OcrLine, ...] = ()
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))
        if not isinstance(self.lines, tuple):
            raise TypeError("lines must be tuple")

    @property
    def text(self) -> str:
        return "\n".join(l.text for l in self.lines if l.text)

    @property
    def avg_confidence(self) -> float:
        vals = [l.confidence for l in self.lines if l.confidence > 0]
        return sum(vals) / len(vals) if vals else 0.0

    def to_dict(self) -> dict:
        return {
            "line_count": len(self.lines),
            "avg_confidence": round(self.avg_confidence, 4),
            "text": self.text,
            "meta": dict(self.meta),
        }

class OcrEngineProtocol(Protocol):
    """OCR 引擎接口。实现类需提供 recognize()。"""
    def recognize(self, image_path: str) -> OcrResult: ...

__all__ = ["OcrLine", "OcrResult", "OcrEngineProtocol"]
