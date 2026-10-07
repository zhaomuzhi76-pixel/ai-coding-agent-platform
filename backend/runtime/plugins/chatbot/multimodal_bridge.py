"""多模态桥接。职责：把选择绑定 + 输入 + 输出诉求 翻译为 BridgePlan。
不路由领域，不组装响应。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import FrozenSet, Optional
from backend.providers.multimodal.router import route
from backend.providers.multimodal.output_orchestrator import plan_output
from backend.providers.selection.contracts import Modality, SelectionBinding
from backend.providers.selection.model_catalog import ModelCatalog
from backend.providers.selection.modality_gate import check_input

MODE_LLM_MISSING = "llm_missing"
MODE_INPUT_REJECTED = "input_rejected"
MODE_UNSUPPORTED_OUTPUT = "unsupported_output"

@dataclass(frozen=True)
class BridgePlan:
    output_mode: str
    needs_image_gen: bool
    required_input_modalities: FrozenSet[Modality]
    reason: str = ""

def _find(catalog: ModelCatalog, model_id: Optional[str]):
    if model_id is None: return None
    for d in catalog.all():
        if d.id == model_id: return d
    return None

def plan(binding: SelectionBinding, catalog: ModelCatalog,
         text: str, images: tuple[str, ...], audios: tuple[str, ...],
         want_image: bool) -> BridgePlan:
    routed = route(text=text, images=images, audios=audios)
    llm = _find(catalog, binding.llm_id)
    if llm is None:
        return BridgePlan(MODE_LLM_MISSING, False, routed.required_modalities,
                          "未选择 LLM 或所选 LLM 不在 catalog")
    gate = check_input(llm, routed.required_modalities)
    if not gate.allowed:
        return BridgePlan(MODE_INPUT_REJECTED, False, routed.required_modalities, gate.reason)
    ig = _find(catalog, binding.image_gen_id)
    try:
        out = plan_output(llm, ig, want_image)
    except ValueError as e:
        return BridgePlan(MODE_UNSUPPORTED_OUTPUT, False, routed.required_modalities, str(e))
    return BridgePlan(out.mode, out.needs_image_gen, routed.required_modalities)
