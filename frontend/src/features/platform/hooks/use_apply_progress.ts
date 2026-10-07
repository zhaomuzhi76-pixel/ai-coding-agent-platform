/**
 * useApplyProgress：订阅代码 apply 进度（WS 实时累积）。
 *
 * Owns:
 *   - POST /platform/apply?wait=false → task_id
 *   - WS 订阅 + 累积 chunks/logs
 *   - 状态机（idle → running → done/failed）
 *
 * Not:
 *   - WebSocket 底层（apply_socket 管）
 *   - UI 渲染（调用方管）
 */
import { useCallback, useRef, useState } from "react"
import { openApplySocket } from "../ws/apply_socket"
import { backendHttpUrl } from "../../../core/config/runtime"

export interface ApplyChunkEvent {
  file: string
  status: "start" | "done" | "failed"
  index: number
  total: number
  error?: string
}

export interface ApplyProgress {
  phase: "idle" | "running" | "done" | "failed"
  taskId: string
  proposalId: string
  chunks: ApplyChunkEvent[]
  logs: string[]
  error: string
}

const EMPTY: ApplyProgress = {
  phase: "idle", taskId: "", proposalId: "",
  chunks: [], logs: [], error: "",
}

export function useApplyProgress() {
  const [progress, setProgress] = useState<ApplyProgress>(EMPTY)
  const wsRef = useRef<WebSocket | null>(null)

  const reset = useCallback(() => {
    try { wsRef.current?.close() } catch { /* ignore */ }
    wsRef.current = null
    setProgress(EMPTY)
  }, [])

  const apply = useCallback(async (proposalId: string): Promise<boolean> => {
    setProgress({ ...EMPTY, phase: "running", proposalId })
    try {
      const resp = await fetch(
        `${backendHttpUrl()}/api/platform/apply?wait=false`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ proposal_id: proposalId }),
        },
      )
      if (!resp.ok) {
        const t = await resp.text()
        throw new Error(`HTTP ${resp.status}: ${t.slice(0, 200)}`)
      }
      const body = await resp.json()
      const tid: string = body?.data?.task_id || ""
      if (!tid) throw new Error("no task_id returned")

      return await new Promise<boolean>((resolve) => {
        const chunks: ApplyChunkEvent[] = []
        const logs: string[] = []
        let finished = false

        const done = (ok: boolean, err = "") => {
          if (finished) return
          finished = true
          try { ws.close() } catch { /* ignore */ }
          setProgress((p) => ({
            ...p,
            phase: ok ? "done" : "failed",
            chunks: [...chunks],
            logs: [...logs],
            error: err,
          }))
          resolve(ok)
        }

        const ws = openApplySocket(tid)
        wsRef.current = ws

        ws.onmessage = (ev: MessageEvent) => {
          try {
            const e = JSON.parse(ev.data)
            if (e.type === "chunk") {
              const c: ApplyChunkEvent = {
                file: String(e.file || ""),
                status: e.status,
                index: Number(e.index) || 0,
                total: Number(e.total) || 0,
                error: e.error ? String(e.error) : undefined,
              }
              const idx = chunks.findIndex(
                (x) => x.file === c.file && x.index === c.index,
              )
              if (idx >= 0) chunks[idx] = c
              else chunks.push(c)
              setProgress((p) => ({ ...p, chunks: [...chunks] }))
            } else if (e.type === "log") {
              logs.push(String(e.message || ""))
              if (logs.length > 500) logs.shift()
              setProgress((p) => ({ ...p, logs: [...logs] }))
            } else if (e.type === "error") {
              done(false, String(e.message || "unknown error"))
            } else if (e.type === "_end") {
              done(e.status === "succeeded", String(e.error || ""))
            }
          } catch { /* ignore */ }
        }
        ws.onerror = () => done(false, "ws error")
        setTimeout(() => done(false, "apply timeout 300s"), 300_000)
      })
    } catch (e) {
      const msg = String((e as Error).message || e)
      setProgress((p) => ({ ...p, phase: "failed", error: msg }))
      return false
    }
  }, [])

  return { progress, apply, reset }
}

export type { ApplyProgress }
