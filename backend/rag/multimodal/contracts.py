"""RAG 图文混合契约。职责：只定义数据类与序列化。
不切片、不向量化、不检索、不碰 Chroma。与现有 rag/spec.py 职责互斥：
spec.py 管纯文本 RagChunk/RagHit；本文件管其"带图片"变体，独立不继承。"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

IMAGES_META_KEY = "__images_json__"

def _freeze(m: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(m))

@dataclass(frozen=True)
class ImageRef:
    """单张图片引用。url 与 b64 二选一；两者皆空 → 无效。"""
    id: str
    mime: str
    source: str = "indexed"
    url: Optional[str] = None
    b64: Optional[str] = None
    alt_text: str = ""

    def __post_init__(self) -> None:
        if not self.id: raise ValueError("ImageRef.id must not be empty")
        if not self.mime or not self.mime.startswith("image/"):
            raise ValueError(f"ImageRef.mime must be image/*, got {self.mime!r}")
        if self.url and self.b64:
            raise ValueError("ImageRef: url and b64 are mutually exclusive")
        if not self.url and not self.b64:
            raise ValueError("ImageRef: either url or b64 required")

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"id": self.id, "mime": self.mime,
                             "source": self.source, "alt_text": self.alt_text}
        if self.url: d["url"] = self.url
        if self.b64: d["b64"] = self.b64
        return d

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ImageRef":
        return cls(id=str(raw["id"]), mime=str(raw["mime"]),
                   source=str(raw.get("source", "indexed")),
                   url=raw.get("url") or None, b64=raw.get("b64") or None,
                   alt_text=str(raw.get("alt_text", "")))

def _encode_images(images: Tuple[ImageRef, ...]) -> str:
    return json.dumps([i.to_dict() for i in images], ensure_ascii=False)

def _decode_images(s: str) -> Tuple[ImageRef, ...]:
    if not s: return ()
    try:
        raw = json.loads(s)
    except json.JSONDecodeError:
        return ()
    if not isinstance(raw, list):
        return ()
    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            out.append(ImageRef.from_dict(item))
        except (KeyError, ValueError):
            continue
    return tuple(out)

@dataclass(frozen=True)
class MultimodalChunk:
    """图文混合索引单元。text 是索引向量源；images 挂 metadata。"""
    chunk_id: str
    text: str
    images: Tuple[ImageRef, ...] = ()
    source: str = ""
    source_path: str = ""
    line_no: int = 0
    role: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze(self.metadata))
        if not self.chunk_id: raise ValueError("MultimodalChunk.chunk_id must not be empty")
        if not self.text: raise ValueError("MultimodalChunk.text must not be empty")
        if not isinstance(self.images, tuple):
            raise TypeError("images must be tuple, not list")

    def to_metadata(self) -> dict[str, Any]:
        """转 Chroma 可存 metadata（标量 + JSON 字符串）。"""
        base = {
            "source": self.source, "source_path": self.source_path,
            "line_no": int(self.line_no), "role": self.role,
            "text_len": len(self.text), "image_count": len(self.images),
        }
        if self.images:
            base[IMAGES_META_KEY] = _encode_images(self.images)
        base.update({k: v for k, v in self.metadata.items()
                     if isinstance(v, (str, int, float, bool))})
        return base

    @classmethod
    def from_metadata(cls, chunk_id: str, text: str,
                      metadata: Mapping[str, Any]) -> "MultimodalChunk":
        m = dict(metadata)
        images = _decode_images(str(m.pop(IMAGES_META_KEY, "")))
        source = str(m.pop("source", ""))
        sp = str(m.pop("source_path", ""))
        ln = int(m.pop("line_no", 0))
        role = str(m.pop("role", ""))
        m.pop("text_len", None); m.pop("image_count", None)
        return cls(chunk_id=chunk_id, text=text, images=images,
                   source=source, source_path=sp, line_no=ln,
                   role=role, metadata=m)

@dataclass(frozen=True)
class MultimodalHit:
    """检索命中。text + images 一起返回。"""
    chunk_id: str
    text: str
    score: float
    images: Tuple[ImageRef, ...] = ()
    source: str = ""
    source_path: str = ""
    line_no: int = 0
    role: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze(self.metadata))
        if not isinstance(self.images, tuple):
            raise TypeError("images must be tuple")

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id, "text": self.text,
            "score": round(self.score, 4),
            "images": [i.to_dict() for i in self.images],
            "source": self.source, "source_path": self.source_path,
            "line_no": self.line_no, "role": self.role,
            "metadata": dict(self.metadata),
        }

def make_multimodal_chunk_id(source: str, line_no: int, text: str,
                              images: Tuple[ImageRef, ...] = (),
                              offset: int = 0) -> str:
    """确定性 ID：同源+同行+同偏移+同文+同图 ids → 同 ID，幂等 upsert。
    offset 参与哈希：同一文档硬切出多段同内容时，各段 ID 不碰撞。"""
    h = hashlib.sha1()
    h.update(f"{source}|{line_no}|{int(offset)}|".encode("utf-8"))
    h.update(text.encode("utf-8"))
    for i in images:
        h.update(b"|"); h.update(i.id.encode("utf-8"))
    return "mm-" + h.hexdigest()[:16]

__all__ = ["IMAGES_META_KEY", "ImageRef", "MultimodalChunk",
           "MultimodalHit", "make_multimodal_chunk_id"]
