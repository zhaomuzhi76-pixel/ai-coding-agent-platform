/**
 * FinetuneJobSocket：/ws/finetune/jobs 的薄包装。
 *
 * Owns:
 *   - JobEvent 类型
 *   - URL 构造（含可选 job_id 过滤）
 *   - 消息 JSON 解码
 *
 * Not:
 *   - 重连 / 退避 / 状态机（复用 core/websocket/agent_socket_resilient）
 *   - React 状态（use_finetune_jobs 管）
 */
import {
  ResilientSocket,
  type ResilientHandlers,
} from "../../../core/websocket/agent_socket_resilient"
import { BACKEND_PORT } from "../../../core/config/runtime"

export interface JobEvent {
  event_id: string
  event_type:
    | "created" | "started" | "progress" | "log" | "epoch"
    | "checkpoint" | "eval" | "succeeded" | "failed" | "cancelled"
  payload: Record<string, unknown>
  created_at: number
}

export interface FinetuneJobSocketHandlers {
  onEvent?: (event: JobEvent) => void
  onPhaseChange?: ResilientHandlers["onPhaseChange"]
  onGiveUp?: ResilientHandlers["onGiveUp"]
}

export interface FinetuneJobSocketOptions {
  /** 可选：只订阅某 job_id */
  jobId?: string | null
  /** 可选：覆盖默认 host（Electron 里常用） */
  baseUrl?: string
}

function defaultBase(): string {
  // 生产打包（Electron 加载后端静态文件）时，页面和后端同源在 9022；
  // vite dev (4173) 时 page host 是 4173，但 WS 后端仍在 9022。
  // 因此按 port 判断：非 9022 一律强制指向 127.0.0.1:9022。
  const BACKEND_PORT = "9022"
  const BACKEND_HOST = "127.0.0.1"
  if (typeof window === "undefined") return `ws://${BACKEND_HOST}:${BACKEND_PORT}`
  const proto = window.location.protocol === "https:" ? "wss" : "ws"
  const port = window.location.port
  if (port === BACKEND_PORT) {
    return `${proto}://${window.location.host}`
  }
  return `${proto}://${BACKEND_HOST}:${BACKEND_PORT}`
}

export function buildFinetuneJobsUrl(opts: FinetuneJobSocketOptions = {}): string {
  const base = (opts.baseUrl || defaultBase()).replace(/\/$/, "")
  const q = opts.jobId ? `?job_id=${encodeURIComponent(opts.jobId)}` : ""
  return `${base}/ws/finetune/jobs${q}`
}

export function createFinetuneJobSocket(
  opts: FinetuneJobSocketOptions = {},
  handlers: FinetuneJobSocketHandlers = {},
): ResilientSocket {
  const url = buildFinetuneJobsUrl(opts)
  return new ResilientSocket(url, {
    onMessage: (data: string) => {
      if (!data || data === '{"type":"pong"}') return
      try {
        const ev = JSON.parse(data) as JobEvent
        handlers.onEvent?.(ev)
      } catch {
        /* 非法 JSON 静默丢弃 */
      }
    },
    onPhaseChange: handlers.onPhaseChange,
    onGiveUp: handlers.onGiveUp,
  })
}

export type { ResilientSocket }
