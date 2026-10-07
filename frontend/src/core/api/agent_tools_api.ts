/** Agent Tools HTTP 客户端。职责：唯一网络出口。
 * 不持状态、不做工具逻辑、不渲染。 */
import { apiBase } from "../config/runtime"
const BASE = `${apiBase()}/agent`

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

export interface ToolItem {
  name: string
  description: string
  category: string
  domain: string
  server: string
  tags: string[]
}

export interface ToolsList { total: number; groups: Record<string, ToolItem[]> }

export interface MountsSnapshot {
  session_id: string
  enabled: string[]
  total: number
  enabled_count: number
}

export interface ToolImage {
  id: string
  mime: string
  url?: string | null
  b64?: string | null
  alt_text?: string
}

export interface ToolTraceEntry {
  step: number
  action: string
  args: Record<string, unknown>
  ok: boolean
  observation: string
  meta?: {
    images?: ToolImage[]
    hit_count?: number
    query?: string
    [k: string]: unknown
  }
}

export interface AgentChatReply {
  ok: boolean
  answer: string
  error: string
  steps: number
  tool_trace: ToolTraceEntry[]
}

export const agentToolsApi = {
  listTools(): Promise<ToolsList> {
    return call<ToolsList>(`${BASE}/tools`)
  },
  getMounts(sid: string): Promise<MountsSnapshot> {
    return call<MountsSnapshot>(`${BASE}/${sid}/tools`)
  },
  setMounts(sid: string, body: {
    enable?: string[]; add?: string[]; remove?: string[];
  }): Promise<MountsSnapshot> {
    return call<MountsSnapshot>(`${BASE}/${sid}/tools`, {
      method: "POST", body: JSON.stringify(body),
    })
  },
  chat(sid: string, body: {
    text: string; provider?: string; model?: string; domains?: string[];
  }): Promise<AgentChatReply> {
    return call<AgentChatReply>(`${BASE}/${sid}/chat`, {
      method: "POST", body: JSON.stringify(body),
    })
  },
}
