"""输出编排：判定是否出图以及走哪条路径。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from backend.providers.selection.contracts import ModelDescriptor
from backend.providers.selection.modality_gate import resolve_output_plan

@dataclass(frozen=True)
class OutputPlan:
    mode: str
    needs_image_gen: bool

def plan_output(llm: ModelDescriptor, image_gen: Optional[ModelDescriptor],
                need_image: bool) -> OutputPlan:
    ok, mode = resolve_output_plan(llm, image_gen, need_image)
    if not ok:
        raise ValueError(f"无法出图：LLM={llm.display_name} 且无 image_gen")
    return OutputPlan(mode=mode, needs_image_gen=(mode == "llm_plus_image_gen"))
