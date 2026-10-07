/**
 * TreeSocket: /ws/tree WebSocket 客户端。
 *
 * 单一职责：
 *   - 连 /ws/tree
 *   - 发 subscribe / unsubscribe / ping
 *   - 收 ready / subscribed / tree_changed / pong / error
 *   - 事件回调
 *
 * 不负责：
 *   - file_tree_store 更新（调用方决定）
 *   - 重连策略（下一轮可选增强）
 *   - 事件过滤（后端已过滤）
 *
 * 契约对齐后端 backend/api/ws_tree_protocol.py
 */

import { WS_TREE } from "../config/paths"
export type TreeSocketState =
  | "idle"
  | "connecting"
  | "open"
  | "closed"

export interface TreeChangeEvent {
  type: "created" | "modified" | "deleted"
  path: string
  name: string
  kind: "file" | "dir"
  mtime_ns?: number
  size?: number
}

export interface TreeSocketHandlers {
  onReady?: (sessionId: string) => void
  onSubscribed?: (projectId: string) => void
  onTreeChanged?: (projectId: string, events: TreeChangeEvent[]) => void
  onError?: (reason: string) => void
  onStateChange?: (state: TreeSocketState) => void
}

export class TreeSocket {
  private socket: WebSocket | null = null
  private state: TreeSocketState = "idle"
  private currentSessionId = ""

  private readonly url: string
  private readonly handlers: TreeSocketHandlers

  constructor(
    url: string,
    handlers: TreeSocketHandlers = {},
  ) {
    this.url = url
    this.handlers = handlers
  }

  connect(): void {
    if (
      this.socket?.readyState === WebSocket.OPEN
      || this.socket?.readyState === WebSocket.CONNECTING
    ) {
      return
    }

    this.setState("connecting")
    let s: WebSocket
    try {
      s = new WebSocket(this.url)
    } catch (e) {
      this.setState("closed")
      this.handlers.onError?.(String(e))
      return
    }
    this.socket = s

    s.onopen = () => {
      this.setState("open")
    }
    s.onmessage = (ev) => {
      this.handleMessage(ev.data)
    }
    s.onerror = () => {
      this.setState("closed")
      this.handlers.onError?.("tree websocket error")
    }
    s.onclose = () => {
      this.setState("closed")
      this.socket = null
      this.currentSessionId = ""
    }
  }

  subscribe(projectId: string, workspaceRoot: string): void {
    this.send({
      action: "subscribe",
      project_id: projectId,
      workspace_root: workspaceRoot,
    })
  }

  unsubscribe(): void {
    this.send({ action: "unsubscribe" })
  }

  ping(): void {
    this.send({ action: "ping" })
  }

  close(): void {
    try { this.socket?.close() } catch { /* noop */ }
    this.socket = null
    this.setState("closed")
  }

  sessionId(): string {
    return this.currentSessionId
  }

  getState(): TreeSocketState {
    return this.state
  }

  private send(payload: Record<string, unknown>): void {
    const s = this.socket
    if (!s || s.readyState !== WebSocket.OPEN) {
      this.handlers.onError?.("tree websocket not connected")
      return
    }
    s.send(JSON.stringify(payload))
  }

  private setState(next: TreeSocketState): void {
    if (this.state !== next) {
      this.state = next
      this.handlers.onStateChange?.(next)
    }
  }

  private handleMessage(raw: unknown): void {
    let msg: Record<string, unknown>
    try {
      msg = typeof raw === "string" ? JSON.parse(raw) : (raw as Record<string, unknown>)
    } catch {
      this.handlers.onError?.("tree websocket invalid json")
      return
    }
    const type = String(msg.type ?? "")
    switch (type) {
      case "ready": {
        this.currentSessionId = String(msg.session_id ?? "")
        this.handlers.onReady?.(this.currentSessionId)
        return
      }
      case "subscribed": {
        this.handlers.onSubscribed?.(String(msg.project_id ?? ""))
        return
      }
      case "tree_changed": {
        const pid = String(msg.project_id ?? "")
        const events = Array.isArray(msg.events)
          ? (msg.events as TreeChangeEvent[])
          : []
        this.handlers.onTreeChanged?.(pid, events)
        return
      }
      case "error": {
        this.handlers.onError?.(String(msg.reason ?? "unknown"))
        return
      }
      case "pong": {
        return
      }
      default: {
        this.handlers.onError?.("tree websocket unknown type: " + type)
      }
    }
  }
}

export function buildTreeSocketUrl(
  wsBase: string,
): string {
  // wsBase 形如 ws://host:port/ws/agent
  // 换成 /ws/tree
  return wsBase.replace(/\/ws\/agent$/, WS_TREE)
}
