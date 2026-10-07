/**
 * ResilientSocket: 状态机 + 退避 + 日志 的组合器。
 *
 * Owns:
 *   - 组合 SocketState + ReconnectConfig + SocketLogger
 *   - 提供 connect / close / onMessage 生命周期
 *   - 代际号隔离旧回调
 *
 * Not:
 *   - WebSocket 实例底层发送（走注入的 factory）
 *   - 业务消息解码（外部注入）
 *   - 状态机的实现（在 agent_socket_state.ts）
 */

import {
  initialState, bumpGeneration, isCurrent, type SocketState,
} from "./agent_socket_state"
import {
  DEFAULT_RECONNECT, nextDelay, shouldRetry, type ReconnectConfig,
} from "./agent_socket_reconnect"
import {
  SocketLogger, type LogEntry,
} from "./agent_socket_logger"

export interface ResilientHandlers {
  onMessage?: (data: string) => void
  onPhaseChange?: (phase: SocketState["phase"], generation: number) => void
  onGiveUp?: (lastError?: unknown) => void
}

export class ResilientSocket {
  private state: SocketState = initialState()
  private socket: WebSocket | null = null
  private logger: SocketLogger
  private config: ReconnectConfig
  private stopped = false

  private readonly url: string
  private readonly handlers: ResilientHandlers

  constructor(
    url: string,
    handlers: ResilientHandlers = {},
    config?: Partial<ReconnectConfig>,
    minLevel?: LogEntry["level"],
  ) {
    this.url = url
    this.handlers = handlers
    this.config = { ...DEFAULT_RECONNECT, ...(config || {}) }
    this.logger = new SocketLogger(minLevel || "info")
  }

  phase(): SocketState["phase"] { return this.state.phase }
  generation(): number { return this.state.generation }

  connect(): void {
    this.stopped = false
    this.openSocket(this.state.attempts)
  }

  send(payload: string): boolean {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      this.logger.log({ event: "send-dropped", level: "warn",
                        generation: this.state.generation })
      return false
    }
    this.socket.send(payload)
    return true
  }

  close(): void {
    this.stopped = true
    this.state.phase = "closed"
    this.state.generation += 1
    if (this.socket) {
      try { this.socket.close() } catch { /* noop */ }
      this.socket = null
    }
    this.handlers.onPhaseChange?.("closed", this.state.generation)
  }

  private openSocket(attempt: number): void {
    const gen = bumpGeneration(this.state)
    this.state.phase = attempt === 0 ? "connecting" : "reconnecting"
    this.handlers.onPhaseChange?.(this.state.phase, gen)
    this.logger.log({ event: "open", level: "info",
                      generation: gen, attempt })

    let socket: WebSocket
    try { socket = new WebSocket(this.url) }
    catch (e) {
      this.logger.log({ event: "open-throw", level: "error",
                        generation: gen, error: String(e) })
      this.scheduleRetry(attempt, e); return
    }
    this.socket = socket

    socket.onopen = () => {
      if (!isCurrent(this.state, gen)) return
      this.state.phase = "open"; this.state.attempts = 0
      this.handlers.onPhaseChange?.("open", gen)
      this.logger.log({ event: "opened", level: "info", generation: gen })
    }

    socket.onmessage = (ev) => {
      if (!isCurrent(this.state, gen)) return
      try { this.handlers.onMessage?.(String(ev.data)) }
      catch (e) {
        this.logger.log({ event: "message-decode-failed",
                          level: "warn", generation: gen, error: String(e) })
      }
    }

    socket.onerror = () => {
      if (!isCurrent(this.state, gen)) return
      this.logger.log({ event: "socket-error", level: "warn", generation: gen })
    }

    socket.onclose = () => {
      if (!isCurrent(this.state, gen)) return
      this.logger.log({ event: "closed", level: "info", generation: gen })
      if (this.stopped) return
      this.scheduleRetry(attempt, null)
    }
  }

  private scheduleRetry(attempt: number, err: unknown): void {
    if (!shouldRetry(attempt, this.config)) {
      this.state.phase = "closed"
      this.handlers.onGiveUp?.(err)
      this.handlers.onPhaseChange?.("closed", this.state.generation)
      this.logger.log({ event: "give-up", level: "error",
                        attempt, maxAttempts: this.config.maxAttempts })
      return
    }
    const delay = nextDelay(attempt, this.config)
    this.state.attempts = attempt + 1
    this.state.phase = "reconnecting"
    this.handlers.onPhaseChange?.("reconnecting", this.state.generation)
    this.logger.log({ event: "retry-scheduled", level: "info",
                      attempt, delayMs: delay })
    setTimeout(() => {
      if (!this.stopped) this.openSocket(attempt + 1)
    }, delay)
  }
}

export type { ReconnectConfig }
