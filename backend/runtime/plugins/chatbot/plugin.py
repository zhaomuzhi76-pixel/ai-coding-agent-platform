"""Chatbot 插件主入口。职责：编排，不做路由/门控/产物/组装细节。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from backend.providers.multimodal.contracts import MultimodalResponse
from backend.providers.selection.contracts import SelectionBinding
from backend.providers.selection.model_catalog import ModelCatalog
from backend.providers.selection.session_binding import SessionBindingStore
from backend.runtime.plugins.chatbot.artifact_emitter import emit_text_only
from backend.runtime.plugins.chatbot.capability import CapabilitySpec
from backend.runtime.plugins.chatbot.domain_router import route_domain, RouteDecision
from backend.runtime.plugins.chatbot.multimodal_bridge import plan, BridgePlan
from backend.runtime.plugins.chatbot.selection_binder import resolve_binding

@dataclass(frozen=True)
class ChatbotRequest:
    session_id: str
    text: str = ""
    images: tuple[str, ...] = ()
    audios: tuple[str, ...] = ()
    want_image: bool = False

@dataclass(frozen=True)
class ChatbotResult:
    response: MultimodalResponse
    domain: str
    binding: SelectionBinding
    output_mode: str
    reason: str
    capability: CapabilitySpec

class ChatbotPlugin:
    def __init__(self, *, session_store: SessionBindingStore,
                 model_catalog: ModelCatalog) -> None:
        self._store = session_store
        self._catalog = model_catalog

    @property
    def capability(self) -> CapabilitySpec:
        return CapabilitySpec.default()

    def handle(self, req: ChatbotRequest) -> ChatbotResult:
        res = resolve_binding(self._store, req.session_id, self._catalog)
        decision: RouteDecision = route_domain(req.text)
        bridge: BridgePlan = plan(res.binding, self._catalog, req.text,
                                  req.images, req.audios, req.want_image)
        llm_display = res.binding.llm_id or "(未选)"
        text = self._render_text(req.text, decision, bridge)
        response = emit_text_only(text=text, llm_display=llm_display,
                                  output_mode=bridge.output_mode)
        return ChatbotResult(response=response, domain=decision.domain,
                             binding=res.binding, output_mode=bridge.output_mode,
                             reason=bridge.reason, capability=self.capability)

    @staticmethod
    def _render_text(text: str, decision: RouteDecision, bridge: BridgePlan) -> str:
        tag = f"[{decision.domain}]"
        if bridge.output_mode == "text_only" or bridge.needs_image_gen:
            return f"{tag} {text}"
        return f"{tag} {text} ({bridge.output_mode}: {bridge.reason})"
