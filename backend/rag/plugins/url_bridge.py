"""URL 编码桥接（单一职责：幂等 try_encode）。

为什么需要桥接层：
  · _to_url 里若直接调 url_encoder，会造成主逻辑 ↔ 插件的硬依赖
  · 桥接层做"已编码检测"，防止 T7 检测到的双重编码
  · url_encoder 不可用时返回 None，让主逻辑 fallback
"""
from __future__ import annotations
from typing import Optional
from urllib.parse import unquote


def try_encode(rel: str, safe: str = "/") -> Optional[str]:
    """幂等 URL 编码：先 unquote 归一化，再编码。

    输入 "a b(c).jpg"        → "a%20b%28c%29.jpg"
    再喂给本函数             → "a%20b%28c%29.jpg"（不再双重编码）
    输入 "a%20b%28c%29.jpg"  → "a%20b%28c%29.jpg"（幂等）
    """
    if rel is None:
        return None
    try:
        from backend.rag.plugins.url_encoder import encode_path
        normalized = unquote(rel)
        return encode_path(normalized, safe=safe)
    except Exception:
        return None


def is_encoded(s: str) -> bool:
    """快速判断字符串是否含有效的 %XX 转义（用于上层门控）。"""
    if not isinstance(s, str):
        return False
    i = 0
    while i < len(s) - 2:
        if s[i] == "%":
            h = s[i + 1:i + 3]
            if all(c in "0123456789abcdefABCDEF" for c in h):
                return True
        i += 1
    return False
