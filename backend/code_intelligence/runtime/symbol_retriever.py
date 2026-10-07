from __future__ import annotations

import re
from typing import Any


class SymbolRetriever:
    """
    Retrieve candidate files from the code index by matching
    identifiers/keywords extracted from the user prompt.

    Pure keyword heuristic — no LLM, no embedding, deterministic.
    Index (symbols + imports) is provided by CodeIndexService.

    Responsibility:
        - tokenize prompt into candidate identifiers
        - score each index entry (path/symbols/imports)
        - return top-K files sorted by relevance

    Not Responsible:
        - index construction
        - graph expansion
        - code modification
    """

    VERSION = "1.0"

    # 排除通用词，避免命中无关文件
    STOPWORDS = frozenset({
        # 英文通用
        "the", "and", "for", "with", "from", "this", "that",
        "all", "any", "new", "old", "are", "was", "were",
        "has", "have", "had", "will", "would", "can", "could",
        "should", "into", "onto", "over", "under", "out",
        # 动作词（任务意图，不是符号）
        "add", "insert", "append", "delete", "remove",
        "replace", "change", "modify", "update", "edit",
        "create", "make", "build", "generate",
        # 通用名词
        "file", "files", "code", "line", "lines",
        "function", "functions", "method", "class", "classes",
        "module", "modules", "comment", "header", "license",
        "copyright", "top", "bottom", "end", "start",
        # Python 关键字
        "import", "from", "def", "class", "self", "return",
        "true", "false", "none", "print", "yield",
    })

    MIN_TOKEN_LEN = 3
    MAX_FILES = 20

    def retrieve(
        self,
        *,
        prompt: str,
        index: list[dict[str, Any]],
        max_files: int | None = None,
    ) -> dict[str, Any]:
        if not isinstance(prompt, str) or not prompt.strip():
            return {"tokens": [], "files": [], "matches": []}

        if not isinstance(index, list) or not index:
            return {"tokens": [], "files": [], "matches": []}

        limit = max_files or self.MAX_FILES
        tokens = self._extract_tokens(prompt)
        if not tokens:
            return {"tokens": [], "files": [], "matches": []}

        scored = self._score(index, tokens)
        top = scored[:limit]

        return {
            "tokens": tokens,
            "files": [item["path"] for item, _ in top],
            "matches": [
                {"path": item["path"], "score": score}
                for item, score in top
            ],
        }

    def _extract_tokens(self, prompt: str) -> list[str]:
        raw = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", prompt)
        seen: set[str] = set()
        out: list[str] = []
        for token in raw:
            low = token.lower()
            if len(token) < self.MIN_TOKEN_LEN:
                continue
            if low in self.STOPWORDS:
                continue
            if low in seen:
                continue
            seen.add(low)
            out.append(token)
        return out

    @staticmethod
    def _score(
        index: list[dict[str, Any]],
        tokens: list[str],
    ) -> list[tuple[dict[str, Any], int]]:
        results: list[tuple[dict[str, Any], int]] = []
        for item in index:
            path = str(item.get("path", ""))
            symbols = [str(s) for s in item.get("symbols", [])]
            imports = [str(i) for i in item.get("imports", [])]

            symbols_lower = [s.lower() for s in symbols]
            imports_lower = [i.lower() for i in imports]
            path_lower = path.lower()

            score = 0
            for token in tokens:
                tl = token.lower()
                if token in symbols:
                    score += 10  # 精确符号命中
                elif tl in symbols_lower:
                    score += 8   # 大小写无关命中
                elif tl in path_lower:
                    score += 3   # 路径命中（如 login.py）
                elif tl in imports_lower:
                    score += 2   # import 命中
                elif any(tl in s for s in symbols_lower):
                    score += 1   # 部分符号命中

            if score > 0:
                results.append((item, score))

        results.sort(key=lambda x: -x[1])
        return results

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "max_files": self.MAX_FILES,
            "stopwords_count": len(self.STOPWORDS),
        }


__all__ = ["SymbolRetriever"]
