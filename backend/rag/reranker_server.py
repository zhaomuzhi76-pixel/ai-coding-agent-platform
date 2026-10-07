"""Reranker HTTP server（llama.cpp GPU · 9033）。

POST /rerank {"query": str, "documents": [str], "top_k": int}
GET  /health
"""
from backend.config.constants.endpoints import (
    RERANKER_PORT,
)

import os
import sys

MODEL = os.environ.get(
    "RERANKER_MODEL",
    os.path.expanduser(
        "~/.biancheng/models/reranker/Qwen3-Reranker-4B.Q5_K_M.gguf"
    ),
)
PORT = int(os.environ.get("RERANKER_PORT", str(RERANKER_PORT)))
HOST = os.environ.get("RERANKER_HOST", "127.0.0.1")
GPU = int(os.environ.get("RERANKER_N_GPU", "999"))
CTX = int(os.environ.get("RERANKER_N_CTX", "4096"))

_llm = None


def _load():
    global _llm
    if _llm is not None:
        return _llm
    if not os.path.isfile(MODEL):
        raise FileNotFoundError(MODEL)
    from llama_cpp import Llama
    print(f"[reranker] loading {MODEL}", flush=True)
    _llm = Llama(
        model_path=MODEL,
        n_gpu_layers=GPU,
        n_ctx=CTX,
        logits_all=True,
        n_batch=512,
        flash_attn=True,
        verbose=False,
    )
    print("[reranker] loaded", flush=True)
    return _llm


def _tpl(query: str, doc: str) -> str:
    """Qwen3-Reranker 官方 prompt 模板。"""
    instr = "Given a web search query, retrieve relevant passages that answer the query"
    return (
        "<|im_start|>system\n"
        "Judge whether the Document meets the requirements based on the "
        "Query and the Instruct provided. Note that the answer can only be "
        '\"yes\" or \"no\".<|im_end|>\n'
        "<|im_start|>user\n"
        f"<Instruct>: {instr}\n\n"
        f"<Query>: {query}\n\n"
        f"<Document>: {doc}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )


import math as _math

_YES_ID = 9693   # "yes"
_NO_ID = 902     # " no"


def rerank(query: str, docs: list, top_k: int = 5) -> dict:
    llm = _load()
    if not docs:
        return {"results": []}
    scored = []
    for i, d in enumerate(docs):
        try:
            prompt = _tpl(query, d)
            toks = llm.tokenize(prompt.encode("utf-8"), add_bos=True)
            llm.reset()
            llm.eval(toks)
            # 最后一 token 的 logits（scores 是 (n_ctx, vocab)）
            last = llm.scores[len(toks) - 1]
            y = float(last[_YES_ID])
            n = float(last[_NO_ID])
            m = max(y, n)
            ey = _math.exp(y - m)
            en = _math.exp(n - m)
            s = ey / (ey + en)
        except Exception as exc:
            print(f"[rerank] doc{i} fail: {exc}", flush=True)
            s = 0.0
        scored.append({"index": i, "score": s, "document": d})
    scored.sort(key=lambda x: -x["score"])
    return {"results": scored[:top_k] if top_k > 0 else scored}


def main() -> None:
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI(title="Reranker", version="1.2")

    @app.get("/health")
    def h():
        try:
            _load()
            return {"ok": True, "model": MODEL, "ready": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    @app.post("/rerank")
    def r(payload: dict):
        query = str(payload.get("query", ""))
        docs = list(payload.get("documents", []) or [])
        top_k = int(payload.get("top_k", 5) or 5)
        return rerank(query, docs, top_k)

    @app.post("/unload")
    def unload():
        """卸载模型，释放 GPU 显存。下次请求自动重新加载。"""
        global _llm
        if _llm is None:
            return {"ok": True, "message": "already unloaded"}
        try:
            del _llm
        except Exception:
            pass
        _llm = None
        import gc
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        print("[reranker] unloaded (显存已释放)", flush=True)
        return {"ok": True, "message": "unloaded"}

    print(f"[reranker] serving on {HOST}:{PORT}", flush=True)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    main()
