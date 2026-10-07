/** MCP Client API。职责：唯一网络出口。
 * 不做 UI、不持状态、不解析 server。 */
import { apiBase } from "../config/runtime"
const BASE = `${apiBase()}/mcp_client`

interface Envelope<T> { ok: boolean; data?: T; error?: { code: string; message: string } }

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const r = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init.headers || {}) },
  })
  const payload = (await r.json()) as Envelope<T>
  if (!payload.ok || payload.data === undefined) {
    throw new Error(payload.error
      ? `${payload.error.code}: ${payload.error.message}`
      : "unknown error")
  }
  return payload.data
}

export interface ServerConfigDTO {
  id: string
  name: string
  transport: "stdio" | "http" | "sse"
  enabled: boolean
  namespace: string
  command?: string
  args?: string[]
  env?: Record<string, string>
  url?: string
}

export interface ServerStateDTO {
  server_id: string
  status: "disconnected" | "connecting" | "online" | "error"
  tool_count: number
  error: string
  started_at: number
  server_info: Record<string, unknown>
}

export interface ServerItem {
  config: ServerConfigDTO
  status: ServerStateDTO
}

export interface ToolInfo {
  namespaced_name: string
  raw_name: string
  server_id: string
}

export const mcpClientApi = {
  listServers(): Promise<{ servers: ServerItem[]; total: number; tool_count: number }> {
    return call(`${BASE}/servers`)
  },
  addServer(cfg: Omit<ServerConfigDTO, "enabled"> & { enabled?: boolean }): Promise<ServerStateDTO> {
    return call(`${BASE}/servers`, { method: "POST", body: JSON.stringify(cfg) })
  },
  removeServer(sid: string): Promise<boolean> {
    return call(`${BASE}/servers/${encodeURIComponent(sid)}`, { method: "DELETE" })
  },
  reconnect(sid: string): Promise<ServerStateDTO> {
    return call(`${BASE}/servers/${encodeURIComponent(sid)}/reconnect`, { method: "POST" })
  },
  tools(sid: string): Promise<{ server_id: string; tools: ToolInfo[]; count: number }> {
    return call(`${BASE}/servers/${encodeURIComponent(sid)}/tools`)
  },
}
