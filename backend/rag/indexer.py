"""RAG 索引器（L1 · 数据集 → chunks → embed → 存向量库）。

职责：
    - 读微调数据集 JSONL
    - 切片（复用 chunker）
    - 向量化（复用 EmbeddingService）
    - 存入向量库（复用 VectorStore）

不负责：
    - 检索（retriever 管）
    - RAG 编排（service 管）
    - UI / HTTP（api 管）
"""
from __future__ import annotations
from backend.core.model_registry.embedding_resolver import resolve_embedding_model
from backend.core.observability.silent import swallow

from backend.config.constants.endpoints import (
    OLLAMA_URL,
)

import json
from pathlib import Path
from typing import Any, Callable

import httpx

from backend.storage.vector_backend import get_vector_store
from backend.storage.vector_config import VectorConfig

from .chunker import chunk_many
from .spec import RagChunk

_EMBED_TIMEOUT = 60.0
_BATCH_SIZE = 16


class RagIndexer:
    VERSION = "1.0"

    def __init__(
        self,
        *,
        vector_config: VectorConfig | None = None,
        base_url: str = "",
        embedding_model: str = "",
    ) -> None:
        # 从 yaml 读默认值（不硬编码）
        cfg_base_url, cfg_model = _load_embed_cfg_from_yaml()

        self.vector_config = vector_config or VectorConfig()
        self.store = get_vector_store(self.vector_config)
        self.base_url = (base_url or cfg_base_url or OLLAMA_URL).rstrip("/")
        self.embedding_model = embedding_model or cfg_model or resolve_embedding_model()

    # ─── 索引 ──────────────────────────────────────
    async def index_dataset(
        self,
        dataset_path: str,
        dataset_id: str = "",
        *,
        on_progress: Callable[[dict], None] | None = None,
    ) -> dict[str, Any]:
        p = Path(dataset_path).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"dataset not found: {p}")

        rows = _read_jsonl(p)
        if not rows:
            return {"indexed": 0, "reason": "empty jsonl"}

        chunks = chunk_many(
            rows,
            source=dataset_id or p.stem,
            source_path=str(p),
        )
        if not chunks:
            return {"indexed": 0, "reason": "no valid chunks"}

        _emit(on_progress, {"stage": "chunked", "count": len(chunks)})

        # 批量 embed + upsert
        total = 0
        for i in range(0, len(chunks), _BATCH_SIZE):
            batch = chunks[i:i + _BATCH_SIZE]
            embs = await self._embed_batch([c.text for c in batch])
            self.store.upsert_documents(
                documents=[c.text for c in batch],
                ids=[c.chunk_id for c in batch],
                metadata=[c.to_metadata() for c in batch],
                embeddings=embs,
            )
            total += len(batch)
            _emit(on_progress, {
                "stage": "indexing", "done": total, "total": len(chunks),
            })

        return {
            "indexed": total,
            "dataset_id": dataset_id or p.stem,
            "dataset_path": str(p),
            "collection": self.vector_config.collection_name,
        }

    async def index_texts(
        self,
        texts: list[str],
        *,
        source: str = "inline",
    ) -> dict[str, Any]:
        """直接索引一批文本（测试 / 快捷入口用）。"""
        if not texts:
            return {"indexed": 0}
        chunks: list[RagChunk] = []
        for i, t in enumerate(texts, 1):
            from .chunker import chunk_text
            chunks.extend(chunk_text(
                t, source=source, line_no=i, role="raw",
            ))
        if not chunks:
            return {"indexed": 0}

        total = 0
        for i in range(0, len(chunks), _BATCH_SIZE):
            batch = chunks[i:i + _BATCH_SIZE]
            embs = await self._embed_batch([c.text for c in batch])
            self.store.upsert_documents(
                documents=[c.text for c in batch],
                ids=[c.chunk_id for c in batch],
                metadata=[c.to_metadata() for c in batch],
                embeddings=embs,
            )
            total += len(batch)
        return {"indexed": total, "collection": self.vector_config.collection_name}

    # ─── 状态 ──────────────────────────────────────
    def count(self) -> int:
        try:
            return int(self.store.count())
        except Exception:
            return 0

    def clear(self) -> dict[str, Any]:
        """清空 collection（危险操作，仅供测试 / 重建）。"""
        try:
            self.store.client.delete_collection(self.vector_config.collection_name)
            self.store = get_vector_store(self.vector_config)
            return {"cleared": True}
        except Exception as exc:
            return {"cleared": False, "error": str(exc)}

    # ─── 内部：embedding 调用（复用 ollama /api/embed）───
    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        async with httpx.AsyncClient(timeout=_EMBED_TIMEOUT) as client:
            r = await client.post(
                f"{self.base_url}/api/embed",
                json={"model": self.embedding_model, "input": texts},
            )
            r.raise_for_status()
            data = r.json()
        embs = data.get("embeddings")
        if not isinstance(embs, list) or len(embs) != len(texts):
            raise RuntimeError(
                f"embedding 响应尺寸不符: got={len(embs) if isinstance(embs, list) else '?'} "
                f"want={len(texts)}"
            )
        return embs



def _load_embed_cfg_from_yaml() -> tuple[str, str]:
    """从 llm_providers.yaml 读默认 embedding 的 (base_url, model)。"""
    try:
        import yaml
        p = Path(__file__).resolve().parents[1] / "config" / "llm_providers.yaml"
        if not p.is_file():
            return "", ""
        d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        embs = d.get("embeddings") or []
        # 找 default: true 的
        target = next(
            (e for e in embs if isinstance(e, dict) and e.get("default")),
            embs[0] if embs else None,
        )
        if not target:
            return "", ""
        provider_name = str(target.get("provider", ""))
        model = str(target.get("model", ""))
        # 找 provider 的 base_url
        base_url = ""
        for p_ in d.get("providers", []) or []:
            if isinstance(p_, dict) and p_.get("name") == provider_name:
                base_url = str(p_.get("base_url", ""))
                break
        return base_url, model
    except Exception:
        return "", ""

def _read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, 1):
            t = raw.strip()
            if not t or t.startswith("#"):
                continue
            try:
                d = json.loads(t)
            except json.JSONDecodeError:
                continue
            if isinstance(d, dict):
                out.append(d)
    return out


def _emit(on_progress: Callable[[dict], None] | None, ev: dict) -> None:
    if on_progress is None:
        return
    try:
        on_progress(ev)
    except Exception as e:
        swallow("rag.indexer:222", e)


__all__ = ["RagIndexer"]
