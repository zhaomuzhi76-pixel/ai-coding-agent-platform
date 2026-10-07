/** 已入库文档管理：点击行选中 / 查看 / 单删 / 批删 */
import { useCallback, useEffect, useMemo, useState } from "react"
import { Badge, EmptyState } from "../../../app/ui/industrial"
import { SourceDetailDrawer } from "./SourceDetailDrawer"

// [NATURAL] 中文拼音 + 数字自然序（"中医方剂大辞典2" < "中医方剂大辞典10"）
const _collator = new Intl.Collator("zh-Hans-CN", {
  numeric: true,
  sensitivity: "base",
})

interface SourceItem {
  key?: string
  source?: string
  title: string
  kb: string
  domain: string
  chunks: number
  page_min: number | null
  page_max: number | null
  chunk_ids?: string[]
  match_values?: string[]
}

export function VectorSourcesPanel() {
  const [sources, setSources] = useState<SourceItem[]>([])
  const [total, setTotal] = useState(0)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState("")
  const [detail, setDetail] = useState<SourceItem | null>(null)
  const [sortBy, setSortBy] = useState<"chunks" | "pages" | "title">("chunks")
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc")

  // [FIX] 稳定 props：防止父组件轮询触发子组件重渲染
  const stableChunkIds = useMemo(
    () => detail?.chunk_ids ?? [], [detail?.key])
  const stableMatchValues = useMemo(
    () => detail?.match_values ?? [], [detail?.key])
  const onCloseDetail = useCallback(() => setDetail(null), [])

  const load = useCallback(async () => {
    try {
      const r = await fetch("/api/rag/vectors/sources")
      const d = await r.json()
      setSources(d.sources ?? [])
      setTotal(d.total_chunks ?? 0)
    } catch (e) { setMsg(`加载失败: ${e}`) }
  }, [])
  const onChangedDetail = useCallback(() => { void load() }, [load])

  useEffect(() => { void load() }, [load])

  // [SORT] 根据 sortBy + sortDir 排序 sources
  const sortedSources = useMemo(() => {
    const arr = [...sources]
    arr.sort((a, b) => {
      let va: number | string = 0
      let vb: number | string = 0
      if (sortBy === "chunks") { va = a.chunks; vb = b.chunks }
      else if (sortBy === "pages") {
        va = a.page_max ?? 0; vb = b.page_max ?? 0
      } else { va = a.title; vb = b.title }
      let cmp = 0
      if (typeof va === "string" && typeof vb === "string") {
        // [NATURAL] 中文拼音 + 数字自然序（1<2<10<11）
        cmp = _collator.compare(va, vb)
      } else {
        cmp = (va as number) - (vb as number)
      }
      return sortDir === "asc" ? cmp : -cmp
    })
    return arr
  }, [sources, sortBy, sortDir])

  const keyOf = (s: SourceItem) => s.key || s.title

  const toggle = (s: SourceItem) => {
    const k = keyOf(s)
    setSelected((prev) => {
      const n = new Set(prev)
      if (n.has(k)) n.delete(k); else n.add(k)
      return n
    })
  }

  const toggleAll = (v: boolean) => {
    setSelected(v ? new Set(sources.map(keyOf)) : new Set())
  }

  // 单删
  const deleteOne = async (s: SourceItem) => {
    if (!window.confirm(`删除《${s.title}》及 ${s.chunks} 块向量？不可逆`)) return
    setBusy(true)
    try {
      const r = await fetch("/api/rag/vectors/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chunk_ids: s.chunk_ids ?? [],
          match_values: s.match_values ?? [],
        }),
      })
      const d = await r.json()
      setMsg(d.ok ? `✅ 已删除 ${d.deleted} 块` : "❌ 删除失败")
      await load()
    } finally { setBusy(false); setSelected(new Set()) }
  }

  // 批删（合并所有 chunk_ids 一次调用）
  // [RENAME] 用户编辑文档名
  const renameSource = async (s: SourceItem) => {
    const newName = window.prompt("输入新的文档名（留空取消）", s.title)
    if (!newName || !newName.trim() || newName === s.title) return
    setBusy(true)
    try {
      const r = await fetch("/api/rag/vectors/source-rename", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          match_values: s.match_values ?? [],
          chunk_ids: s.chunk_ids ?? [],
          new_title: newName.trim(),
        }),
      })
      const d = await r.json()
      setMsg(d.ok ? `✅ 重命名成功（${d.updated} 块）` : "❌ 重命名失败")
      await load()
    } finally { setBusy(false) }
  }

  const deleteBatch = async () => {
    if (selected.size === 0) return
    if (!window.confirm(`删除选中的 ${selected.size} 个文档及其所有向量？`)) return
    setBusy(true)
    try {
      const allIds: string[] = []
      for (const s of sources) {
        if (selected.has(keyOf(s)) && s.chunk_ids) allIds.push(...s.chunk_ids)
      }
      const r = await fetch("/api/rag/vectors/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chunk_ids: allIds }),
      })
      const d = await r.json()
      setMsg(d.ok ? `✅ 已删除 ${d.deleted} 块` : "❌ 批量删除失败")
      await load()
    } finally { setBusy(false); setSelected(new Set()) }
  }

  return (
    <div className="ind-card" style={{ padding: 16 }}>
      {/* 工具栏 */}
      <div style={{ display: "flex", justifyContent: "space-between",
                    alignItems: "center", marginBottom: 12, gap: 10,
                    flexWrap: "wrap" }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>已入库文档</span>
          <Badge tone="info">{sources.length} 个</Badge>
          <Badge tone="success">{total} 块向量</Badge>
          {selected.size > 0 && (
            <Badge tone="warning">已选 {selected.size}</Badge>
          )}
        </div>
        <div className="ind-toolbar" style={{ margin: 0 }}>
          {/* [SORT] 排序选择器 */}
          <select className="ind-btn"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  disabled={sources.length === 0}
                  title="选择排序维度"
                  style={{
                    padding: "4px 8px", fontSize: 11,
                    background: "#1c1c1e", color: "#e8e8ea",
                    border: "1px solid #33333a", borderRadius: 6,
                    colorScheme: "dark",  // [DARK] 让原生下拉也深色
                    cursor: "pointer",
                  }}>
            <option value="chunks" style={{ background: "#1c1c1e", color: "#e8e8ea" }}>块数</option>
            <option value="pages" style={{ background: "#1c1c1e", color: "#e8e8ea" }}>页数</option>
            <option value="title" style={{ background: "#1c1c1e", color: "#e8e8ea" }}>名称</option>
          </select>
          <button className="ind-btn"
                  title={sortDir === "asc" ? "升序（点击切降序）" : "降序（点击切升序）"}
                  onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
                  disabled={sources.length === 0}
                  style={{ padding: "4px 10px", fontSize: 12 }}>
            {sortDir === "asc" ? "↑ 升序" : "↓ 降序"}
          </button>
          <button className="ind-btn" onClick={() => toggleAll(true)}
                  disabled={sources.length === 0}>全选</button>
          <button className="ind-btn" onClick={() => toggleAll(false)}
                  disabled={selected.size === 0}>取消全选</button>
          <button className="ind-btn"
                  style={{ borderColor: "#7f1d1d", color: "#fca5a5" }}
                  disabled={busy || selected.size === 0}
                  onClick={deleteBatch}>
            🗑 删除选中（{selected.size}）
          </button>
        </div>
      </div>

      {msg && (
        <div style={{ padding: "6px 10px", background: "rgba(79,214,154,.08)",
                      border: "1px solid rgba(79,214,154,.3)",
                      color: "#4fd69a", borderRadius: 6,
                      fontSize: 12, marginBottom: 10 }}>{msg}</div>
      )}

      {sources.length === 0 ? (
        <EmptyState title="向量库为空"
                    hint="上传并处理文档后，这里显示已入库的所有文档"
                    icon="📦" />
      ) : (
        <div style={{ display: "grid", gap: 4 }}>
          {sortedSources.map((s) => {
            const k = keyOf(s)
            const isSel = selected.has(k)
            return (
              <div key={k}
                   onClick={() => toggle(s)}
                   style={{
                     display: "flex", alignItems: "center", gap: 10,
                     padding: "8px 12px",
                     background: isSel ? "rgba(37,99,235,.15)" : "#17171a",
                     border: "1px solid " + (isSel ? "#2563eb" : "transparent"),
                     borderRadius: 6, fontSize: 12,
                     cursor: "pointer",
                     transition: "background .12s, border-color .12s",
                   }}>
                {/* 复选框：装饰用途，点它 = 点行 */}
                <div style={{
                  width: 16, height: 16, borderRadius: 4,
                  border: "2px solid " + (isSel ? "#2563eb" : "#4a4a52"),
                  background: isSel ? "#2563eb" : "transparent",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  flexShrink: 0, color: "#fff", fontSize: 11, fontWeight: 700,
                }}>
                  {isSel ? "✓" : ""}
                </div>

                <span style={{ flex: 1, overflow: "hidden",
                               textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  📄 {s.title}
                </span>

                {s.kb && <Badge tone="muted">{s.kb}</Badge>}

                <span style={{ color: "#9a9aa0", fontSize: 11,
                               fontFamily: "ui-monospace, monospace" }}>
                  {s.chunks} 块
                </span>

                {s.page_min != null && (
                  <span style={{ color: "#6b7280", fontSize: 11 }}>
                    p.{s.page_min}-{s.page_max}
                  </span>
                )}

                <button className="ind-btn"
                        style={{ padding: "3px 10px", fontSize: 11 }}
                        title="编辑文档名"
                        disabled={busy}
                        onClick={(e) => { e.stopPropagation(); renameSource(s) }}>
                  ✏️
                </button>
                <button className="ind-btn"
                        style={{ padding: "3px 10px", fontSize: 11 }}
                        onClick={(e) => { e.stopPropagation(); setDetail(s) }}>
                  查看
                </button>
                <button className="ind-btn"
                        style={{ padding: "3px 10px", fontSize: 11,
                                 borderColor: "#7f1d1d", color: "#fca5a5" }}
                        disabled={busy}
                        onClick={(e) => { e.stopPropagation(); deleteOne(s) }}>
                  删除
                </button>
              </div>
            )
          })}
        </div>
      )}

      {detail && (
        <SourceDetailDrawer
          open={true}
          title={detail.title}
          chunkIds={stableChunkIds}
          matchValues={stableMatchValues}
          onClose={onCloseDetail}
          onChanged={onChangedDetail}
        />
      )}
    </div>
  )
}
export default VectorSourcesPanel
