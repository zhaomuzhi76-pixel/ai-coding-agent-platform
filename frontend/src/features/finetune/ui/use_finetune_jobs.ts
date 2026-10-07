/**
 * useFinetuneJobs：订阅 JobEvent 流并转成 React 状态。
 *
 * Owns:
 *   - socket 生命周期（mount 连接 / unmount 关闭）
 *   - 环形缓冲（最多保留 500 条）
 *   - phase 暴露
 *
 * Not:
 *   - 传输逻辑（finetune_job_socket 管）
 *   - 业务渲染（UI 组件管）
 */
import { useEffect, useRef, useState } from "react"
import {
  createFinetuneJobSocket,
  type FinetuneJobSocketOptions,
  type JobEvent,
} from "../ws/finetune_job_socket"
import type { ResilientSocket } from "../../../core/websocket/agent_socket_resilient"
import { backendHttpUrl } from "../../../core/config/runtime"

const HISTORY_LIMIT = 500

async function fetchHistory(jobId: string | null): Promise<JobEvent[]> {
  if (!jobId) return []
  try {
    const r = await fetch(`${backendHttpUrl()}/api/finetune/jobs/${encodeURIComponent(jobId)}/events?limit=${HISTORY_LIMIT}`)
    if (!r.ok) return []
    const d = await r.json() as { data?: { events?: JobEvent[] } }
    return d.data?.events || []
  } catch {
    return []
  }
}

const MAX_EVENTS = 500

export interface UseFinetuneJobsResult {
  events: JobEvent[]
  phase: string
  clear: () => void
}

export function useFinetuneJobs(
  options: FinetuneJobSocketOptions = {},
): UseFinetuneJobsResult {
  const [events, setEvents] = useState<JobEvent[]>([])
  const [phase, setPhase] = useState<string>("idle")
  const socketRef = useRef<ResilientSocket | null>(null)

  const jobId = options.jobId ?? null
  const baseUrl = options.baseUrl ?? null

  useEffect(() => {
    let cancelled = false
    // 先拉历史（仅当指定了 jobId）
    if (jobId) {
      fetchHistory(jobId).then((hist) => {
        if (cancelled || hist.length === 0) return
        setEvents((prev) => {
          const merged = [...hist, ...prev]
          return merged.length > MAX_EVENTS
            ? merged.slice(merged.length - MAX_EVENTS)
            : merged
        })
      })
    }
    const socket = createFinetuneJobSocket(
      { jobId, baseUrl: baseUrl ?? undefined },
      {
        onEvent: (ev) =>
          setEvents((prev) => {
            const next = prev.length >= MAX_EVENTS ? prev.slice(1) : prev.slice()
            next.push(ev)
            return next
          }),
        onPhaseChange: (p) => setPhase(p),
      },
    )
    socketRef.current = socket
    socket.connect()
    return () => {
      cancelled = true
      try { socket.close() } catch { /* ignore */ }
      socketRef.current = null
    }
  }, [jobId, baseUrl])

  return {
    events,
    phase,
    clear: () => setEvents([]),
  }
}
