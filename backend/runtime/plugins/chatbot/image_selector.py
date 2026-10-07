"""智能配图决策。职责：决定「何时配图」「配哪张」。

三级优先级（工业级，避免幻觉图）：
    1) RAG 检索到真图 → 展示（retrieved，最高优先）
    2) 用户明确要图（want_image）或关键词触发 → 文生图（generated）
    3) RAG 无图 + 未明确要图 → 不配图（避免编造）

不负责：
    - 实际检索（rag_bridge 管）
    - 实际生图（image_gen_bridge 管）
    - 渲染（前端管）
"""
from __future__ import annotations

from typing import Any, Iterable, List

from backend.config.rag_governance import get_rag_config

# ── 数据/阈值（从 backend/config/rag_governance 读，不硬编码）──
# 关键词表：backend/data/rag_intent_keywords.json
# 阈值：env RAG_MAX_AUTO_PROMPT_LEN 覆盖
#   （兼容旧常量名：`IMAGE_INTENT_KEYWORDS` / `MAX_AUTO_PROMPT_LEN`
#    仍作为模块属性存在，但动态读 rag_cfg）


def _intent_keywords() -> frozenset:
    """动态获取图片意图关键词（支持 env 更新 + cache_clear 后 reload）。"""
    return get_rag_config().intent_keywords


def _max_auto_prompt_len() -> int:
    """动态获取最大问题长度阈值。"""
    return get_rag_config().max_auto_prompt_len


def has_rag_images(rag_ctx: Any) -> bool:
    """RAG 检索是否返回了真图。"""
    if rag_ctx is None:
        return False
    imgs = getattr(rag_ctx, "images", None)
    if not imgs:
        return False
    try:
        return len(imgs) > 0
    except TypeError:
        return False


def is_image_intent(text: str) -> bool:
    """用户是否明确问图片（读配置关键词）。"""
    t = (text or "").strip()
    if not t:
        return False
    return any(k in t for k in _intent_keywords())


def should_auto_generate(
    text: str,
    rag_ctx: Any,
    user_images: Iterable[str] = (),
) -> bool:
    """是否自动触发「文生图」。

    规则（AND）：
        1) 用户没上传图（有上传就不需要生成）
        2) RAG 没有真图（有真图就不用生成，避免重复）
        3) 用户问题是"要图"的（含关键词）+ 长度合适
    """
    # 规则 1：用户已上传图 → 不生成
    if user_images and len(list(user_images)) > 0:
        return False
    # 规则 2：RAG 已有图 → 不生成（避免重复 / 避免覆盖真实图）
    if has_rag_images(rag_ctx):
        return False
    # 规则 3：必须明确"要图" + 长度合适
    t = (text or "").strip()
    if not t or len(t) > _max_auto_prompt_len() or "\n" in t:
        return False
    return is_image_intent(t)


def dedup_images(images: Iterable[Any]) -> List[Any]:
    """按 id 去重，retrieved 优先于 generated / input_echo。"""
    seen: dict = {}
    priority = {"retrieved": 0, "generated": 1, "input_echo": 2}
    for a in images:
        aid = getattr(a, "id", None)
        if not aid:
            continue
        src = getattr(a, "source", None)
        src_v = getattr(src, "value", str(src)) if src else ""
        rank = priority.get(src_v, 9)
        prev = seen.get(aid)
        if prev is None or rank < prev[0]:
            seen[aid] = (rank, a)
    return [v[1] for v in sorted(seen.values(), key=lambda x: x[0])]


def summarize_sources(images: Iterable[Any]) -> dict:
    """统计各来源数量：retrieved / generated / input_echo。"""
    out = {"retrieved": 0, "generated": 0, "input_echo": 0, "other": 0}
    for a in images:
        src = getattr(a, "source", None)
        v = getattr(src, "value", str(src)) if src else ""
        if v in out:
            out[v] += 1
        else:
            out["other"] += 1
    return out




# ═══════════════════════════════════════════════════════════════
# 图片相关性过滤（避免返回不相关图）
# ═══════════════════════════════════════════════════════════════

def _tokens(text: str) -> set:
    """中英文 token（中文按字，英文按词）。"""
    import re
    return {
        m.group(0).lower()
        for m in re.finditer(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+", text or "")
    }


def _image_match_score(query_tokens: set, img: Any, hit_text: str = "") -> float:
    """单张图与 query 的相关性（alt_text + 关联 chunk 文本命中数）。"""
    if not query_tokens:
        return 0.0
    alt = str(getattr(img, "alt_text", "") or "")
    tokens = _tokens(alt) | _tokens(hit_text)
    if not tokens:
        return 0.0
    overlap = len(query_tokens & tokens)
    return overlap / max(1, len(query_tokens))


def filter_relevant_images(
    query: str,
    images: list,
    *,
    hit_texts: list | None = None,
    max_images: int = 2,
    min_score: float = 0.3,
) -> list:
    """按 query 相关性过滤图片。

    Args:
        query: 用户查询
        images: RagContext.images 或等价列表
        hit_texts: 与 images 一一对应的 hit 文本（可选，增强匹配）
        max_images: 最多保留几张
        min_score: 相关性阈值（低于丢弃）

    Returns:
        过滤后的图片列表（按相关性降序）
    """
    if not images:
        return []
    q_tokens = _tokens(query)
    if not q_tokens:
        return list(images)[:max_images]

    scored = []
    texts = hit_texts or [""] * len(images)
    for i, img in enumerate(images):
        htext = texts[i] if i < len(texts) else ""
        score = _image_match_score(q_tokens, img, htext)
        scored.append((score, img))

    # 按分数降序
    scored.sort(key=lambda x: -x[0])

    # 过滤 + 上限
    result = [img for score, img in scored if score >= min_score][:max_images]

    # 兜底：全被过滤时，返回最高分那张（避免问"玉米"却无图）
    if not result and scored:
        result = [scored[0][1]]
    return result


__all__ = [
    "_intent_keywords",
    "_max_auto_prompt_len",
    "has_rag_images",
    "is_image_intent",
    "should_auto_generate",
    "dedup_images",
    "summarize_sources",
    "filter_relevant_images",
]
