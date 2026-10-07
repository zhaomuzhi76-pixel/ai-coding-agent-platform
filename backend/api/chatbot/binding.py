"""协议层 DTO 与序列化。职责：raw dict <-> typed DTO <-> 响应 dict。
无框架依赖，不做业务。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional
from backend.providers.multimodal.contracts import ImageArtifact, MultimodalResponse
from backend.providers.selection.contracts import (
    EmbeddingDescriptor, ModelDescriptor, RerankDescriptor)

@dataclass(frozen=True)
class ModelItem:
    id: str
    provider: str
    kind: str
    display: str
    input_modalities: tuple[str, ...]
    output_modalities: tuple[str, ...]

@dataclass(frozen=True)
class ChatBody:
    text: str
    images: tuple[str, ...]
    audios: tuple[str, ...]
    want_image: bool
    domains: tuple[str, ...] = ()

@dataclass(frozen=True)
class SelectionBody:
    llm_id: Optional[str]
    image_gen_id: Optional[str]

def _require_mapping(raw: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return raw

def _opt_str(v: Any) -> Optional[str]:
    if v is None: return None
    if not isinstance(v, str): raise ValueError("expected str or null")
    return v

def _opt_str_tuple(v: Any) -> tuple[str, ...]:
    if v is None: return ()
    if not isinstance(v, (list, tuple)): raise ValueError("expected list of str")
    for x in v:
        if not isinstance(x, str): raise ValueError("expected list of str")
    return tuple(v)

def parse_chat_body(raw: Any) -> ChatBody:
    m = _require_mapping(raw, "chat body")
    text = m.get("text", "")
    if not isinstance(text, str): raise ValueError("text must be str")
    return ChatBody(
        text=text,
        images=_opt_str_tuple(m.get("images")),
        audios=_opt_str_tuple(m.get("audios")),
        want_image=bool(m.get("want_image", False)),
        domains=_opt_str_tuple(m.get("domains")),
    )

def parse_selection_body(raw: Any) -> SelectionBody:
    m = _require_mapping(raw, "selection body")
    return SelectionBody(
        llm_id=_opt_str(m.get("llm_id")),
        image_gen_id=_opt_str(m.get("image_gen_id")),
    )

def render_model_item(d: ModelDescriptor | EmbeddingDescriptor | RerankDescriptor) -> dict:
    if isinstance(d, ModelDescriptor):
        return {
            "id": d.id, "provider": d.provider, "kind": d.kind.value,
            "display": d.display_name,
            "input_modalities": sorted(m.value for m in d.input_modalities),
            "output_modalities": sorted(m.value for m in d.output_modalities),
        }
    if isinstance(d, EmbeddingDescriptor):
        return {"id": d.id, "provider": d.provider, "kind": "embedding",
                "display": d.display_name, "dim": d.dim}
    if isinstance(d, RerankDescriptor):
        return {"id": d.id, "provider": d.provider, "kind": "rerank",
                "display": d.display_name}
    raise TypeError(f"unsupported descriptor: {type(d).__name__}")

def render_image(a: ImageArtifact) -> dict:
    out: dict[str, Any] = {"id": a.id, "mime": a.mime,
                           "source": a.source.value, "alt_text": a.alt_text}
    if a.url: out["url"] = a.url
    if a.b64: out["b64"] = a.b64
    return out

def render_multimodal_response(r: MultimodalResponse) -> dict:
    return {
        "text": r.text,
        "images": [render_image(a) for a in r.images],
        "meta": dict(r.meta),
    }

def render_model_list(model_catalog, embedding_catalog, rerank_catalog) -> dict:
    groups: dict[str, list[dict]] = {"llm": [], "image_gen": [],
                                     "embedding": [], "rerank": []}
    for d in model_catalog.all():
        groups[d.kind.value].append(render_model_item(d))
    for d in embedding_catalog.all():
        groups["embedding"].append(render_model_item(d))
    for d in rerank_catalog.all():
        groups["rerank"].append(render_model_item(d))
    return {"groups": groups}
