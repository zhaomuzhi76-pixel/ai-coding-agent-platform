"""L23 独立 reranker 加载器 —— 扫描本地 gguf，按需加载，缓存实例。

与 backend/rag/reranker_server.py（9033 HTTP 服务）是独立路径。
不重复职责：仅加载 + 推理，不做 HTTP，不做 UI。
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import math
import os
import threading
from pathlib import Path
from typing import Optional

DEFAULT_SEARCH_DIRS = (
    "~/.biancheng/models/reranker",
    "~/.biancheng/models",
)
_INSTR = "Given a web search query, retrieve relevant passages that answer the query"


class RerankerLoader:
    VERSION = "1.0"

    def __init__(self, search_dirs: Optional[tuple[str, ...]] = None) -> None:
        self._dirs = tuple(
            Path(os.path.expanduser(d))
            for d in (search_dirs or DEFAULT_SEARCH_DIRS)
        )
        self._lock = threading.RLock()
        self._models: dict[str, dict] = {}
        self._scan()

    def _scan(self) -> None:
        with self._lock:
            found: dict[str, dict] = {}
            for d in self._dirs:
                if not d.is_dir():
                    continue
                for f in sorted(d.glob("*.gguf")):
                    mid = f.stem
                    if mid in found:
                        continue
                    try:
                        size_mb = round(f.stat().st_size / 1e6, 1)
                    except OSError:
                        continue
                    found[mid] = {
                        "model_id": mid,
                        "label": f"{mid}（{size_mb:.0f}MB）",
                        "backend_kind": "gguf",
                        "path": str(f),
                        "size_mb": size_mb,
                        "_llm": None,
                        "_error": "",
                    }
            self._models = found

    def list_models(self) -> list[dict]:
        with self._lock:
            return [
                {k: v for k, v in m.items() if not k.startswith("_")}
                for m in self._models.values()
            ]

    def has(self, model_id: str) -> bool:
        with self._lock:
            return model_id in self._models

    def rerank(self, model_id: str, query: str,
               docs: list[str]) -> list[float]:
        if not docs:
            return []
        llm = self._get_llm(model_id)
        if llm is None:
            return [0.0] * len(docs)
        scores: list[float] = []
        for doc in docs:
            try:
                out = llm(_tpl(query, doc), max_tokens=1,
                          logprobs=2, echo=False)
                scores.append(_yes_prob(out))
            except Exception:
                scores.append(0.0)
        return scores

    def _get_llm(self, model_id: str):
        with self._lock:
            entry = self._models.get(model_id)
            if entry is None:
                return None
            if entry["_llm"] is not None:
                return entry["_llm"]
            if entry["_error"]:
                return None
            try:
                from llama_cpp import Llama
                print(f"[l23-reranker] loading {entry['path']}", flush=True)
                llm = Llama(
                    model_path=entry["path"],
                    n_gpu_layers=int(os.environ.get("RERANKER_N_GPU", "999")),
                    n_ctx=int(os.environ.get("RERANKER_N_CTX", "2048")),
                    n_threads=int(os.environ.get("RERANKER_N_THREADS",
                                                 str(os.cpu_count() or 4))),
                    logits_all=True, n_batch=512,
                    flash_attn=True, verbose=False,
                )
                entry["_llm"] = llm
                print("[l23-reranker] loaded", flush=True)
                # 预热一次（跳过首次冷启动）
                try:
                    llm(_tpl("warmup", "warmup doc"),
                        max_tokens=1, logprobs=1, echo=False)
                    print("[l23-reranker] warmed up", flush=True)
                except Exception as e:
                    swallow("rag.ingest.review.review.reranker_loader:116", e)
                return llm
            except Exception as e:
                entry["_error"] = f"{type(e).__name__}: {e}"
                print(f"[l23-reranker] load failed: {entry['_error']}",
                      flush=True)
                return None


def _tpl(query: str, doc: str) -> str:
    """Qwen3-Reranker 官方 prompt 模板 + 预填空 think 块关闭思考。"""
    return (
        "<|im_start|>system\n"
        "Judge whether the Document meets the requirements based on the "
        "Query and the Instruct provided. Note that the answer can only be "
        '\"yes\" or \"no\".<|im_end|>\n'
        "<|im_start|>user\n"
        f"<Instruct>: {_INSTR}\n\n"
        f"<Query>: {query}\n\n"
        f"<Document>: {doc}<|im_end|>\n"
        "<|im_start|>assistant\n"
        "<think>\n\n</think>\n\n"
    )


def _yes_prob(out: dict) -> float:
    """从 llama_cpp 输出解析 p(yes)。兼容多种 logprobs 结构 + token 变体。"""
    try:
        top = out["choices"][0]["logprobs"]["top_logprobs"][0] or {}
    except (KeyError, IndexError, TypeError):
        return 0.0
    # 兼容 [dict] 和 dict 两种结构
    items = top.items() if isinstance(top, dict) else enumerate(top)
    p_yes = p_no = 0.0
    for tok, lp in items:
        k = str(tok).strip().lower()
        if not k:
            continue
        try:
            p = math.exp(float(lp))
        except (TypeError, ValueError):
            continue
        # 子串匹配：处理 "yes" / " Yes" / "yes<|im_end|>" / "yes." 等
        if "yes" in k or k in ("y", "是", "yes"):
            p_yes += p
        elif "no" in k or k in ("n", "否", "no"):
            p_no += p
    total = p_yes + p_no
    return 0.0 if total <= 0 else p_yes / total


_default: Optional[RerankerLoader] = None
_lock = threading.Lock()


def get_default_loader() -> RerankerLoader:
    global _default
    with _lock:
        if _default is None:
            _default = RerankerLoader()
        return _default
