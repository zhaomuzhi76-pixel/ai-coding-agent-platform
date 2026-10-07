/**
 * Chatbot HTTP 客户端。职责：唯一网络出口。
 * 不持有状态、不做选择器逻辑、不做多模态判定。
 */
import { apiBase } from "../config/runtime"
const BASE = `${apiBase()}/chatbot`

export interface ModelItem {
  id: string
  provider: string
  kind: "llm" | "image_gen" | "embedding" | "rerank"
  display: string
  input_modalities?: string[]
  output_modalities?: string[]
  dim?: number
}

export interface ModelGroups {
  llm: ModelItem[]
  image_gen: ModelItem[]
  embedding: ModelItem[]
  rerank: ModelItem[]
}

export interface ImageOut {
  id: string
  mime: string
  source: "generated" | "retrieved" | "input_echo"
  url?: string
  b64?: string
  alt_text?: string
}

export interface ChatResponse {
  text: string
  images: ImageOut[]
  meta: Record<string, unknown>
}

export interface ChatReply {
  response: ChatResponse
  domain: string
  output_mode: string
  reason: string
  binding: { llm_id: string | null; image_gen_id: string | null }
  default_notes: string[]
}

export interface SelectionBody {
  llm_id?: string | null
  image_gen_id?: string | null
}

export interface SelectionSnapshot {
  llm_id: string | null
  image_gen_id: string | null
  embedding_id?: string | null
  rerank_id?: string | null
}

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  })
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return (await r.json()) as T
}

export const chatbotApi = {
  async listModels(): Promise<ModelGroups> {
    const data = await jsonFetch<{ groups: ModelGroups }>(`${BASE}/models`)
    return data.groups
  },
  async getSelection(sessionId: string): Promise<SelectionSnapshot> {
    return jsonFetch<SelectionSnapshot>(`${BASE}/${sessionId}/selection`)
  },
  async setSelection(sessionId: string, body: SelectionBody): Promise<SelectionSnapshot> {
    return jsonFetch<SelectionSnapshot>(`${BASE}/${sessionId}/selection`, {
      method: "POST",
      body: JSON.stringify(body),
    })
  },
  async chat(sessionId: string, body: {
    text?: string; images?: string[]; audios?: string[]; want_image?: boolean
  }): Promise<ChatReply> {
    return jsonFetch<ChatReply>(`${BASE}/${sessionId}/chat`, {
      method: "POST",
      body: JSON.stringify(body),
    })
  },
}
