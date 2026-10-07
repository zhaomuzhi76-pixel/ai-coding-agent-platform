"""多模态输入路由：把原始输入归类到模态集合。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import FrozenSet
from backend.providers.selection.contracts import Modality

@dataclass(frozen=True)
class RoutedInput:
    text: str = ""
    images: tuple[str, ...] = ()
    audios: tuple[str, ...] = ()
    required_modalities: FrozenSet[Modality] = frozenset()

def route(text: str = "", images: tuple[str, ...] = (),
          audios: tuple[str, ...] = ()) -> RoutedInput:
    req = {Modality.TEXT}
    if images: req.add(Modality.IMAGE)
    if audios: req.add(Modality.AUDIO)
    return RoutedInput(text=text, images=images, audios=audios,
                       required_modalities=frozenset(req))
