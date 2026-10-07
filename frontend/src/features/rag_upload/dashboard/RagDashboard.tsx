/** RAG 知识库主面板：点击选文件 → 待处理队列 → 点开始 → 实时进度 */
import { useCallback, useEffect, useState } from "react"
import {
  Badge, IndustrialPage, KpiCard, KpiRow,
} from "../../../app/ui/industrial"
import { RecallTestPanel } from "./RecallTestPanel"
import { RagQAPanel } from "./RagQAPanel"
import { RagModelSelectors } from "./RagModelSelectors"
import { VectorSourcesPanel } from "./VectorSourcesPanel"
import { UploadDropzone } from "../upload_dropzone"
import { UploadQueue } from "./UploadQueue"
import { ProgressList } from "./ProgressList"
import { JobDetailDrawer } from "../job_detail_drawer"
import { useJobPolling } from "../_hooks/useJobPolling"
import { useUploadQueue } from "../_hooks/useUploadQueue"
import { ragUploadApi, type IngestJob } from "../../../core/api/rag_upload_api"

interface RagStatus {
  count: number
  collection: string
  vector_path: string
  embedding: { base_url: string; model: string }
  reranker?: {
    url: string; enabled: boolean
    health?: { ok: boolean; models?: string[]; count?: number }
  }
}

type Tab = "recall" | "vectors" | "processing"

export function RagDashboard() {
  const [status, setStatus] = useState<RagStatus | null>(null)
  const [tab, setTab] = useState<Tab>("vectors")
  const [embModel, setEmbModel] = useState("")
  const [refreshKey, setRefreshKey] = useState(0)
  const [kb, setKb] = useState("tcm")
  const [ocrLang, setOcrLang] = useState("")
  const [busy, setBusy] = useState(false)
  const [detailJob, setDetailJob] = useState<IngestJob | null>(null)

  const refreshStatus = useCallback(() => {
    fetch("/api/rag/status")
      .then((r) => r.ok ? r.json() : null)
      .then((d) => setStatus(d?.data ?? d))
      .catch(() => {})
  }, [])

  const {
    items, setItems, startPoll, stopPoll, restored, dismiss,
  } = useJobPolling(() => {
    refreshStatus()
    setRefreshKey((k) => k + 1)
  })

  const {
    pending, add: addFiles, remove: removePending, clear: clearQueue,
  } = useUploadQueue(restored)

  useEffect(() => {
    refreshStatus()
    const id = window.setInterval(refreshStatus, 10000)
    return () => window.clearInterval(id)
  }, [refreshStatus])

  const clearItem = useCallback((jobId: string) => dismiss(jobId), [dismiss])

  const cancel = useCallback(async (jobId: string) => {
    stopPoll(jobId)
    try {
      await fetch(`/api/rag/ingest/jobs/${encodeURIComponent(jobId)}/purge`,
                  { method: "POST" })
    } catch {}
    clearItem(jobId)
  }, [stopPoll, clearItem])

  const handleDeleteVectors = useCallback(async (jobId: string) => {
    stopPoll(jobId)
    try {
      await fetch(`/api/rag/ingest/jobs/${encodeURIComponent(jobId)}/purge`,
                  { method: "POST" })
    } catch {}
    clearItem(jobId)
    refreshStatus()
    setRefreshKey((k) => k + 1)
  }, [stopPoll, clearItem, refreshStatus])

  const showDetail = useCallback(async (jobId: string) => {
    console.log("[DIAG] showDetail 被点击, jobId =", jobId)
    try {
      const j = await ragUploadApi.getJob(jobId)
      console.log("[DIAG] getJob 成功, status =", j?.status)
      setDetailJob(j)
      return
    } catch (e) {
      console.warn("[DIAG] getJob 失败，走 [FALLBACK]", e)
    }
    // [FALLBACK] 后端已丢这个 job（重启），用前端 item 数据构造简版
    const item = items.find((it) => it.jobId === jobId)
    if (!item) {
      console.error("[DIAG] fallback: items 里也找不到", jobId)
      return
    }
    setDetailJob({
      job_id: jobId,
      filename: item.filename,
      kb: kb || "?",
      lang: ocrLang || "ch",
      size_bytes: item.sizeBytes,
      status: item.status,
      progress: item.progress as any,
      chunks_indexed: item.chunks,
      elapsed_ms: item.elapsedMs,
      error: item.error || "",
      steps: [],
      draft_path: "",
      draft_count: 0,
      meta: { _fallback: true,
              _note: "后端已重启，本地缓存数据" },
    } as any)
    console.log("[DIAG] fallback setDetailJob 已调用")
  }, [items, kb, ocrLang])

  // 点击选择文件 → 只入队列（不自动上传）
  const handleFiles = useCallback((files: File[]) => {
    console.log("[handleFiles] received:", files.length, "files")
    if (!files || files.length === 0) return
    addFiles(files)
  }, [addFiles])

  // 点【开始处理】→ 逐个上传
  const handleStart = useCallback(async () => {
    if (pending.length === 0) return
    setTab("processing")
    setBusy(true)

    // 保存 embedding 模型
    if (embModel) {
      fetch("/api/rag/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ embedding_model: embModel }),
      }).catch(() => {})
    }

    const arr = Array.from(pending)
    // [OPTIMISTIC_UPLOAD] 预先加 N 个占位卡片（用户立即看到）
    const tempIds: string[] = []
    for (let i = 0; i < arr.length; i++) {
      const f = arr[i]
      const tid = `uploading-${Date.now()}-${i}-${f.name}`
      tempIds.push(tid)
    }
    setItems((prev) => [
      ...tempIds.map((tid, i) => ({
        jobId: tid,
        filename: arr[i].name,
        sizeBytes: arr[i].size,
        status: "uploading",
        chunks: 0,
        elapsedMs: 0,
      })),
      ...prev,
    ])

    for (let i = 0; i < arr.length; i++) {
      const f = arr[i]
      const tid = tempIds[i]
      try {
        const r = await ragUploadApi.uploadFileAsync(f, {
          kb, lang: ocrLang,
        })
        console.log("[handleStart] uploaded:", r.job_id, r.filename)
        // 把占位替换成真实 job_id
        setItems((prev) => prev.map((it) =>
          it.jobId === tid
            ? {
                ...it,
                jobId: r.job_id,
                filename: r.filename,
                sizeBytes: (r as any).size_bytes ?? f.size,
                status: "pending",
              }
            : it
        ))
        startPoll(r.job_id)
      } catch (e) {
        console.error("[handleStart] upload failed:", e)
        setItems((prev) => prev.map((it) =>
          it.jobId === tid
            ? { ...it, status: "error", error: String(e) }
            : it
        ))
      }
    }
    await clearQueue()
    // [FIX] 不调 refresh（会覆盖本地 active），只更新 activeCount
    setBusy(false)
  }, [pending, kb, ocrLang, embModel, startPoll, setItems, clearQueue])

  const healthy = status?.reranker?.health?.ok
  const activeCount = items.filter((i) =>
    ["pending", "running", "pending_review"].includes(i.status)).length

  return (
    <>
    <IndustrialPage
      title="RAG 知识库"
      subtitle="向量化数据 · 召回测试 · 处理进度"
      actions={(
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <Badge tone={healthy ? "success" : "muted"}>
            {healthy ? "重排序已启用" : "重排序未启用"}
          </Badge>
          <Badge tone="info">集合 {status?.collection ?? "—"}</Badge>
        </div>
      )}
    >
      <KpiRow>
        <KpiCard label="向量块总数" value={status?.count ?? 0} tone="success" />
        <KpiCard label="向量模型" value={status?.embedding?.model ?? "—"} />
        <KpiCard label="重排序模型"
                 value={status?.reranker?.health?.models?.[0]?.split("/").pop() ?? "未启用"}
                 tone={healthy ? "success" : "warning"} />
        <KpiCard label="处理中" value={activeCount}
                 tone={activeCount > 0 ? "warning" : "success"} />
      </KpiRow>

      <section style={{ marginTop: 16 }}>
        <RagModelSelectors onChange={setEmbModel} />
      </section>

      {/* 文件选择 + 队列 + 开始按钮 */}
      <section style={{ marginTop: 16 }}>
        <div className="ind-card" style={{ padding: 12 }}>
          <div style={{ display: "flex", gap: 12, alignItems: "center",
                        flexWrap: "wrap", marginBottom: 10 }}>
            <label style={{ display: "flex", gap: 6, alignItems: "center",
                            fontSize: 12, color: "var(--text-soft)" }}>
              知识库领域
              <select className="ind-select" value={kb}
                      onChange={(e) => setKb(e.target.value)}
                      style={{ fontSize: 12 }}>
                <option value="general">通用</option>
                <option value="tcm">中医</option>
                <option value="agriculture">农业</option>
                <option value="finance">金融</option>
              </select>
            </label>
            <label style={{ display: "flex", gap: 6, alignItems: "center",
                            fontSize: 12, color: "var(--text-soft)" }}>
              OCR 语言
              <select className="ind-select" value={ocrLang}
                      onChange={(e) => setOcrLang(e.target.value)}
                      style={{ fontSize: 12 }}>
                <option value="">自动（简体+英文）</option>
                <option value="chinese_cht">繁体中文（古籍）</option>
                <option value="ch">简体中文</option>
                <option value="en">英文</option>
                <option value="japan">日文</option>
              </select>
            </label>
            <span style={{ fontSize: 11, color: "var(--text-soft)", marginLeft: "auto" }}>
              PDF / 图片 / Word / Excel / PPT / HTML / MD / TXT · ≤1GB
            </span>
          </div>

          <UploadDropzone
            busy={busy}
            kbLabel={kb === "tcm" ? "中医" : kb === "general" ? "通用"
                    : kb === "agriculture" ? "农业" : "金融"}
            onFiles={handleFiles}
          />

          <UploadQueue
            pending={pending}
            busy={busy}
            embModel={embModel}
            onRemove={removePending}
            onStart={handleStart}
          />
        </div>
      </section>

      {/* Tabs */}
      <div className="ind-toolbar" style={{ marginTop: 16 }}>
        {([
          ["recall",     "🔍 召回测试"],
            ["qa",         "💬 图文问答"],
          ["vectors",    "📦 已入库数据"],
          ["processing", `📋 任务列表${activeCount > 0 ? `（${activeCount} 进行中）` : ""}`],
        ] as const).map(([k, label]) => (
          <button key={k}
                  className={"ind-btn" + (tab === k ? " ind-btn--primary" : "")}
                  onClick={() => setTab(k)}>
            {label}
          </button>
        ))}
      </div>

      <div style={{ marginTop: 14 }}>
        {tab === "recall" && <RecallTestPanel />}
        {tab === "qa" && <RagQAPanel />}
        {tab === "vectors" && <VectorSourcesPanel key={refreshKey} />}
                  {tab === "processing" && (() => {
            if (items.length === 0) {
              return (
                <div className="ind-card" style={{ padding: 60,
                                                    textAlign: "center",
                                                    opacity: 0.7 }}>
                  <div style={{ fontSize: 32, marginBottom: 10 }}>✨</div>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>
                    暂无任务
                  </div>
                  <div style={{ fontSize: 11, marginTop: 8, opacity: 0.6 }}>
                    上传文件后，任务会出现在这里
                  </div>
                </div>
              )
            }
            // 按状态分组：进行中 + 失败 + 已完成/已取消
            // [STATUS_FALLBACK] status 兜底：无 status 的按 pending 处理
            const safeItems = items.map((i) => ({
              ...i,
              status: i.status || "pending",
            }))
            const ACTIVE = ["pending", "running", "pending_review", "uploading"]
            const activeItems = safeItems.filter((i) =>
              ACTIVE.includes(i.status))
            const failedItems = safeItems.filter((i) =>
              i.status === "failed" || i.status === "error")
            const doneItems = safeItems.filter((i) =>
              ["done", "completed", "cancelled"].includes(i.status))
            return (
              <div style={{ display: "grid", gap: 16 }}>
                {activeItems.length > 0 && (
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600,
                                  marginBottom: 8, color: "#e29e4a" }}>
                      ⏳ 进行中（{activeItems.length}）
                    </div>
                    <ProgressList
                      items={activeItems}
                      onCancel={cancel}
                      onDeleteVectors={handleDeleteVectors}
                      onClear={clearItem}
                      onDetail={showDetail}
                    />
                  </div>
                )}
                {failedItems.length > 0 && (
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600,
                                  marginBottom: 8, color: "#ef8585" }}>
                      ❌ 失败（{failedItems.length}）
                    </div>
                    <ProgressList
                      items={failedItems}
                      onCancel={cancel}
                      onDeleteVectors={handleDeleteVectors}
                      onClear={clearItem}
                      onDetail={showDetail}
                    />
                  </div>
                )}
                {doneItems.length > 0 && (
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600,
                                  marginBottom: 8, color: "#4fd69a" }}>
                      ✅ 已完成 / 已取消（{doneItems.length}）
                    </div>
                    <ProgressList
                      items={doneItems}
                      onCancel={cancel}
                      onDeleteVectors={handleDeleteVectors}
                      onClear={clearItem}
                      onDetail={showDetail}
                    />
                  </div>
                )}
              </div>
            )
          })()}
      </div>
    </IndustrialPage>

    <JobDetailDrawer
      job={detailJob}
      onClose={() => setDetailJob(null)}
    />
    </>
  )
}

export default RagDashboard
