/** 分块审核面板（工业级） */
import { useEffect, useState } from "react"
import { Badge, EmptyState } from "../../../app/ui/industrial"

export interface ChunkItem {
  index: number
  text: string
  page_start: number
  page_end: number
  source: string
  accepted?: boolean
}

interface Props { jobId: string; onApproved?: () => void }

export function ChunkReviewPanel({ jobId, onApproved }: Props) {
  const [chunks, setChunks] = useState<ChunkItem[]>([])
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState("")

  useEffect(() => {
    if (jobId === "__latest__") return
    fetch(`/api/rag/ingest/jobs/${encodeURIComponent(jobId)}/draft-chunks`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => setChunks(
        (d?.chunks ?? []).map((c: ChunkItem) => ({ ...c, accepted: true }))))
      .catch(() => {})
  }, [jobId])

  const toggle = (i: number) =>
    setChunks((l) => l.map((c) => c.index === i ? { ...c, accepted: !c.accepted } : c))
  const toggleAll = (v: boolean) =>
    setChunks((l) => l.map((c) => ({ ...c, accepted: v })))

  const approve = async () => {
    setBusy(true)
    const accepted = chunks.filter((c) => c.accepted).map((c) => c.index)
    try {
      const r = await fetch(`/api/rag/ingest/jobs/${encodeURIComponent(jobId)}/draft-approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accepted_indices: accepted }),
      })
      const d = await r.json()
      setMsg(d.ok ? `已采纳 ${d.approved} 块入库` : (d.detail || "失败"))
      onApproved?.()
    } catch (e) { setMsg(String(e)) } finally { setBusy(false) }
  }

  const accepted = chunks.filter((c) => c.accepted).length

  return (
    <div className="ind-card" style={{ padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between",
                    alignItems: "center", marginBottom: 12 }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>分块审核</span>
          <Badge tone="info">{chunks.length} 块</Badge>
          <Badge tone="success">{accepted} 采纳</Badge>
        </div>
        <div className="ind-toolbar" style={{ margin: 0 }}>
          <button className="ind-btn" onClick={() => toggleAll(true)}>全选</button>
          <button className="ind-btn" onClick={() => toggleAll(false)}>全不选</button>
          <button className="ind-btn ind-btn--primary"
                  disabled={busy || accepted === 0} onClick={approve}>
            {busy ? "入库中…" : `采纳入库（${accepted}）`}
          </button>
        </div>
      </div>

      {msg && (
        <div style={{ padding: "6px 10px", background: "rgba(79,214,154,.08)",
                      border: "1px solid rgba(79,214,154,.3)",
                      color: "#4fd69a", borderRadius: 6,
                      fontSize: 12, marginBottom: 10 }}>{msg}</div>
      )}

      {chunks.length === 0 ? (
        <EmptyState title="暂无待审核分块"
                    hint="上传文档后，在【上传记录】点【详情】获取 job_id"
                    icon="📄" />
      ) : (
        <div className="rag-review-list">
          {chunks.map((c) => (
            <div key={c.index}
                 className={"rag-chunk-card" + (c.accepted ? " ok" : " off")}
                 onClick={() => toggle(c.index)}>
              <div className="rag-chunk-head">
                <span className="rag-chunk-check">{c.accepted ? "☑" : "☐"}</span>
                <span className="rag-chunk-idx">#{c.index + 1}</span>
                {c.page_start > 0 && (
                  <Badge tone="muted">p.{c.page_start}-{c.page_end}</Badge>
                )}
                {c.source && (
                  <span className="rag-chunk-src">
                    📄 {c.source.split("/").pop()}
                  </span>
                )}
              </div>
              <div className="rag-chunk-text">{c.text}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ChunkReviewPanel
