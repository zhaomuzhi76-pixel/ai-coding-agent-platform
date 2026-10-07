/**
 * useDeployTask：异步部署 + WS 实时进度累积。
 *
 * Owns:
 *   - POST /deploy?wait=false → task_id
 *   - 订阅 WS，累积 steps / logs
 *   - 中途 onPartial 回调 + 最终 resolve DeployResult
 *
 * Not:
 *   - WebSocket 底层（deploy_socket 管）
 *   - UI 渲染（adapter_panel 管）
 */
import { useCallback } from "react"
import type { DeployResult, DeployStep } from "../../../core/contracts/finetune"
import { openDeploySocket } from "../ws/deploy_socket"
import { backendHttpUrl } from "../../../core/config/runtime"

export interface DeployPartial {
  steps: DeployStep[]
  logs: string[]
}

const DEPLOY_TIMEOUT_MS = 300_000

export function useDeployTask() {
  const run = useCallback(async (
    adapterId: string,
    onPartial?: (p: DeployPartial) => void,
  ): Promise<DeployResult> => {
    // 1. 异步 POST
    const resp = await fetch(
      `${backendHttpUrl()}/api/finetune/adapters/${encodeURIComponent(adapterId)}/deploy?wait=false`,
      { method: "POST" },
    )
    if (!resp.ok) {
      const t = await resp.text()
      throw new Error(`HTTP ${resp.status}: ${t.slice(0, 200)}`)
    }
    const body = await resp.json()
    const taskId: string | undefined = body?.data?.task_id
    if (!taskId) throw new Error("no task_id returned")

    // 2. WS 订阅
    return await new Promise<DeployResult>((resolve) => {
      const steps: DeployStep[] = []
      const logs: string[] = []
      let finalMeta: any = null
      let finished = false

      const ws = openDeploySocket(taskId)

      const done = (r: DeployResult) => {
        if (finished) return
        finished = true
        try { ws.close() } catch { /* ignore */ }
        clearTimeout(timer)
        resolve(r)
      }

      const timer = setTimeout(() => {
        done({
          ok: false, adapter_id: adapterId, model_name: "",
          returncode: -1, stdout: "", stderr: "",
          elapsed_sec: 0, error: "deploy timeout 300s",
          steps: [...steps], log_tail: [...logs],
        })
      }, DEPLOY_TIMEOUT_MS)

      ws.onmessage = (ev: MessageEvent) => {
        try {
          const e = JSON.parse(ev.data)
          if (e.type === "step") {
            const idx = steps.findIndex(s => s.name === e.name)
            const ns: DeployStep = {
              name: String(e.name),
              ok: e.status === "done" ? !!e.ok : false,
              elapsed_sec: Number(e.elapsed_sec) || 0,
              message: e.status === "start" ? "运行中…" : String(e.message || ""),
            }
            if (idx >= 0) steps[idx] = ns
            else steps.push(ns)
            onPartial?.({ steps: [...steps], logs: [...logs] })
          } else if (e.type === "log") {
            logs.push(String(e.message || ""))
            // 保留更多（上限 2000，分页在 UI 做）
            if (logs.length > 2000) logs.shift()
            onPartial?.({ steps: [...steps], logs: [...logs] })
          } else if (e.type === "result") {
            finalMeta = e
          } else if (e.type === "_end") {
            const ok = e.status === "succeeded"
            done({
              ok,
              adapter_id: adapterId,
              model_name: String(finalMeta?.model_name || ""),
              returncode: ok ? 0 : -1,
              stdout: "",
              stderr: "",
              elapsed_sec: Number(finalMeta?.elapsed_sec) || 0,
              error: ok ? "" : "deploy failed",
              steps: [...steps],
              log_tail: [...logs],
            })
          }
        } catch { /* ignore */ }
      }
      ws.onerror = () => {
        done({
          ok: false, adapter_id: adapterId, model_name: "",
          returncode: -1, stdout: "", stderr: "",
          elapsed_sec: 0, error: "ws error",
          steps: [...steps], log_tail: [...logs],
        })
      }
    })
  }, [])

  return { run }
}
