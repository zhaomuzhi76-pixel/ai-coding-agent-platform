"""手动向量化已有草稿（绕过 FastAPI 阻塞）。
用法: python scripts/manual_approve_draft.py <job_id>
"""
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, "/home/computer01/xiangmu02/biancheng_aiagentpro")

JOB = sys.argv[1] if len(sys.argv) > 1 else "job-8372f4f24ab24d5a"
DRAFT = Path.home() / ".cache" / "agent_knowledge" / "drafts" / f"{JOB}.jsonl"

if not DRAFT.exists():
    sys.exit(f"❌ 草稿不存在: {DRAFT}")

print(f"📖 读取草稿: {DRAFT}")
chunks = []
with open(DRAFT, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            chunks.append(json.loads(line))
print(f"✅ 共 {len(chunks)} 条 chunks")

# 分批 embed
from backend.api.rag.ingest_runtime import get_ingest_runtime
rt = get_ingest_runtime()
ef = rt.embed_fn
print(f"✅ embed_fn: {type(ef).__name__}")

BATCH = int(os.environ.get("RAG_EMBED_BATCH", "8"))
texts = [c.get("text", "") for c in chunks]
ids = [c.get("chunk_id", f"{JOB}_chunk_{i}") for i, c in enumerate(chunks)]
metas = [dict(c.get("metadata") or {}) for c in chunks]

all_embs = []
n_batches = (len(texts) + BATCH - 1) // BATCH
t_all = time.time()

for i in range(0, len(texts), BATCH):
    batch = texts[i:i + BATCH]
    t0 = time.time()
    try:
        embs = ef(batch)
    except Exception as e:
        print(f"❌ 批次 {i//BATCH+1} 失败: {e!r}")
        sys.exit(1)
    all_embs.extend(embs)
    dt = time.time() - t0
    done = i + len(batch)
    print(f"  [{i//BATCH+1}/{n_batches}] {done}/{len(texts)} 条  ({dt:.2f}s)")

print(f"✅ embedding 全部完成（{time.time()-t_all:.1f}s）")

# 写向量库
from backend.storage.vector_backend import get_vector_store
from backend.storage.vector_config import VectorConfig
vs = get_vector_store(VectorConfig())

print(f"📦 写入向量库...")
try:
    vs.add_documents(documents=texts, ids=ids, metadata=metas, embeddings=all_embs)
except TypeError:
    # Lite 的 add_documents 签名可能是 (documents, ids, metadata, embeddings)
    vs.add_documents(documents=texts, ids=ids, metadata=metas, embeddings=all_embs)
print(f"✅ 向量库 count = {vs.count()}")

# 更新 job 状态为 done
try:
    from backend.api.rag.ingest_runtime import get_worker
    from backend.rag.ingest.jobs.registry import JobStatus
    w = get_worker()
    w.registry.finish(JOB, status=JobStatus.DONE, chunks_indexed=len(chunks), error="")
    print(f"✅ job 状态更新为 done")
except Exception as e:
    print(f"⚠ 更新 job 状态失败（不影响向量数据）: {e!r}")

print()
print("═" * 50)
print(f"🎉 完成! {len(chunks)} 条 chunk 已向量化入库")
print("═" * 50)
