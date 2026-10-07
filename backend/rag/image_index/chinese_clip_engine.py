"""Chinese-CLIP 编码引擎（插件化 · 兼容 transformers 4.x/5.x）。

职责：单一（encode_text / encode_texts / encode_image / encode_images / dim）。

输出兼容：
  · transformers 4.x：get_*_features 返回 tensor
  · transformers 5.x：返回 BaseModelOutputWithPooling（含 .pooler_output）

env:
  IMAGE_INDEX_ENGINE=chinese   → 用本引擎（默认）
  RAG_CLIP_MODEL               → 模型名，默认 OFA-Sys/chinese-clip-vit-base-patch16
"""
from __future__ import annotations
import logging
import os
from typing import List, Optional, Sequence

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "OFA-Sys/chinese-clip-vit-base-patch16"


def _pick_device() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _to_tensor(v):
    """归一化输出：tensor | ModelOutput → tensor。"""
    if hasattr(v, "pooler_output") and v.pooler_output is not None:
        return v.pooler_output
    if hasattr(v, "last_hidden_state") and v.last_hidden_state is not None:
        # fallback: 取 [CLS] token
        return v.last_hidden_state[:, 0, :]
    # 尝试像 tensor
    if hasattr(v, "norm"):
        return v
    # 尝试从 tuple / dict 里解
    if isinstance(v, (tuple, list)) and v:
        for x in v:
            if hasattr(x, "norm"):
                return x
    raise TypeError("cannot extract tensor from {}".format(type(v).__name__))


class ChineseClipEmbedder:
    """Chinese-CLIP 编码器（懒加载）。"""

    def __init__(self, model_name: Optional[str] = None,
                 device: Optional[str] = None):
        self._model_name = model_name or os.getenv("RAG_CLIP_MODEL", _DEFAULT_MODEL)
        self._device = device or _pick_device()
        self._model = None
        self._processor = None
        self._dim: Optional[int] = None

    def _ensure(self):
        if self._model is not None:
            return
        from transformers import ChineseCLIPModel, ChineseCLIPProcessor
        logger.info("[chinese-clip] loading %s on %s",
                    self._model_name, self._device)
        self._model = ChineseCLIPModel.from_pretrained(self._model_name
                                                        ).to(self._device).eval()
        self._processor = ChineseCLIPProcessor.from_pretrained(self._model_name)
        try:
            import torch
            with torch.no_grad():
                dummy = self._processor(text=["x"], return_tensors="pt",
                                        padding=True).to(self._device)
                v = _to_tensor(self._model.get_text_features(**dummy))
            self._dim = int(v.shape[-1])
        except Exception:
            self._dim = 512

    @property
    def dim(self) -> int:
        if self._dim is None:
            self._ensure()
        return self._dim or 512

    def _normalize(self, v):
        import torch
        if not torch.is_tensor(v):
            v = torch.as_tensor(v)
        return v / v.norm(dim=-1, keepdim=True).clamp(min=1e-12)

    def encode_texts(self, texts: Sequence[str]) -> List[List[float]]:
        self._ensure()
        import torch
        items = [t or "" for t in texts]
        with torch.no_grad():
            inputs = self._processor(text=items, return_tensors="pt",
                                     padding=True, truncation=True,
                                     max_length=77).to(self._device)
            v = _to_tensor(self._model.get_text_features(**inputs))
            v = self._normalize(v)
        return v.cpu().tolist()

    def encode_text(self, text: str) -> List[float]:
        return self.encode_texts([text or ""])[0]

    def encode_images(self, images) -> List[List[float]]:
        self._ensure()
        import torch
        from PIL import Image
        pil_list = []
        for it in images:
            if isinstance(it, str):
                pil_list.append(Image.open(it).convert("RGB"))
            else:
                pil_list.append(it.convert("RGB") if hasattr(it, "convert") else it)
        with torch.no_grad():
            inputs = self._processor(images=pil_list,
                                     return_tensors="pt").to(self._device)
            v = _to_tensor(self._model.get_image_features(**inputs))
            v = self._normalize(v)
        return v.cpu().tolist()

    def encode_image(self, pil_or_path) -> List[float]:
        return self.encode_images([pil_or_path])[0]


def make_engine(model_name: Optional[str] = None,
                device: Optional[str] = None) -> ChineseClipEmbedder:
    return ChineseClipEmbedder(model_name=model_name, device=device)


def is_enabled() -> bool:
    return os.getenv("IMAGE_INDEX_ENGINE", "chinese").lower() == "chinese"


__all__ = ["ChineseClipEmbedder", "make_engine", "is_enabled"]
