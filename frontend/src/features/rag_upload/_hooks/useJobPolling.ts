/** 轮询层：管理 job 状态 + 自动 approve + refresh */
import { useCallback, useEffect, useRef, useState } from "react"
import { ragUploadApi, type IngestJob } from "../../../core/api/rag_upload_api"
import { saveJobCache, loadJobCache, type CachedJob } from "../persistence/job_cache"

export interface JobItem {
  jobId: string
  filename: string
  sizeBytes: number
  status: string
  progress?: { phase: string; current: number; total: number; percent: number }
  error?: string
  chunks: number
  elapsedMs: number
}

const POLL_MS = 1500
const TIMEOUT_MS = 4 * 60 * 60 * 1000
const APPROVE_DELAY_MS = 8000
const REFRESH_MS = 60000

const autoApproved = new Set<string>()

async function autoApprove(jobId: string): Promise<boolean> {
  if (autoApproved.has(jobId)) return true
  autoApproved.add(jobId)
  await new Promise((r) => setTimeout(r, APPROVE_DELAY_MS))
  try {
    const r = await fetch(
      `/api/rag/ingest/jobs/${encodeURIComponent(jobId)}/draft-approve`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accepted_indices: null }),
      },
    )
    if (r.ok) { console.log("[autoApprove] OK:", jobId); return true }
    console.warn("[autoApprove] failed:", r.status, jobId)
    setTimeout(() => autoApproved.delete(jobId), 30000)
    return false
  } catch (e) {
    console.error("[autoApprove] error:", e)
    setTimeout(() => autoApproved.delete(jobId), 30000)
    return false
  }
}

// 本地已 dismiss 的 job（用户主动清除的）
const dismissed = new Set<string>()
try {
  const raw = localStorage.getItem("biancheng.rag.dismissed")
  if (raw) JSON.parse(raw).forEach((x: string) => dismissed.add(x))
} catch { /* ignore */ }

function markDismissed(jobId: string) {
  dismissed.add(jobId)
  try {
    localStorage.setItem("biancheng.rag.dismissed",
      JSON.stringify(Array.from(dismissed)))
  } catch { /* ignore */ }
}

/** 从 localStorage cache 中彻底移除该 job。 */
export function purgeJobCache(jobId: string) {
  dismissed.add(jobId)
  try {
    localStorage.setItem("biancheng.rag.dismissed",
      JSON.stringify(Array.from(dismissed)))
  } catch { /* ignore */ }
  try {
    const raw = localStorage.getItem("biancheng.rag.upload.cache")
    if (raw) {
      const arr = JSON.parse(raw) as Array<{ jobId?: string }>
      const filtered = arr.filter((x) => x.jobId !== jobId)
      localStorage.setItem("biancheng.rag.upload.cache", JSON.stringify(filtered))
    }
  } catch { /* ignore */ }
}

export async function cancelJob(jobId: string): Promise<boolean> {
  try {
    const r = await fetch(
      `/api/rag/ingest/jobs/${encodeURIComponent(jobId)}/cancel`,
      { method: "POST" }
    )
    if (r.ok) { purgeJobCache(jobId); return true }
    console.warn("[cancelJob] failed:", r.status, jobId)
    return false
  } catch (e) { console.error("[cancelJob]", e); return false }
}

export function useJobPolling(onDone?: (j: IngestJob) => void) {
  const [items, setItems] = useState<JobItem[]>(
    () => loadJobCache() as JobItem[])
  const [restored, setRestored] = useState(false)
  const pollers = useRef<Map<string, number>>(new Map())

  const stopPoll = useCallback((jobId: string) => {
    const t = pollers.current.get(jobId)
    if (t !== undefined) {
      window.clearInterval(t)
      pollers.current.delete(jobId)
    }
  }, [])

  const update = useCallback((jobId: string, patch: Partial<JobItem>) => {
    setItems((prev) =>
      prev.map((it) => it.jobId === jobId ? { ...it, ...patch } : it))
  }, [])

  const poll = useCallback(async (jobId: string) => {
    try {
      let j
      try {
        j = await ragUploadApi.getJob(jobId)
      } catch (err) {
        const msg = String(err)
        if (msg.includes("JSON") || msg.includes("Unexpected end")) {
          console.warn("[poll] 后端响应异常，跳过本轮:", msg.slice(0, 100))
          return
        }
        throw err
      }
      update(jobId, {
        status: j.status,
        progress: j.progress as any,
        chunks: j.chunks_indexed,
        elapsedMs: j.elapsed_ms,
        error: j.error,
      })
      if ((j.status as string) === "pending_review") {
        console.log("[poll] pending_review → autoApprove", jobId)
        const ok = await autoApprove(jobId)
        if (ok) {
          setTimeout(async () => {
            try {
              const j2 = await ragUploadApi.getJob(jobId)
              update(jobId, {
                status: j2.status,
                progress: j2.progress as any,
                chunks: j2.chunks_indexed,
                elapsedMs: j2.elapsed_ms,
              })
              if ((j2.status as string) === "done" ||
                  j2.status === "failed" ||
                  (j2.status as string) === "cancelled") {
                stopPoll(jobId)
                onDone?.(j2)
              }
            } catch { /* ignore */ }
          }, 800)
        }
        return
      }
      if ((j.status as string) === "done" ||
          j.status === "failed" ||
          (j.status as string) === "cancelled") {
        stopPoll(jobId)
        onDone?.(j)
      }
    } catch (e) {
      const key = `_fail_${jobId}`
      const fails = ((window as any)[key] || 0) + 1
      ;(window as any)[key] = fails
      if (fails >= 3) {
        update(jobId, { status: "error", error: String(e) })
        stopPoll(jobId)
        delete (window as any)[key]
      } else {
        console.warn(`[poll] ${jobId} 失败 ${fails}/3，跳过本轮`)
      }
    }
  }, [update, stopPoll, onDone])

  const start = useCallback((jobId: string) => {
    stopPoll(jobId)
    void poll(jobId)
    const t = window.setInterval(() => void poll(jobId), POLL_MS)
    pollers.current.set(jobId, t)
    window.setTimeout(() => stopPoll(jobId), TIMEOUT_MS)
  }, [poll, stopPoll])

  const startRef = useRef(start)
  useEffect(() => { startRef.current = start }, [start])

  const refresh = useCallback(async () => {
    try {
      const resp = await fetch('/api/rag/ingest/jobs?limit=50')
      if (!resp.ok) { console.error("[refresh] HTTP", resp.status); return }
      const d = await resp.json()
      const rawJobs: any[] = d?.data?.jobs || []
      // 过滤用户主动 dismiss 的（永久消失）
      const fresh = rawJobs.filter((j) => !dismissed.has(j.job_id))
      const freshItems: JobItem[] = fresh.map((j) => ({
        jobId: j.job_id, filename: j.filename, sizeBytes: j.size_bytes,
        status: j.status, progress: j.progress,
        chunks: j.chunks_indexed, elapsedMs: j.elapsed_ms, error: j.error,
      }))
      // 合并：本地在跑的卡片永不丢
      setItems((prev) => {
        const TERMINAL = new Set(["done", "failed", "error", "cancelled"])
        const remoteMap = new Map(freshItems.map((it) => [it.jobId, it]))
        const merged: JobItem[] = []
        for (const it of prev) {
          const remote = remoteMap.get(it.jobId)
          if (remote) {
            // [FORCE_REMOTE] 后端数据优先（status/chunks 等全用后端的）
            merged.push({ ...it, ...remote })
            remoteMap.delete(it.jobId)
          } else if (!TERMINAL.has(it.status)) {
            // 本地新建（uploading/pending），保留但加 fallback status
            merged.push({
              ...it,
              status: it.status || "pending",
              chunks: it.chunks ?? 0,
              elapsedMs: it.elapsedMs ?? 0,
            })
          }
        }
        for (const remote of remoteMap.values()) merged.push(remote)
        return merged
      })
      for (const it of freshItems) {
        const s = it.status
        if (s === "pending" || s === "running") {
          startRef.current(it.jobId)
        } else if (s === "pending_review") {
          void autoApprove(it.jobId).then((ok) => {
            if (ok) startRef.current(it.jobId)
          })
        }
      }
    } catch (e) {
      console.warn("[refresh] failed:", e)
    }
  }, [])

  useEffect(() => {
    let alive = true
    ;(async () => {
      await refresh()
      if (alive) setRestored(true)
    })()
    const timer = window.setInterval(() => { void refresh() }, REFRESH_MS)
    return () => { alive = false; window.clearInterval(timer) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!restored) return
    saveJobCache(items.map((it) => ({ ...it, cachedAt: Date.now() } as CachedJob)))
  }, [items, restored])

  useEffect(() => () => {
    pollers.current.forEach((t) => window.clearInterval(t))
    pollers.current.clear()
  }, [])

  const dismiss = useCallback((jobId: string) => {
    markDismissed(jobId)
    setItems((prev) => prev.filter((it) => it.jobId !== jobId))
  }, [])

  return {
    items, setItems, restored,
    startPoll: start, stopPoll, updateItem: update,
    dismiss, refresh, cancelJob,
  }
}
