"""RAG 数据模型（L0 · 纯数据）。

职责：
    - RagChunk：索引单元（文本 + 元数据）
    - RagHit：检索命中（score + chunk）
    - 序列化

不负责：
    - 切片算法（chunker 管）
    - 向量化（EmbeddingService 管）
    - 存储（VectorStore 管）
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class RagChunk:
    chunk_id: str
    text: str
    source: str = ""             # 数据集 ID 或文件名
    source_path: str = ""        # 原始 JSONL 路径
    line_no: int = 0             # 原行号
    role: str = ""               # user / assistant
    metadata: dict = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        """转成 chroma 可存的 metadata（值必须 str/int/float/bool）。"""
        return {
            "source": self.source,
            "source_path": self.source_path,
            "line_no": int(self.line_no),
            "role": self.role,
            "text_len": len(self.text),
            **{k: v for k, v in self.metadata.items()
               if isinstance(v, (str, int, float, bool))},
        }


@dataclass(frozen=True, slots=True)
class RagHit:
    chunk_id: str
    text: str
    score: float
    source: str = ""
    source_path: str = ""
    line_no: int = 0
    role: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "score": round(self.score, 4),
            "source": self.source,
            "source_path": self.source_path,
            "line_no": self.line_no,
            "role": self.role,
            "metadata": dict(self.metadata),
        }


def make_chunk_id(source: str, line_no: int, offset: int, text: str) -> str:
    """确定性 chunk_id（同内容同 ID，便于幂等 upsert）。"""
    h = hashlib.sha1()
    h.update(f"{source}|{line_no}|{offset}|".encode("utf-8"))
    h.update(text.encode("utf-8"))
    return "ck-" + h.hexdigest()[:16]


__all__ = ["RagChunk", "RagHit", "make_chunk_id"]
