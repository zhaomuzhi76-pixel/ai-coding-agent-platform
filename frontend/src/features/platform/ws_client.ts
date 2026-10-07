/**
 * Platform WS 客户端：订阅 propose 事件流。
 *
 * 事件：
 *   {event: "stage", name: "propose"}
 *   {event: "related_files", files: [...]}
 *   {event: "token", text: "..."}
 *   {event: "done", proposal_id, plan, changes}
 *   {event: "error", reason}
 */
export interface PlatformWsEvent {
  event: string
  [key: string]: unknown
}

function resolveWsUrl(): string {
  const loc = window.location
  const proto = loc.protocol === "https:" ? "wss:" : "ws:"
  return `${proto}//${loc.host}/ws/platform`
}

export class PlatformWsClient {
  private _ws: WebSocket | null = null
  private _url: string
  private _handlers: Set<(e: PlatformWsEvent) => void> = new Set()

  constructor(url?: string) {
    this._url = url || resolveWsUrl()
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this._ws = new WebSocket(this._url)
      } catch (e) {
        reject(e)
        return
      }
      const ws = this._ws
      ws.onopen = () => resolve()
      ws.onerror = (e) => reject(e)
      ws.onclose = () => {
        this._ws = null
      }
      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data) as PlatformWsEvent
          this._handlers.forEach((h) => h(data))
        } catch {
          // ignore malformed
        }
      }
    })
  }

  subscribe(handler: (e: PlatformWsEvent) => void): () => void {
    this._handlers.add(handler)
    return () => this._handlers.delete(handler)
  }

  send(payload: Record<string, unknown>): void {
    if (!this._ws || this._ws.readyState !== WebSocket.OPEN) {
      throw new Error("WS not connected")
    }
    this._ws.send(JSON.stringify(payload))
  }

  close(): void {
    if (this._ws) {
      this._ws.close()
      this._ws = null
    }
  }

  ready(): boolean {
    return this._ws !== null && this._ws.readyState === WebSocket.OPEN
  }
}
