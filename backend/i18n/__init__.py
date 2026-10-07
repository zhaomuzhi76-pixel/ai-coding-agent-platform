"""i18n layer: locale + catalog + translator + detector.

复用冻结层：无（本层自足）。
新增本层只做：翻译数据 + 查找 + 渲染 + 请求侧 locale 识别。
"""
from backend.i18n.locale import (
    Locale, ZH_CN, EN_US, SUPPORTED, DEFAULT_LOCALE,
    normalize, pick_best,
)
from backend.i18n.message import Message
from backend.i18n.catalog import MessageCatalog
from backend.i18n.translator import Translator
from backend.i18n.detector import (
    detect, detect_from_headers, detect_from_query,
)
from backend.i18n.builtin import load_builtin


def build_default_translator(
    default_locale: str = DEFAULT_LOCALE,
) -> Translator:
    """One-liner: build a translator loaded with builtin messages."""
    catalog = MessageCatalog()
    load_builtin(catalog)
    return Translator(catalog, default_locale=default_locale)


__all__ = [
    "Locale", "ZH_CN", "EN_US", "SUPPORTED", "DEFAULT_LOCALE",
    "normalize", "pick_best",
    "Message", "MessageCatalog", "Translator",
    "detect", "detect_from_headers", "detect_from_query",
    "load_builtin", "build_default_translator",
]
