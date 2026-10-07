/** RAG 上传面板（组装 hook + 触发上传 + 展示队列/进度） */
import { useCallback, useState } from "react"

import { ragUploadApi, type IngestJob } from "../../core/api/rag_upload_api"
import { JobDetailDrawer } from "./job_detail_drawer"
import { UploadDropzone } from "./upload_dropzone"
import { UploadConfigRow } from "./dashboard/UploadConfigRow"
import { UploadQueue } from "./dashboard/UploadQueue"
import { ProgressList } from "./dashboard/ProgressList"
import { useJobPolling } from "./_hooks/useJobPolling"
import { useUploadQueue } from "./_hooks/useUploadQueue"

interface Props {
  onUploaded?: (job: IngestJob) => void
  embModel?: string
}

export function RagUploadPanel({ onUploaded, embModel = "" }: Props) {
  const [kb, setKb] = useState("tcm")
  const [ocrLang, setOcrLang] = useState("")
  const [busy, setBusy] = useState(false)
  const [detailJob, setDetailJob] = useState<IngestJob | null>(null)

  const {
    items, setItems, startPoll, stopPoll, updateItem, restored,
  } = useJobPolling(onUploaded)

  const {
    pending, add: addFiles, remove: removePending, clear: clearQueue,
  } = useUploadQueue(restored)

  // ---- 基础操作（先定义，供后续回调引用） ----
  const clearItem = useCallback((jobId: string) => {
    setItems((prev) => prev.filter((it) => it.jobId !== jobId))
  }, [setItems])

  const showDetail = useCallback(async (jobId: string) => {
    try { setDetailJob(await ragUploadApi.getJob(jobId)) } catch {}
  }, [])

  const cancel = useCallback(async (jobId: string) => {
    stopPoll(jobId)
    try {
      // 一键清理：草稿 + 向量 + job
      await fetch(
        `/api/rag/ingest/jobs/${encodeURIComponent(jobId)}/purge`,
        { method: "POST" },
      )
    } catch {}
    updateItem(jobId, { status: "cancelled" })
  }, [stopPoll, updateItem])

  // ---- 开始处理 ----
  const handleStart = useCallback(async () => {
    if (pending.length === 0) return
    setBusy(true)
    try {
      if (embModel) {
        await fetch("/api/rag/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ embedding_model: embModel }),
        }).catch(() => {})
      }
      const files = Array.from(pending)
      for (const f of files) {
        try {
          const r = await ragUploadApi.uploadFileAsync(f, { kb, lang: ocrLang })
          setItems((prev) => [{
            jobId: r.job_id, filename: r.filename,
            sizeBytes: r.size_bytes, status: "pending",
            chunks: 0, elapsedMs: 0,
          }, ...prev])
          startPoll(r.job_id)
        } catch (e) {
          setItems((prev) => [{
            jobId: `err-${Date.now()}-${f.name}`, filename: f.name,
            sizeBytes: f.size, status: "error",
            chunks: 0, elapsedMs: 0, error: String(e),
          }, ...prev])
        }
      }
      await clearQueue()
    } finally {
      setBusy(false)
    }
  }, [pending, kb, ocrLang, embModel, startPoll, setItems, clearQueue])

  // ---- 删除（取消草稿 or 回滚向量） ----
  const handleDeleteVectors = useCallback(async (jobId: string) => {
    stopPoll(jobId)
    try {
      await fetch(
        `/api/rag/ingest/jobs/${encodeURIComponent(jobId)}/purge`,
        { method: "POST" },
      )
    } catch {}
    clearItem(jobId)
  }, [stopPoll, clearItem])

  return (
    <section style={{ marginTop: 12 }}>
      <div className="ind-card" style={{ padding: 12, marginBottom: 12 }}>
        <UploadConfigRow
          kb={kb} ocrLang={ocrLang} busy={busy}
          onChangeKb={setKb} onChangeLang={setOcrLang}
        />
        <UploadDropzone busy={busy} kbLabel={kb} onFiles={addFiles} />
        <UploadQueue
          pending={pending} busy={busy} embModel={embModel}
          onRemove={removePending} onStart={handleStart}
        />
      </div>

      <ProgressList
        items={items}
        onCancel={cancel}
        onDeleteVectors={handleDeleteVectors}
        onClear={clearItem}
        onDetail={showDetail}
      />

      <JobDetailDrawer job={detailJob} onClose={() => setDetailJob(null)} />
    </section>
  )
}
export default RagUploadPanel
