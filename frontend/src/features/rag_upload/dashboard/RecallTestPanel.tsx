/** 召回测试：数据源多选 + 命中筛选 + 保存到 AI 可用数据 */
import { useCallback, useEffect, useMemo, useState } from "react"

// [NATURAL] 中文拼音 + 数字自然序（"辞2" < "辞10"）
const _collator = new Intl.Collator("zh-Hans-CN", {
  numeric: true, sensitivity: "base",
})
import { Badge, EmptyState } from "../../../app/ui/industrial"

interface Hit {
  chunk_id: string
  score?: number
  rerank_score?: number
  text?: string
  doc_title?: string
  source?: string
  page?: number
  curated?: boolean
}
interface SourceItem {
  key?: string
  title: string
  chunks: number
  chunk_ids?: string[]
  match_values?: string[]
}

export function RecallTestPanel() {
  const [sources, setSources] = useState<SourceItem[]>([])
  const [selectedSources, setSelectedSources] = useState<Set<string>>(new Set())
  const [query, setQuery] = useState("")
  const [topK, setTopK] = useState(5)
  const [useRerank, setUseRerank] = useState(true)
  const [hits, setHits] = useState<Hit[]>([])
  const [keepSet, setKeepSet] = useState<Set<string>>(new Set())
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState("")
  const [elapsed, setElapsed] = useState(0)
  const [sortBy, setSortBy] = useState<"chunks" | "pages" | "title">("chunks")
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc")

  const loadSources = useCallback(async () => {
    try {
      const r = await fetch("/api/rag/vectors/sources")
      const d = await r.json()
      setSources(d.sources ?? [])
    } catch { /* ignore */ }
  }, [])
  useEffect(() => { void loadSources() }, [loadSources])

  // [SORT] 数据源排序
  const sortedSources = useMemo(() => {
    const arr = [...sources]
    arr.sort((a, b) => {
      let va: number | string = 0
      let vb: number | string = 0
      if (sortBy === "chunks") { va = a.chunks; vb = b.chunks }
      else if (sortBy === "pages") {
        va = 0; vb = 0  // SourceItem 无 page_max，退化为无差异
      } else { va = a.title; vb = b.title }
      let cmp = 0
      if (typeof va === "string" && typeof vb === "string") {
        cmp = _collator.compare(va, vb)
      } else {
        cmp = (va as number) - (vb as number)
      }
      return sortDir === "asc" ? cmp : -cmp
    })
    return arr
  }, [sources, sortBy, sortDir])

  const toggleSource = (title: string) => {
    setSelectedSources((prev) => {
      const n = new Set(prev)
      if (n.has(title)) n.delete(title); else n.add(title)
      return n
    })
  }
  const selectAllSources = () => {
    setSelectedSources(new Set(sources.map((s) => s.title)))
  }
  const clearSources = () => setSelectedSources(new Set())

  const test = async () => {
    if (!query.trim()) return
    setBusy(true); setHits([]); setMsg("")
    const t0 = performance.now()
    try {
      const r = await fetch("/api/rag/recall-filtered", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query, top_k: topK, rerank: useRerank,
          sources: Array.from(selectedSources),
          only_curated: true,
        }),
      })
      const d = await r.json()
      setElapsed(Math.round(performance.now() - t0))
      if (d.ok) {
        setHits(d.hits ?? [])
        setKeepSet(new Set((d.hits ?? []).map((h: Hit) => h.chunk_id)))
      } else setMsg(d.detail || "失败")
    } catch (e) { setMsg(String(e)) } finally { setBusy(false) }
  }

  const toggleKeep = (cid: string) => {
    setKeepSet((prev) => {
      const n = new Set(prev)
      if (n.has(cid)) n.delete(cid); else n.add(cid)
      return n
    })
  }

  const saveCuration = async () => {
    if (hits.length === 0) return
    const keep_ids = Array.from(keepSet)
    const filter_ids = hits.filter((h) => !keepSet.has(h.chunk_id))
                            .map((h) => h.chunk_id)
    setBusy(true)
    try {
      const r = await fetch("/api/rag/curate/commit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keep_ids, filter_ids }),
      })
      const d = await r.json()
      setMsg(d.ok ? `✅ 已保存：保留 ${d.kept} 条，过滤 ${d.filtered} 条`
                  : "❌ 保存失败")
    } catch (e) { setMsg(`❌ ${e}`) } finally { setBusy(false) }
  }

  return (
    <div className="ind-card" style={{ padding: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>
        召回测试 · 验证知识库命中质量
      </div>
      <div style={{ fontSize: 11, color: "var(--text-soft)", marginBottom: 12 }}>
        勾选数据源 → 输入问题 → 召回 → 逐条保留/过滤 → 保存（AI 助手只用保留的）
      </div>

      {/* 数据源多选 */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
          <span style={{ fontSize: 12, fontWeight: 500 }}>数据源</span>
          <Badge tone="info">{selectedSources.size}/{sources.length}</Badge>
          <button className="ind-btn" style={{ padding: "2px 8px", fontSize: 11 }}
                  onClick={selectAllSources}>全选</button>
          <button className="ind-btn" style={{ padding: "2px 8px", fontSize: 11 }}
                  onClick={clearSources}>清空</button>
          {/* [SORT] 排序 */}
          <select className="ind-btn"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  title="排序维度"
                  style={{ padding: "2px 6px", fontSize: 11,
                           background: "#1c1c1e", color: "#e8e8ea",
                           border: "1px solid #33333a", borderRadius: 4,
                           colorScheme: "dark", cursor: "pointer" }}>
            <option value="chunks" style={{ background: "#1c1c1e" }}>块数</option>
            <option value="title" style={{ background: "#1c1c1e" }}>名称</option>
          </select>
          <button className="ind-btn" style={{ padding: "2px 8px", fontSize: 11 }}
                  title={sortDir === "asc" ? "点击切降序" : "点击切升序"}
                  onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}>
            {sortDir === "asc" ? "↑ 升序" : "↓ 降序"}
          </button>
          <span style={{ fontSize: 11, color: "var(--text-soft)", marginLeft: 8 }}>
            空 = 全部
          </span>
        </div>
        <div style={{ maxHeight: 120, overflowY: "auto",
                      padding: 8, background: "#17171a", borderRadius: 6,
                      display: "grid", gap: 2 }}>
          {sources.length === 0 && (
            <div style={{ fontSize: 11, color: "var(--text-soft)" }}>暂无已入库文档</div>
          )}
          {sortedSources.map((s) => {
            const on = selectedSources.has(s.title)
            return (
              <div key={s.title} onClick={() => toggleSource(s.title)}
                   style={{ display: "flex", alignItems: "center", gap: 8,
                            padding: "3px 6px", cursor: "pointer",
                            borderRadius: 4, fontSize: 11,
                            background: on ? "rgba(37,99,235,.15)" : "transparent" }}>
                <input type="checkbox" checked={on} readOnly
                       style={{ pointerEvents: "none" }} />
                <span style={{ flex: 1 }}>📄 {s.title}</span>
                <span style={{ color: "var(--text-soft)" }}>{s.chunks} 块</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* 搜索框 */}
      <div className="ind-toolbar">
        <input className="ind-input" value={query}
               placeholder="输入测试问题，如：桂枝汤治什么病？"
               onChange={(e) => setQuery(e.target.value)}
               onKeyDown={(e) => e.key === "Enter" && test()} />
        <label style={{ fontSize: 12, color: "var(--text-soft)",
                        display: "flex", gap: 4, alignItems: "center" }}>
          Top-K
          <input className="ind-input" type="number" value={topK} min={1} max={20}
                 style={{ width: 60, flex: "none" }}
                 onChange={(e) => setTopK(Number(e.target.value))} />
        </label>
        <label style={{ fontSize: 12, color: "var(--text-soft)",
                        display: "flex", gap: 4, alignItems: "center" }}>
          <input type="checkbox" checked={useRerank}
                 onChange={(e) => setUseRerank(e.target.checked)} />
          启用重排序
        </label>
        <button className="ind-btn ind-btn--primary"
                disabled={busy || !query.trim()} onClick={test}>
          {busy ? "检索中…" : "召回测试"}
        </button>
      </div>

      {msg && (
        <div style={{ padding: "6px 10px", background: "rgba(79,214,154,.08)",
                      border: "1px solid rgba(79,214,154,.3)",
                      color: "#4fd69a", borderRadius: 6,
                      fontSize: 12, marginTop: 10 }}>{msg}</div>
      )}
      {elapsed > 0 && (
        <div style={{ fontSize: 11, color: "var(--text-soft)", marginTop: 6 }}>
          耗时 {elapsed}ms
        </div>
      )}

      {hits.length === 0 && !busy ? (
        <EmptyState title="输入问题后点【召回测试】"
                    hint="勾选数据源 → 输入问题 → 查看命中"
                    icon="🔍" />
      ) : (
        <>
          <div style={{ display: "flex", gap: 8, alignItems: "center",
                        marginTop: 12, marginBottom: 8 }}>
            <span style={{ fontSize: 12, fontWeight: 500 }}>命中结果</span>
            <Badge tone="info">{hits.length} 条</Badge>
            <Badge tone="success">保留 {keepSet.size}</Badge>
            <Badge tone="muted">过滤 {hits.length - keepSet.size}</Badge>
            <button className="ind-btn ind-btn--primary"
                    style={{ marginLeft: "auto" }}
                    disabled={busy || keepSet.size === hits.length
                              && hits.every((h) => h.curated !== false)}
                    onClick={saveCuration}>
              💾 保存筛选结果
            </button>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            {hits.map((h, i) => {
              const on = keepSet.has(h.chunk_id)
              return (
                <div key={h.chunk_id}
                     onClick={() => toggleKeep(h.chunk_id)}
                     style={{
                       padding: 12, borderRadius: 6, cursor: "pointer",
                       background: on ? "rgba(37,99,235,.12)" : "#17171a",
                       border: "1px solid " + (on ? "#2563eb" : "#2a2a2e"),
                     }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center",
                                marginBottom: 6, flexWrap: "wrap" }}>
                    <input type="checkbox" checked={on} readOnly
                           style={{ pointerEvents: "none" }} />
                    <Badge tone="info">#{i + 1}</Badge>
                    {h.rerank_score != null && (
                      <Badge tone="success">rerank {h.rerank_score.toFixed(3)}</Badge>
                    )}
                    {h.doc_title && (
                      <span style={{ fontSize: 11, color: "var(--text-soft)" }}>
                        📄 {h.doc_title}{h.page ? ` p.${h.page}` : ""}
                      </span>
                    )}
                    {on
                      ? <Badge tone="success">保留</Badge>
                      : <Badge tone="warning">过滤</Badge>}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-soft)",
                                lineHeight: 1.5 }}>
                    {(h.text || "").slice(0, 300)}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
export default RecallTestPanel
