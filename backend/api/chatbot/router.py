"""chat endpoint handler（框架无关）+ 可选 FastAPI 挂载。
职责：解析协议 → 调 L3 service → 序列化。不含业务。"""
from __future__ import annotations
from typing import Any, Callable
from backend.api.chatbot.binding import parse_chat_body, render_multimodal_response
from backend.application.chatbot.service import ChatbotService

def chat_handler(service: ChatbotService, session_id: str, raw_body: Any) -> dict:
    if not session_id:
        raise ValueError("session_id must not be empty")
    body = parse_chat_body(raw_body)
    rep = service.reply(session_id=session_id, text=body.text,
                        images=body.images, audios=body.audios,
                        want_image=body.want_image,
                        domains=list(body.domains))
    return {
        "response": render_multimodal_response(rep.response),
        "domain": rep.domain,
        "output_mode": rep.output_mode,
        "reason": rep.reason,
        "binding": {"llm_id": rep.binding.llm_id,
                    "image_gen_id": rep.binding.image_gen_id},
        "default_notes": list(rep.default_notes),
    }

def register_chat_routes(router: Any, get_service: Callable[[], ChatbotService]) -> None:
    """FastAPI 挂载。未安装 fastapi 时抛错，但不影响本模块导入。"""
    try:
        from fastapi import APIRouter  # noqa: F401
    except ImportError as e:
        raise RuntimeError("fastapi 未安装，无法挂载 chat routes") from e

    @router.post("/api/chatbot/{session_id}/chat")
    def _chat(session_id: str, body: dict) -> dict:
        return chat_handler(get_service(), session_id, body)
