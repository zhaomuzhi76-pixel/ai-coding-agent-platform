from __future__ import annotations

import re


# 匹配：
#   - 多级路径: avatars/audio_features
#   - 单级目录: server
#   - 单文件名: app.py
# 排除纯动词、纯中文、纯数字
_PATH_TOKEN = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"([A-Za-z_][A-Za-z0-9_\-]*"
    r"(?:/[A-Za-z0-9_][A-Za-z0-9_.\-]*)*"
    r"(?:\.[A-Za-z0-9]+)?)"
    r"(?![A-Za-z0-9_])"
)
_EXT_TOKEN = re.compile(
    r"\.(py|js|ts|tsx|jsx|java|go|rs|rb|php|cs|cpp|c|h|hpp|md|txt|json|yaml|yml)"
)


class PathPatternExtractor:
    """
    Extract a glob pattern from a raw user message.

    Used to correct LLM-classified `edit_multiple_files` patterns.
    Pure regex, no LLM — deterministic and fast.
    """

    VERSION = "1.0"
    RESPONSIBILITY = ("path_pattern_extraction",)

    def extract(self, message: str) -> str | None:
        if not isinstance(message, str) or not message.strip():
            return None

        text = message.strip()

        path = self._extract_path(text)
        exts = self._extract_extensions(text)

        if not path and not exts:
            return None

        if not exts:
            exts = ["py"]

        # 单文件名（含扩展名）→ 直接返回
        if path and "/" not in path and re.fullmatch(
            r"[A-Za-z0-9_\-]+\.[A-Za-z0-9]+", path
        ):
            return path

        if path:
            if len(exts) == 1:
                return f"{path}/**/*.{exts[0]}"
            joined = ",".join(exts)
            return f"{path}/**/*.{{{joined}}}"

        if len(exts) == 1:
            return f"**/*.{exts[0]}"
        joined = ",".join(exts)
        return f"**/*.{{{joined}}}"

    @staticmethod
    def _extract_path(text: str) -> str | None:
        _IGNORE = {
            "the", "and", "for", "with", "from",
            "a", "an", "to", "of", "in", "on",
            "所有", "全部", "这个", "那个",
        }

        for match in _PATH_TOKEN.finditer(text):
            raw = match.group(1).replace("\\", "/").strip("/")
            if not raw or raw == "." or raw in _IGNORE:
                continue
            # 若只有 1 个字符且不含 / 和 .，跳过（避免匹配 "a")
            if "/" not in raw and "." not in raw and len(raw) < 2:
                continue
            # 去掉尾部的文件扩展名（如果后面用 pattern 拼接会重复）
            if "/" not in raw and re.fullmatch(r"[A-Za-z0-9_\-]+\.[A-Za-z0-9]+", raw):
                # 单文件名：直接返回（不当作目录）
                return raw
            # 目录名：去掉尾部 .ext
            return re.sub(r"\.[A-Za-z0-9]+$", "", raw)

        return None

    @staticmethod
    def _extract_extensions(text: str) -> list[str]:
        found: list[str] = []
        for match in _EXT_TOKEN.finditer(text):
            ext = match.group(1).lower()
            if ext not in found:
                found.append(ext)
        return found

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = ["PathPatternExtractor"]
