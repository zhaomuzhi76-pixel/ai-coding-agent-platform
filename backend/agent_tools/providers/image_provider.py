"""图片向量检索工具 Provider。职责：
  把 ImageRetriever 暴露为 agent 工具 image.search_similar / image.search_by_text。
不做编码、不做存储、不做检索细节（retriever 管）。
与 rag_provider 边界：本 provider 管"图搜图/文搜图"。
"""
from __future__ import annotations
import os
from typing import Any, Optional

from backend.agent_tools.contracts import (
    ToolCall, ToolCategory, ToolDescriptor, ToolDomain, ToolResult)

TOOL_SIMILAR = "image.search_similar"
TOOL_BY_TEXT = "image.search_by_text"


class ImageSearchProvider:
    def __init__(self, *, retriever: Any) -> None:
        if retriever is None:
            raise ValueError("retriever required")
        self._retriever = retriever
        # [SC] 精确匹配器（可选 · 未装则优雅降级）
        try:
            from backend.rag.image_index.exact_matcher import (
                get_default_matcher)
            self._exact = get_default_matcher()
        except Exception:
            self._exact = None

    def descriptors(self) -> list:
        return [
            ToolDescriptor(
                name=TOOL_SIMILAR,
                description="以图搜图：上传图片路径，返回库内相似图片",
                category=ToolCategory.IMAGE, domain=ToolDomain.GENERAL,
                server="local", tags=("image", "clip")),
            ToolDescriptor(
                name=TOOL_BY_TEXT,
                description="以文搜图：输入文本描述，返回库内匹配图片",
                category=ToolCategory.IMAGE, domain=ToolDomain.GENERAL,
                server="local", tags=("image", "clip")),
        ]

    def can_handle(self, name: str) -> bool:
        return name in (TOOL_SIMILAR, TOOL_BY_TEXT)

    def execute(self, call: ToolCall) -> ToolResult:
        if call.name == TOOL_SIMILAR:
            return self._search_similar(call)
        if call.name == TOOL_BY_TEXT:
            return self._search_by_text(call)
        return ToolResult(name=call.name, ok=False,
                          error=f"unknown image tool: {call.name}")

    # ---------- 内部 ----------
    def _search_similar(self, call: ToolCall) -> ToolResult:
        path = str(call.arguments.get("path")
                   or call.arguments.get("query") or "").strip()
        if not path:
            return ToolResult(name=call.name, ok=False, error="path required")
        if not os.path.isfile(path):
            return ToolResult(name=call.name, ok=False,
                              error=f"文件不存在: {path}")
        try:
            limit = int(call.arguments.get("limit", 5) or 5)
        except (TypeError, ValueError):
            limit = 5
        try:
            rep = self._retriever.search_by_image(path, top_k=limit)
        except FileNotFoundError:
            return ToolResult(name=call.name, ok=False,
                              error=f"文件不存在: {path}")
        except Exception as e:
            return ToolResult(name=call.name, ok=False,
                              error=f"{type(e).__name__}: {e}")
        return self._format(rep)

    def _search_by_text(self, call: ToolCall) -> ToolResult:
        text = str(call.arguments.get("query")
                   or call.arguments.get("text") or "").strip()
        if not text:
            return ToolResult(name=call.name, ok=False, error="query required")
        try:
            limit = int(call.arguments.get("limit", 5) or 5)
        except (TypeError, ValueError):
            limit = 5
        # [SC] 路径 1：精确 class_name 匹配（优先 · 100% 准确）
        if self._exact is not None:
            try:
                exact_hits = self._exact.search(text, limit=limit)
                if exact_hits:
                    cls = exact_hits[0].get("class_name", "")
                    n = len(exact_hits)
                    # [FS3] 结构化 output：LLM 能直接基于它回答
                    lines = [
                        "已找到 {} 张「{}」的图片（精确匹配）：".format(n, cls),
                    ]
                    for i, h in enumerate(exact_hits[:5], 1):
                        lines.append("  [{}] {} | {}".format(
                            i, h.get("class_name", ""),
                            h.get("url", "")))
                    return ToolResult(
                        name=call.name, ok=True,
                        output="\n".join(lines),
                        meta={"hit_count": n,
                              "images": exact_hits,
                              "class_name": cls,
                              "source": "exact_match"})
            except Exception:
                pass
        # [SC] 路径 2：CLIP 语义兜底
        try:
            rep = self._retriever.search_by_text(text, top_k=limit)
        except Exception as e:
            return ToolResult(name=call.name, ok=False,
                              error=f"{type(e).__name__}: {e}")
        return self._format(rep)

    @staticmethod
    def _extract_class_v2(h) -> str:
        """从 hit 多源提取类名（v2 · 更多源）。"""
        # 1) 直接字段（含可能的变体）
        for attr in ("class_name", "text", "name", "label", "category",
                     "class", "kind"):
            v = getattr(h, attr, None)
            if v is None:
                continue
            s = str(v).strip()
            if s and s not in ("<none>", "None"):
                return s
        # 2) 从 origin_hash / image_id 反查 desc DB
        origin = getattr(h, "origin_hash", "") or ""
        if origin:
            try:
                import sqlite3, glob
                for db in glob.glob("vector_db/lite_image_desc.db"):
                    conn = sqlite3.connect(db)
                    c = conn.cursor()
                    # 尝试多种匹配
                    for q in [
                        "SELECT * FROM docs WHERE id = ? LIMIT 1",
                        "SELECT * FROM docs WHERE doc_id = ? LIMIT 1",
                    ]:
                        try:
                            c.execute(q, (origin,))
                            row = c.fetchone()
                            if row:
                                for cell in row:
                                    s = str(cell)
                                    if s and "。" not in s and len(s) < 30:
                                        conn.close()
                                        return s
                        except Exception:
                            continue
                    conn.close()
            except Exception:
                pass
        return ""


    @staticmethod
    def _format(rep) -> ToolResult:
        hits = list(getattr(rep, "hits", ()) or ())
        if not hits:
            return ToolResult(name="", ok=True, output="(图片库无匹配)",
                              meta={"hit_count": 0, "images": []})
        lines: list = []
        images_meta: list = []
        for i, h in enumerate(hits, 1):
            origin = getattr(h, "origin_hash", "") or ""
            url = "/api/rag/origin/{}".format(origin) if origin else ""
            desc = h.text or getattr(h, "image_id", "")
            lines.append("[{}] {} | score={:.3f} | {}".format(
                i, desc, getattr(h, "score", 0), url))
            # [RIF] url 兜底：metadata.image_path → _to_url()
            meta_dict = dict(getattr(h, "metadata", {}) or {})
            if not url:
                try:
                    from backend.rag.retrieval_paths import _to_url as _tu
                    ip = meta_dict.get("image_path", "") or ""
                    if ip:
                        url = _tu(ip)
                except Exception:
                    pass
            cls_name = ImageSearchProvider._extract_class_v2(h)
            if url:
                images_meta.append({
                    "id": getattr(h, "image_id", "") or "",
                    "url": url,
                    "class_name": cls_name,
                    "alt_text": cls_name,
                    "score": float(getattr(h, "score", 0)),
                })
        return ToolResult(name="", ok=True, output="\n".join(lines),
                          meta={"hit_count": len(hits), "images": images_meta})


def make_image_provider(*, retriever: Any) -> ImageSearchProvider:
    return ImageSearchProvider(retriever=retriever)


__all__ = ["ImageSearchProvider", "make_image_provider",
           "TOOL_SIMILAR", "TOOL_BY_TEXT"]
