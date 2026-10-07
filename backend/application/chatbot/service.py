"""Chatbot application 服务。职责：编排 L2 插件 + LLM + 图片生成 + RAG 检索。
不实现路由、不实现门控、不组装底层协议。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
from backend.application.chatbot.selection_resolver import apply_defaults, resolve_defaults
from backend.providers.multimodal.contracts import (
    ImageArtifact, ImageSource, MultimodalResponse)
from backend.providers.selection.contracts import ModelDescriptor, ModelKind, SelectionBinding
from backend.providers.selection.model_catalog import ModelCatalog
from backend.providers.selection.session_binding import SessionBindingStore
from backend.runtime.plugins.chatbot import ChatbotPlugin, ChatbotRequest
from backend.rag.generation import (
    build_prompt as rag_build_prompt,
    format_answer_with_citations,
    make_grounded_answer,
)

RAG_PROMPT_TEMPLATE = (
    "请参考以下资料回答问题，资料不足时明确说明。\n\n"
    "--- 参考资料 ---\n{context}\n---\n\n"
    "用户问题：{question}"
)

@dataclass(frozen=True)
class ChatbotReply:
    response: MultimodalResponse
    domain: str
    binding: SelectionBinding
    output_mode: str
    reason: str
    default_notes: tuple[str, ...]
    llm_error: str = ""
    image_error: str = ""
    rag_hits: int = 0

class ChatbotService:
    def __init__(self, *, plugin: ChatbotPlugin, session_store: SessionBindingStore,
                 model_catalog: ModelCatalog,
                 llm_bridge: Any = None, image_gen_bridge: Any = None,
                 rag_bridge: Any = None) -> None:
        self._plugin = plugin
        self._store = session_store
        self._catalog = model_catalog
        self._llm = llm_bridge
        self._image_gen = image_gen_bridge
        self._rag = rag_bridge

    def _ensure_binding(self, session_id: str) -> tuple[SelectionBinding, tuple[str, ...]]:
        b = self._store.get(session_id)
        notes = resolve_defaults(b, self._catalog).notes
        if notes:
            b = apply_defaults(b, self._catalog)
            self._store.set(session_id, b)
        return b, notes

    def _find(self, model_id: Optional[str]) -> Optional[ModelDescriptor]:
        if not model_id:
            return None
        for d in self._catalog.all():
            if d.id == model_id:
                return d
        return None

    def _resolve_image_gen(self, b: SelectionBinding) -> Optional[ModelDescriptor]:
        d = self._find(b.image_gen_id)
        if d is not None:
            return d
        for cand in self._catalog.list_by_kind(ModelKind.IMAGE_GEN):
            return cand
        return None

    @staticmethod
    @staticmethod
    def _should_auto_image(text: str, images: tuple, rag_ctx: Any = None) -> bool:
        """委托给 image_selector.should_auto_generate（工业级决策）。"""
        from backend.runtime.plugins.chatbot.image_selector import (
            should_auto_generate,
        )
        return should_auto_generate(text, rag_ctx, images)

    def _call_llm(self, b: SelectionBinding, prompt: str,
                  images: tuple[str, ...]) -> tuple[str, str]:
        if self._llm is None or not b.llm_id:
            return "", ""
        try:
            text = self._llm.generate_text(
                b.llm_id, prompt,
                images_b64=list(images) if images else None)
            return text, ""
        except Exception as e:
            return "", f"{type(e).__name__}: {e}"

    def _call_image_gen(self, b: SelectionBinding, prompt: str) -> tuple[list, str]:
        if self._image_gen is None:
            return [], ""
        desc = self._resolve_image_gen(b)
        if desc is None:
            return [], "无可用图片生成模型"
        try:
            art = self._image_gen.generate_image(desc, prompt)
            return [art], ""
        except Exception as e:
            return [], f"{type(e).__name__}: {e}"

    def _call_rag(self, text: str, domains=None) -> Any:
        if self._rag is None or not text.strip():
            return None
        try:
            return self._rag.retrieve(text, domains=domains or None,
                                       curated_first=True)
        except TypeError:
            return self._rag.retrieve(text)
        except Exception:
            return None

    def reply(self, *, session_id: str, text: str = "",
              images: tuple[str, ...] = (), audios: tuple[str, ...] = (),
              want_image: bool = False,
              domains: Optional[list] = None) -> ChatbotReply:
        b, notes = self._ensure_binding(session_id)
        res = self._plugin.handle(ChatbotRequest(
            session_id=session_id, text=text, images=images,
            audios=audios, want_image=want_image))

        rag_ctx = self._call_rag(text, domains=domains)
        prompt_for_llm = text
        grounded = None
        final_text = ""

        if rag_ctx is not None and getattr(rag_ctx, "has_context", False):
            # ★ 走 grounded 生成层（置信度 + 拒答 + 溯源）
            raw_hits = list(getattr(rag_ctx, "raw_hits", ()) or [])
            if raw_hits:
                grounded = make_grounded_answer(text, raw_hits)
                # ★ 关键：只有 reranker 生效才信任 confidence
                has_rerank = bool(raw_hits
                                  and raw_hits[0].get("has_rerank", False))

                if grounded.refused:
                    # 置信度不足 → 拒答
                    final_text = grounded.answer
                    llm_text, llm_err = "", ""
                elif has_rerank and grounded.confidence >= 0.9:
                    # ✅ 有 rerank + 高置信 → 直返原文（0 加工 = 0 幻觉）
                    final_text = (
                        "根据知识库原文：\n\n"
                        + grounded.context_text
                        + "\n\n**来源：**\n"
                        + "\n".join(
                            f"  [{c.idx}] {c.source}"
                            + (f" p.{c.page}" if c.page else "")
                            for c in grounded.citations
                        )
                    )
                    llm_text, llm_err = "", ""
                else:
                    # ⚠️ 无 rerank 或中置信 → LLM 尝试整理
                    prompt_for_llm = rag_build_prompt(
                        grounded.context_text, text)
                    llm_text, llm_err = self._call_llm(
                        b, prompt_for_llm, images)
                    if llm_text and "暂无" not in llm_text:
                        grounded2 = make_grounded_answer(
                            text, raw_hits, answer=llm_text)
                        final_text = format_answer_with_citations(grounded2)
                    else:
                        # LLM 拒答 → 拒答（不直返，避免乱码暴露）
                        final_text = "暂无对应资料"
            else:
                # 无 raw_hits，退回老模板
                prompt_for_llm = RAG_PROMPT_TEMPLATE.format(
                    context=rag_ctx.context_text, question=text)
                llm_text, llm_err = self._call_llm(
                    b, prompt_for_llm, images)
                final_text = llm_text or res.response.text
        else:
            llm_text, llm_err = self._call_llm(b, prompt_for_llm, images)
            final_text = llm_text or res.response.text

        artifacts: list = []
        img_err = ""
        if rag_ctx is not None:
            from backend.runtime.plugins.chatbot.image_selector import (
                filter_relevant_images,
            )
            filtered = filter_relevant_images(
                text, list(rag_ctx.images), max_images=2,
            )
            artifacts.extend(filtered)

        auto_img = self._should_auto_image(text, images, rag_ctx)
        if want_image or auto_img:
            gen_artifacts, img_err = self._call_image_gen(b, text)
            artifacts.extend(gen_artifacts)

        for i, b64 in enumerate(images):
            artifacts.append(ImageArtifact(
                id=f"echo-{i}", mime="image/png",
                source=ImageSource.INPUT_ECHO, b64=b64,
                alt_text=f"用户上传图片 {i+1}"))

        rag_hits = getattr(rag_ctx, "hit_count", 0) if rag_ctx else 0
        response = MultimodalResponse(
            text=final_text, images=tuple(artifacts),
            meta={"llm": b.llm_id or "", "output_mode": res.output_mode,
                  "domain": res.domain, "image_count": len(artifacts),
                  "rag_hits": rag_hits},
        )
        return ChatbotReply(response=response, domain=res.domain, binding=b,
                            output_mode=res.output_mode, reason=res.reason,
                            default_notes=notes,
                            llm_error=llm_err, image_error=img_err,
                            rag_hits=rag_hits)

    def set_llm(self, session_id: str, llm_id: str) -> SelectionBinding:
        return self._store.update_llm(session_id, llm_id)

    def set_image_gen(self, session_id: str, image_gen_id: Optional[str]) -> SelectionBinding:
        return self._store.update_image_gen(session_id, image_gen_id)

    def get_binding(self, session_id: str) -> SelectionBinding:
        return self._store.get(session_id)
