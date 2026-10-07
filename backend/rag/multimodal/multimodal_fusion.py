"""图文融合检索（工业级 RRF）。

职责：把 text_hits 和 image_hits 用 RRF 融合成统一排序。
不做：不编码、不查询任何 store（纯函数）。
RRF 公式：score(d) = Σ weight_i / (k + rank_i(d))
"""
from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


@dataclass(frozen=True)
class FusedHit:
    """融合后的统一命中。kind: 'text' | 'image'。"""
    hit_id: str
    kind: str
    score: float
    text: str = ""
    images: Sequence[Any] = ()
    source: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "metadata",
                           MappingProxyType(dict(self.metadata)))
        object.__setattr__(self, "images", tuple(self.images))

    def to_dict(self) -> dict:
        return {
            "id": self.hit_id, "kind": self.kind, "score": round(self.score, 6),
            "text": self.text, "source": self.source,
            "images": [img.to_dict() if hasattr(img, "to_dict") else img
                       for img in self.images],
            "metadata": dict(self.metadata),
        }


def rrf_fuse(
    text_hits: Optional[Iterable[Any]] = None,
    image_hits: Optional[Iterable[Any]] = None,
    *,
    k: int = 60,
    w_text: float = 1.0,
    w_image: float = 1.0,
    top_k: int = 10,
) -> List[FusedHit]:
    """RRF 融合。空输入不崩，单输入直接 RRF。

    Args:
        text_hits: 文本命中（dict 或对象，需有 id/text/images）
        image_hits: 图片命中（dict 或对象，需有 image_id/score）
        k: RRF 平滑常数（默认 60，工业标准）
        w_text / w_image: 权重
        top_k: 返回 Top-K
    """
    th = list(text_hits or [])
    ih = list(image_hits or [])
    if not th and not ih:
        return []

    scores: Dict[str, float] = {}
    payload: Dict[str, FusedHit] = {}

    # ---- 文本侧 ----
    for rank, h in enumerate(th, 1):
        hid = _hid(h)
        if not hid:
            continue
        scores[hid] = scores.get(hid, 0.0) + w_text / (k + rank)
        if hid not in payload:
            payload[hid] = FusedHit(
                hit_id=hid, kind="text", score=0.0,
                text=_htext(h), images=_himgs(h),
                source=_hsource(h), metadata=_hmeta(h))

    # ---- 图片侧 ----
    for rank, h in enumerate(ih, 1):
        hid = _iid(h)
        if not hid:
            continue
        key = f"img:{hid}"
        scores[key] = scores.get(key, 0.0) + w_image / (k + rank)
        if key not in payload:
            payload[key] = FusedHit(
                hit_id=key, kind="image", score=0.0,
                text=_itext(h), images=(),
                source=_isrc(h), metadata=_imeta(h))

    # ---- 填分数 + 排序 ----
    out = []
    for key, sc in scores.items():
        fh = payload[key]
        out.append(FusedHit(
            hit_id=fh.hit_id, kind=fh.kind, score=sc,
            text=fh.text, images=fh.images,
            source=fh.source, metadata=fh.metadata))
    out.sort(key=lambda x: x.score, reverse=True)
    return out[:max(1, int(top_k))]


# ---- 辅助 ----

def _get(o, *keys, default=None):
    for k in keys:
        if isinstance(o, dict) and o.get(k) is not None:
            return o[k]
        v = getattr(o, k, None)
        if v is not None:
            return v
    return default


def _hid(h): return _get(h, "chunk_id", "id", "hit_id", default="")
def _iid(h): return _get(h, "image_id", "id", default="")
def _htext(h): return str(_get(h, "text", default="") or "")
def _itext(h): return str(_get(h, "text", "caption", default="") or "")
def _hsource(h): return str(_get(h, "source", default="") or "")
def _isrc(h): return str(_get(h, "source", "origin_hash", default="") or "")
def _himgs(h):
    imgs = _get(h, "images", default=())
    return tuple(imgs or ())
def _hmeta(h):
    return dict(_get(h, "metadata", default={}) or {})
def _imeta(h):
    m = _get(h, "metadata", default=None)
    if m:
        return dict(m)
    return {}


__all__ = ["FusedHit", "rrf_fuse"]
