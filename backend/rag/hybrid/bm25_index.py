"""BM25 关键词索引（纯 Python，无外部依赖）。
中文：unigram + bigram 混合；英文/数字：空格与标点切分。
职责：内存倒排索引 + BM25 打分 + where 过滤。线程安全。
不做向量、不做融合（fusion 管）、不做持久化。"""
from __future__ import annotations
import math
import re
from collections import Counter
from threading import RLock
from typing import Any, Iterable, Mapping, Optional

DEFAULT_K1 = 1.5
DEFAULT_B = 0.75

# 英文数字词
_WORD_RE = re.compile(r"[a-zA-Z0-9]+")
# 中文
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

def tokenize(text: str) -> list:
    """中英混合分词：英文单词 + 中文单字 + 中文双字。"""
    if not text:
        return []
    out: list = []
    words = _WORD_RE.findall(text.lower())
    out.extend(words)
    cjk_chars = _CJK_RE.findall(text)
    out.extend(cjk_chars)
    for i in range(len(cjk_chars) - 1):
        out.append(cjk_chars[i] + cjk_chars[i + 1])
    return out


class BM25Index:
    """内存 BM25。适合万~十万级。"""

    def __init__(self, *, k1: float = DEFAULT_K1,
                 b: float = DEFAULT_B) -> None:
        if k1 <= 0: raise ValueError("k1 must be > 0")
        if b < 0 or b > 1: raise ValueError("b must be 0..1")
        self._k1 = k1
        self._b = b
        self._docs: dict[str, dict] = {}       # id -> {tokens, text, meta, len}
        self._df: Counter = Counter()          # token -> 出现它的文档数
        self._avgdl: float = 0.0
        self._lock = RLock()

    # ---------- 写入 ----------
    def add(self, chunk_id: str, text: str, *,
            metadata: Optional[Mapping[str, Any]] = None) -> None:
        if not chunk_id:
            raise ValueError("chunk_id required")
        toks = tokenize(text or "")
        with self._lock:
            if chunk_id in self._docs:
                self._remove_locked(chunk_id)
            self._docs[chunk_id] = {
                "tokens": Counter(toks),
                "text": text or "",
                "meta": dict(metadata or {}),
                "len": len(toks),
            }
            for t in set(toks):
                self._df[t] += 1
            self._recalc_avgdl()

    def add_many(self, items: Iterable) -> int:
        """items: [{"chunk_id":..., "text":..., "metadata":...}, ...]"""
        n = 0
        for it in items:
            self.add(str(it["chunk_id"]), str(it.get("text", "")),
                     metadata=it.get("metadata"))
            n += 1
        return n

    def remove(self, chunk_id: str) -> bool:
        with self._lock:
            if chunk_id not in self._docs:
                return False
            self._remove_locked(chunk_id)
            self._recalc_avgdl()
            return True

    def clear(self) -> None:
        with self._lock:
            self._docs.clear(); self._df.clear(); self._avgdl = 0.0

    def count(self) -> int:
        with self._lock:
            return len(self._docs)

    # ---------- 查询 ----------
    def search(self, query: str, *, top_k: int = 10,
               where: Optional[Mapping[str, Any]] = None) -> list:
        """返回 [(chunk_id, score, text, meta), ...] 按 score 降序。"""
        if top_k <= 0:
            raise ValueError("top_k must be > 0")
        q_tokens = tokenize(query or "")
        if not q_tokens:
            return []
        with self._lock:
            n = len(self._docs)
            if n == 0:
                return []
            scores: list = []
            for cid, d in self._docs.items():
                if where and not _match_where(d["meta"], where):
                    continue
                s = self._score(q_tokens, d)
                if s > 0:
                    scores.append((cid, s, d["text"], dict(d["meta"])))
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]

    def _score(self, q_tokens: list, d: dict) -> float:
        dl = d["len"] or 1
        k1, b, avgdl = self._k1, self._b, (self._avgdl or 1.0)
        n = len(self._docs)
        score = 0.0
        tf = d["tokens"]
        for t in q_tokens:
            f = tf.get(t, 0)
            if f == 0:
                continue
            df = self._df.get(t, 0)
            idf = math.log(1.0 + (n - df + 0.5) / (df + 0.5))
            score += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avgdl))
        return score

    # ---------- 内部 ----------
    def _remove_locked(self, chunk_id: str) -> None:
        d = self._docs.pop(chunk_id)
        for t in set(d["tokens"].keys()):
            self._df[t] -= 1
            if self._df[t] <= 0:
                self._df.pop(t, None)

    def _recalc_avgdl(self) -> None:
        if not self._docs:
            self._avgdl = 0.0
            return
        total = sum(d["len"] for d in self._docs.values())
        self._avgdl = total / len(self._docs)


def _match_where(meta: Mapping[str, Any],
                 where: Mapping[str, Any]) -> bool:
    for k, v in where.items():
        if meta.get(k) != v:
            return False
    return True


def make_bm25_index(*, k1: float = DEFAULT_K1,
                    b: float = DEFAULT_B) -> BM25Index:
    return BM25Index(k1=k1, b=b)


__all__ = ["BM25Index", "make_bm25_index", "tokenize",
           "DEFAULT_K1", "DEFAULT_B"]
