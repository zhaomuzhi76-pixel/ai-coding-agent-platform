"""模态门控：输入校验与输出计划解析。check_output 已移除——全仓无调用，
且 resolve_output_plan 已含输出模态判定，避免职责漂移。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import FrozenSet, Optional
from backend.providers.selection.contracts import ModelDescriptor, Modality

@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    reason: str = ""
    suggestion: str = ""

def check_input(d: ModelDescriptor, need: FrozenSet[Modality]) -> GateDecision:
    miss = need - d.input_modalities
    if not miss: return GateDecision(True)
    return GateDecision(False, f"{d.display_name} 不支持输入 {sorted(m.value for m in miss)}",
                        "请切换支持该模态的模型")

def resolve_output_plan(llm: ModelDescriptor, image_gen: Optional[ModelDescriptor],
                        need_image: bool) -> tuple[bool, str]:
    if not need_image: return True, "text_only"
    if llm.supports_output(Modality.IMAGE): return True, "llm_native"
    if image_gen is not None and image_gen.supports_output(Modality.IMAGE):
        return True, "llm_plus_image_gen"
    return False, "unsupported"
