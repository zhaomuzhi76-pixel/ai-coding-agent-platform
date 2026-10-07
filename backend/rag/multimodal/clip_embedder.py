"""CLIP 向量编码器（工业级插件）。

职责：文本→向量、图片→向量，统一到 CLIP 的 512 维空间。
不做：不存储、不检索、不改语料。
单例懒加载；GPU 优先；模型走 HF 缓存（离线可用）。
"""
from __future__ import annotations
import logging
from typing import List, Optional, Sequence

logger = logging.getLogger(__name__)

_MODEL_NAME = "openai/clip-vit-base-patch32"
_singleton = None


def _to_tensor(out):
    """transformers 5.x 兼容：从模型输出提取 tensor。

    顺序：Tensor 直返 → .text_embeds/.image_embeds → .pooler_output → 首元素
    """
    import torch
    if isinstance(out, torch.Tensor):
        return out
    for attr in ("text_embeds", "image_embeds", "pooler_output"):
        v = getattr(out, attr, None)
        if isinstance(v, torch.Tensor):
            return v
    if isinstance(out, (tuple, list)) and out and isinstance(out[0], torch.Tensor):
        return out[0]
    raise TypeError(f"cannot extract tensor from {type(out).__name__}")


def _ensure_pil(x):
    """兼容：path str 或 PIL.Image → PIL.Image。"""
    try:
        from PIL import Image
    except ImportError as e:
        raise RuntimeError("Pillow 未安装") from e
    if isinstance(x, (str, bytes)):
        with Image.open(x) as im:
            return im.convert("RGB")
    # PIL.Image 或其他
    if hasattr(x, "convert"):
        return x.convert("RGB")
    return x


class ClipEmbedder:
    def __init__(self, model_name: str = _MODEL_NAME, device: Optional[str] = None):
        self._model_name = model_name
        self._device = device
        self._model = None
        self._processor = None
        self._dim = None

    def _lazy(self):
        if self._model is not None:
            return
        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor
        except ImportError as e:
            raise RuntimeError(f"CLIP deps missing: {e}")
        dev = self._device
        if dev is None:
            dev = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("[clip] loading %s on %s", self._model_name, dev)
        self._model = CLIPModel.from_pretrained(self._model_name).to(dev).eval()
        self._processor = CLIPProcessor.from_pretrained(self._model_name)
        self._device = dev
        with torch.no_grad():
            inp = self._processor(text=["warmup"], return_tensors="pt", padding=True)
            inp = {k: v.to(dev) for k, v in inp.items()}
            v = _to_tensor(self._model.get_text_features(**inp))
            self._dim = int(v.shape[-1])

    @property
    def dim(self) -> int:
        self._lazy()
        return self._dim

    def encode_text(self, text: str) -> List[float]:
        return self.encode_texts([text or ""])[0]

    def encode_texts(self, texts: Sequence[str]) -> List[List[float]]:
        self._lazy()
        import torch
        if not texts:
            return []
        clean = [t if t else " " for t in texts]
        with torch.no_grad():
            inp = self._processor(text=clean, return_tensors="pt",
                                  padding=True, truncation=True, max_length=77)
            inp = {k: v.to(self._device) for k, v in inp.items()}
            v = _to_tensor(self._model.get_text_features(**inp))
            v = v / v.norm(dim=-1, keepdim=True).clamp(min=1e-12)
            return v.cpu().tolist()

    def encode_image(self, pil_or_path) -> List[float]:
        return self.encode_images([pil_or_path])[0]

    def encode_images(self, images) -> List[List[float]]:
        self._lazy()
        import torch
        if not images:
            return []
        imgs_pil = [_ensure_pil(x) for x in images]
        with torch.no_grad():
            inp = self._processor(images=imgs_pil, return_tensors="pt")
            inp = {k: v.to(self._device) for k, v in inp.items()}
            v = _to_tensor(self._model.get_image_features(**inp))
            v = v / v.norm(dim=-1, keepdim=True).clamp(min=1e-12)
            return v.cpu().tolist()


def get_embedder() -> ClipEmbedder:
    global _singleton
    if _singleton is None:
        _singleton = ClipEmbedder()
    return _singleton


__all__ = ["ClipEmbedder", "get_embedder"]
