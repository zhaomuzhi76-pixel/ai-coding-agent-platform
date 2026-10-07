/**
 * Terminal WebSocket 客户端：连接到 /ws/terminal。
 * 职责：只负责字节流传输，不碰 UI。
 */

import { WS_TERMINAL } from "../config/paths"
export interface TerminalSocketHandlers {
  onData: (data: string) => void
  onClose: () => void
  onError: (err: Event) => void
}

export interface TerminalSocketApi {
  send: (data: string) => void
  resize: (cols: number, rows: number) => void
  close: () => void
}

export function openTerminalSocket(
  baseUrl: string,
  handlers: TerminalSocketHandlers,
): TerminalSocketApi {
  const host = baseUrl.replace(/\/api\/?$/, "")
  const url = host.replace(/^http/, "ws") + WS_TERMINAL
  const ws = new WebSocket(url)
  ws.binaryType = "arraybuffer"

  ws.onmessage = (ev) => {
    if (typeof ev.data === "string") {
      handlers.onData(ev.data)
    } else if (ev.data instanceof ArrayBuffer) {
      handlers.onData(new TextDecoder().decode(ev.data))
    }
  }
  ws.onclose = () => handlers.onClose()
  ws.onerror = (e) => handlers.onError(e)

  return {
    send: (data) => {
      if (ws.readyState === WebSocket.OPEN) ws.send(data)
    },
    resize: (cols, rows) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "resize", cols, rows }))
      }
    },
    close: () => {
      // StrictMode 双挂载场景：CONNECTING 时延迟到 open 再关（避免浏览器警告）
      if (ws.readyState === WebSocket.CONNECTING) {
        ws.addEventListener("open", () => { try { ws.close() } catch { /* noop */ } }, { once: true })
        ws.addEventListener("error", () => { try { ws.close() } catch { /* noop */ } }, { once: true })
      } else {
        try { ws.close() } catch { /* noop */ }
      }
    },
  }
}
