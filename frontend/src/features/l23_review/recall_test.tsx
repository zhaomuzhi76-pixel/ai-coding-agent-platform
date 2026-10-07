/** 重排序召回可视化 —— Dify 风格。 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  l23RecallApi, l23RecallConfigApi,
  type RecallHit, type RecallModelsResp, type RecallQueryResp,
} from "../../core/api/l23_review_api"
import "./l23_review.css"

export function RecallTest() {
  const [q, setQ] = useState("太阳病")
  const [topK, setTopK] = useState(10)
  const [useRerank, setUseRerank] = useState(true)
  const [modelId, setModelId] = useState("builtin-qwen3-reranker")
  const [rrfK, setRrfK] = useState(60)
  const [vW, setVW] = useState(0.7)
  const [bW, setBW] = useState(0.3)
  const [showParams, setShowParams] = useState(true)
  const [models, setModels] = useState<RecallModelsResp | null>(null)
  const [resp, setResp] = useState<RecallQueryResp | null>(null)
  const [busy, setBusy] = useState(false)
  const [applied, setApplied] = useState<number | null>(null)
  const [savedAt, setSavedAt] = useState<string>("")
  const timer = useRef<number | null>(null)

  useEffect(() => { void l23RecallApi.models().then(setModels).catch(() => {}) }, [])

  useEffect(() => {
    void l23RecallConfigApi.get().then((r) => {
      setTopK(r.config.top_k)
      setUseRerank(r.config.use_reranker)
      setModelId(r.config.reranker_model_id)
      setRrfK(r.config.rrf_k)
      setVW(r.config.vector_weight)
      setBW(r.config.bm25_weight)
      setApplied(r.version)
      setSavedAt("")
    }).catch(() => {})
  }, [])


  const run = useCallback(async () => {
    if (!q.trim()) return
    setBusy(true)
    try {
      const r = await l23RecallApi.query({
        query: q.trim(), top_k: topK, use_reranker: useRerank,
        reranker_model_id: modelId, rrf_k: rrfK,
        vector_weight: vW, bm25_weight: bW,
      })
      setResp(r)
    } catch (e) { console.error(e); setResp(null) } finally { setBusy(false) }
  }, [q, topK, useRerank, modelId, rrfK, vW, bW])

  // Dify 模式：参数即改即应用
  useEffect(() => {
    if (timer.current) window.clearTimeout(timer.current)
    timer.current = window.setTimeout(async () => {
      try {
        await l23RecallConfigApi.apply({
          top_k: topK, use_reranker: useRerank,
          reranker_model_id: modelId, rrf_k: rrfK,
          vector_weight: vW, bm25_weight: bW,
        })
        setSavedAt("已生效")
      } catch {}
      void run()
    }, 600)
    return () => { if (timer.current) window.clearTimeout(timer.current) }
  }, [run, topK, useRerank, modelId, rrfK, vW, bW])

  return (
    <section className="l23-panel">
      <div className="l23-panel__head">
        <div>
          <div className="l23-panel__title">重排序召回可视化</div>
          <div className="l23-panel__sub">BM25 · 向量 · Reranker 三路分数实时对比</div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {savedAt && <span style={{ fontSize: 11, opacity: .7, color: "#78cc96" }}>● {savedAt}</span>}
          <button className="ind-btn" onClick={() => setShowParams(v => !v)}>
            {showParams ? "隐藏参数" : "⚙ 参数"}
          </button>
        </div>
      </div>

      <div className="l23-search">
        <span className="l23-search__icon">🔍</span>
        <input className="l23-search__input"
          placeholder="输入查询…（400ms 自动执行）"
          value={q} onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") void run() }} />
        {resp && (
          <span className="l23-search__meta">
            {resp.counts.returned} 条 · {resp.elapsed_ms}ms · {resp.reranked ? "已精排" : "未精排"}
          </span>
        )}
        <button className="ind-btn" disabled={busy} onClick={() => void run()}>
          {busy ? "…" : "测试"}
        </button>
      </div>

      {showParams && (
        <div className="l23-params">
          <label>Top-K <input type="number" min={1} max={50} value={topK}
            onChange={(e) => setTopK(Number(e.target.value) || 10)} /></label>
          <label><input type="checkbox" checked={useRerank}
            onChange={(e) => setUseRerank(e.target.checked)} /> Reranker</label>
          <label>排序模型
            <select value={modelId} onChange={(e) => setModelId(e.target.value)}>
              {(models?.models ?? []).map((m) => (
                <option key={m.model_id} value={m.model_id}>{m.label}</option>
              ))}
            </select>
          </label>
          <label>RRF k <input type="number" min={1} max={200} value={rrfK}
            onChange={(e) => setRrfK(Number(e.target.value) || 60)} /></label>
          <label>向量 {vW.toFixed(2)}
            <input type="range" min={0} max={1} step={0.05} value={vW}
              onChange={(e) => setVW(Number(e.target.value))} /></label>
          <label>BM25 {bW.toFixed(2)}
            <input type="range" min={0} max={1} step={0.05} value={bW}
              onChange={(e) => setBW(Number(e.target.value))} /></label>
        </div>
      )}

      {resp?.errors && (resp.errors.vector || resp.errors.bm25) && (
        <div className="l23-error">
          {resp.errors.vector && <div>向量路: {resp.errors.vector}</div>}
          {resp.errors.bm25 && <div>BM25 路: {resp.errors.bm25}</div>}
        </div>
      )}

      {resp && resp.hits.length > 0 && (
        <div className="l23-chunks">
          {resp.hits.map((h) => <HitCard key={h.chunk_id} hit={h} query={q} />)}
        </div>
      )}

      {resp && resp.hits.length === 0 && (
        <div className="l23-empty">无命中</div>
      )}
    </section>
  )
}

function HitCard({ hit, query }: { hit: RecallHit; query: string }) {
  const html = useMemo(() => hl(hit.content, query), [hit.content, query])
  return (
    <div className="l23-chunk">
      <div className="l23-chunk__head">
        <span className="l23-chunk__id">{hit.chunk_id.slice(0, 12)}</span>
        <div className="l23-chunk__badges">
          <span className="l23-rank l23-rank--hit">#{hit.fused_rank}</span>
          <span className="l23-score">RRF {hit.fused.toFixed(4)}</span>
          {hit.source && <span className="l23-score">{hit.source}</span>}
        </div>
      </div>
      <div className="l23-chunk__content"
           dangerouslySetInnerHTML={{ __html: html }} />
      <div className="l23-bars l23-bars--triple">
        <Bar label={`BM25 ${hit.bm25.toFixed(2)}`} pct={hit.bm25_bar} kind="bm25" />
        <Bar label={`向量 ${hit.vector.toFixed(4)}`} pct={hit.vector_bar} kind="vector" />
        <Bar label={`Rerank ${hit.rerank.toFixed(4)}`} pct={hit.rerank_bar} kind="rerank" />
      </div>
    </div>
  )
}

function Bar({ label, pct, kind }: { label: string; pct: number; kind: "bm25" | "vector" | "rerank" }) {
  const w = Math.max(0, Math.min(100, pct * 100))
  return (
    <div className="l23-bar">
      <div className="l23-bar__label"><span>{label}</span><span>{w.toFixed(0)}%</span></div>
      <div className="l23-bar__track">
        <div className={`l23-bar__fill l23-bar__fill--${kind}`} style={{ width: `${w}%` }} />
      </div>
    </div>
  )
}

function hl(text: string, query: string): string {
  const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  const safe = esc(text)
  const terms = query.split(/\s+/).map(t => t.trim()).filter(t => t.length >= 2)
  if (terms.length === 0) return safe
  let out = safe
  for (const t of terms) {
    const re = new RegExp(`(${t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi")
    out = out.replace(re, "<mark>$1</mark>")
  }
  return out
}
