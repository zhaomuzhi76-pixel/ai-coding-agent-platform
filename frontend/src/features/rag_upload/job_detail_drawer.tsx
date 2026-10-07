/** Job 详情抽屉。职责：展示 chunks / steps / JSON 三个 Tab。
 * 不做上传、不轮询、不做 HTTP（api 层管）。 */
import { useEffect, useState } from "react"

import { ragUploadApi } from "../../core/api/rag_upload_api"
import type { IngestJob } from "../../core/api/rag_upload_api"
import { Badge } from "../../app/ui/industrial"
import { JobStepsTimeline } from "./dashboard/JobStepsTimeline"

interface Props { job: IngestJob | null; onClose: () => void }

interface ChunkItem {
  chunk_id: string
  text: string
  metadata: Record<string, unknown>
}

type Tab = "chunks" | "steps" | "json"

const TAB_LABEL: Record<Tab, string> = {
  chunks: "分块数据",
  steps: "生成过程",
  json: "原始 JSON",
}


function ChunksTab({ jobId }: { jobId: string }) {
  const [chunks, setChunks] = useState<ChunkItem[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [busy, setBusy] = useState(false)
  const LIMIT = 20

  useEffect(() => {
    let alive = true
    setBusy(true)
    ragUploadApi.getJobChunks(jobId, offset, LIMIT).then((r) => {
      if (!alive) return
      setChunks(r.chunks)
      setTotal(r.total)
    }).finally(() => { if (alive) setBusy(false) })
    return () => { alive = false }
  }, [jobId, offset])

  return (
    <div style={{ display: "grid", gap: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between",
                    alignItems: "center", fontSize: 12, opacity: 0.7 }}>
        <span>共 <b style={{ color: "#7aa2f7" }}>{total}</b> 条分块</span>
        <div style={{ display: "flex", gap: 6 }}>
          <button className="ind-btn"
            disabled={offset === 0 || busy}
            onClick={() => setOffset(Math.max(0, offset - LIMIT))}>上一页</button>
          <span style={{ padding: "4px 8px" }}>
            {offset + 1}-{Math.min(offset + LIMIT, total)} / {total}
          </span>
          <button className="ind-btn"
            disabled={offset + LIMIT >= total || busy}
            onClick={() => setOffset(offset + LIMIT)}>下一页</button>
        </div>
      </div>

      {chunks.map((c, i) => {
        const m = c.metadata || {}
        return (
          <div key={c.chunk_id || i} style={{
            padding: "8px 10px", borderRadius: 6, fontSize: 12,
            background: "rgba(118,169,255,.04)",
            border: "1px solid rgba(118,169,255,.15)",
          }}>
            <div style={{ display: "flex", gap: 8, marginBottom: 6,
                          fontSize: 11, opacity: 0.65 }}>
              <span style={{ fontFamily: "monospace" }}>#{offset + i + 1}</span>
              <Badge tone="info">{String(m.kb ?? "-")}</Badge>
              {m.page_no != null && <span>第 {String(m.page_no)} 页</span>}
              {m.source != null && (
                <span style={{ opacity: 0.6 }}>{String(m.source).slice(0, 30)}</span>
              )}
              <span style={{ marginLeft: "auto", opacity: 0.5 }}>
                {c.chunk_id.slice(0, 16)}...
              </span>
            </div>
            <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
              {c.text}
            </div>
          </div>
        )
      })}

      {chunks.length === 0 && !busy && (
        <div style={{ textAlign: "center", opacity: 0.5, padding: 30 }}>
          无分块数据
        </div>
      )}
    </div>
  )
}

function StepsTab({ job }: { job: IngestJob }) {
  const ext = job as unknown as {
    steps?: Array<{ ts: number; phase: string; message: string;
                    detail?: Record<string, unknown> }>
    progress?: { phase: string; current: number; total: number;
                 percent: number; message?: string }
    created_at?: number
  }
  const steps = ext.steps || []
  const progress = ext.progress
  const createdAt = ext.created_at

  if (steps.length === 0) {
    return (
      <div style={{ textAlign: "center", opacity: 0.5, padding: 30 }}>
        无过程记录（此 job 在追踪上线前创建）
      </div>
    )
  }

  return (
    <JobStepsTimeline
      steps={steps}
      progress={progress}
      createdAt={createdAt}
    />
  )
}
function JsonTab({ job }: { job: IngestJob }) {
  return (
    <pre style={{
      fontSize: 11, lineHeight: 1.5, padding: 10,
      background: "rgba(0,0,0,.25)",
      borderRadius: 6, overflow: "auto", maxHeight: "60vh",
      fontFamily: "ui-monospace, monospace",
    }}>{JSON.stringify(job, null, 2)}</pre>
  )
}

export function JobDetailDrawer({ job: initialJob, onClose }: Props) {
  const [tab, setTab] = useState<Tab>("chunks")
  // [LIVE] 抽屉内部持有实时 job（每 1.5s 自动刷新）
  const [job, setJob] = useState<IngestJob | null>(initialJob)

  // 父组件切换 job 时同步初始值
  useEffect(() => {
    setJob(initialJob)
  }, [initialJob?.job_id])

  // Esc 关闭
  useEffect(() => {
    const onEsc = (e: KeyboardEvent) => { if (e.key === "Escape") onClose() }
    window.addEventListener("keydown", onEsc)
    return () => window.removeEventListener("keydown", onEsc)
  }, [onClose])

  // [LIVE] 打开时每 1.5s 拉最新 job（到终态自动停）
  useEffect(() => {
    if (!job?.job_id) return
    const TERMINAL = ["done", "failed", "cancelled"]
    if (TERMINAL.includes(job.status as string)) return

    const timer = setInterval(async () => {
      try {
        const fresh = await ragUploadApi.getJob(job.job_id)
        setJob(fresh)
        if (TERMINAL.includes(fresh.status as string)) {
          clearInterval(timer)
        }
      } catch { /* 网络抖动忽略 */ }
    }, 1500)
    return () => clearInterval(timer)
  }, [job?.job_id, job?.status])

  if (!job) return null

  return (
    <>
      <div onClick={onClose} style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,.4)",
        zIndex: 998,
      }} />
      <div style={{
        position: "fixed", top: 0, right: 0, bottom: 0, width: "min(720px, 92vw)",
        background: "#0d1117", borderLeft: "1px solid rgba(118,169,255,.2)",
        zIndex: 999, display: "flex", flexDirection: "column",
        boxShadow: "-4px 0 30px rgba(0,0,0,.6)",
      }}>
        <div style={{
          padding: "14px 20px", borderBottom: "1px solid rgba(118,169,255,.15)",
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 500 }}>{job.filename}</div>
            <div style={{ fontSize: 11, opacity: 0.55, marginTop: 4 }}>
              job_id: {job.job_id} · {job.status} · {job.kb}
            </div>
          </div>
          <button className="ind-btn" onClick={onClose}>✕</button>
        </div>

        <div style={{ display: "flex", gap: 8, padding: "10px 20px",
                      borderBottom: "1px solid rgba(118,169,255,.1)" }}>
          {(["chunks", "steps", "json"] as Tab[]).map((t) => (
            <button key={t} className="ind-btn"
              style={{
                background: tab === t ? "rgba(118,169,255,.15)" : "transparent",
                borderColor: tab === t ? "#7aa2f7" : undefined,
              }}
              onClick={() => setTab(t)}>{TAB_LABEL[t]}</button>
          ))}
        </div>

        <div style={{ flex: 1, overflow: "auto", padding: 20 }}>
          {tab === "chunks" && <ChunksTab jobId={job.job_id} />}
          {tab === "steps" && <StepsTab job={job} />}
          {tab === "json" && <JsonTab job={job} />}
        </div>
      </div>
    </>
  )
}
