/** L23 审核门 API 客户端。职责：唯一网络出口。
 *  不做 UI、不持状态、不缓存。复用 http_client.request。 */
import { request } from "../http/http_client"

// ── 排序模型门控 ──
export interface RerankerCard {
  model_id: string
  display_name: string
  backend_kind: string
  endpoint: string
  description: string
  weight: number
  tags: string[]
  status: string
  status_label: string
  status_color: string
  selectable: boolean
  selected: boolean
  last_probe_at: string
  last_outcome: string
  last_message: string
  last_latency_ms: number
}

export interface RerankerCardsResp {
  count: number
  passing: number
  selected: string
  cards: RerankerCard[]
}

export interface RerankerSelectableResp {
  current: string
  options: { value: string; label: string; selected: boolean }[]
}

export interface ProbeResp {
  model_id: string
  outcome: string
  message: string
  latency_ms: number
}

export const l23RerankerApi = {
  cards: () => request<RerankerCardsResp>("/config/reranker/cards"),
  selectable: () => request<RerankerSelectableResp>("/config/reranker/selectable"),
  yaml: () => request<{ yaml: string }>("/config/reranker/yaml"),
  probe: (model_id: string) =>
    request<ProbeResp>("/config/reranker/probe", {
      method: "POST",
      body: JSON.stringify({ model_id }),
    }),
  select: (model_id: string) =>
    request<{ model_id: string; selected: boolean; current: string }>(
      "/config/reranker/select",
      { method: "POST", body: JSON.stringify({ model_id }) },
    ),
}

// ── 审核门 ──
export interface DraftChunk {
  chunk_id: string
  content: string
  order: number
  bm25: number
  rerank: number
  fused: number
  rank: number
  bm25_bar: number
  rerank_bar: number
  is_hit: boolean
  selected: boolean
  action: string
}

export interface ReviewPageData {
  job_id: string
  query: string
  total: number
  hit_count: number
  selected_count: number
  actions: { id: string; label: string; style: string }[]
  chunks: DraftChunk[]
  metadata: Record<string, unknown>
}

export interface JobSummary {
  job_id: string
  chunk_count: number
  preview: string
}

export interface JobsResp {
  jobs: JobSummary[]
  count: number
}

export interface SeedResp {
  job_id: string
  chunk_count: number
}

export const l23ReviewApi = {
  listJobs: () => request<JobsResp>("/rag/review/ui/jobs"),

  seed: (job_id: string) =>
    request<SeedResp>("/rag/review/ui/seed", {
      method: "POST",
      body: JSON.stringify({ job_id, texts: [] }),
    }),

  page: (job_id: string, query: string) =>
    request<ReviewPageData>(
      `/rag/review/ui/page?job_id=${encodeURIComponent(job_id)}&query=${encodeURIComponent(query)}`,
    ),

  approve: (job_id: string, approved_ids: string[]) =>
    request<{ job_id: string; action: string; written: number }>(
      `/rag/review/ui/approve?job_id=${encodeURIComponent(job_id)}`,
      {
        method: "POST",
        body: JSON.stringify({
          action: "approve",
          approved_chunk_ids: approved_ids,
          edits: [],
        }),
      },
    ),

  reject: (job_id: string) =>
    request<{ job_id: string; action: string; written: number }>(
      `/rag/review/ui/reject?job_id=${encodeURIComponent(job_id)}`,
      { method: "POST", body: JSON.stringify({}) },
    ),
}


// ── 召回测试 ──
export interface RecallHit {
  chunk_id: string; content: string; source: string; line_no: number
  vector: number; vector_rank: number | null; vector_bar: number
  bm25: number; bm25_rank: number | null; bm25_bar: number
  rerank: number; rerank_rank: number | null; rerank_bar: number
  fused: number; fused_rank: number
}
export interface RecallQueryResp {
  query: string; elapsed_ms: number; params_used: Record<string, unknown>
  counts: { vector: number; bm25: number; fused: number; returned: number }
  reranked: boolean; errors: { vector: string; bm25: string }
  hits: RecallHit[]
}
export interface RecallModelsResp {
  models: { model_id: string; label: string; backend_kind: string; selectable: boolean }[]
  default: string
}
export interface RecallQueryParams {
  query: string; top_k?: number; use_reranker?: boolean
  reranker_model_id?: string; rrf_k?: number
  vector_weight?: number; bm25_weight?: number
}
export const l23RecallApi = {
  models: () => request<RecallModelsResp>("/rag/recall-test/models"),
  query: (p: RecallQueryParams) =>
    request<RecallQueryResp>("/rag/recall-test/query", {
      method: "POST",
      body: JSON.stringify({
        query: p.query, top_k: p.top_k ?? 10,
        use_reranker: p.use_reranker ?? true,
        reranker_model_id: p.reranker_model_id ?? "builtin-qwen3-reranker",
        rrf_k: p.rrf_k ?? 60,
        vector_weight: p.vector_weight ?? 0.7,
        bm25_weight: p.bm25_weight ?? 0.3,
      }),
    }),
}


export interface RecallConfig {
  top_k: number; use_reranker: boolean; reranker_model_id: string
  rrf_k: number; vector_weight: number; bm25_weight: number
}
export const l23RecallConfigApi = {
  get: () => request<{ config: RecallConfig; version: number }>("/rag/recall-test/config"),
  apply: (c: RecallConfig) =>
    request<{ applied: boolean; config: RecallConfig; version: number }>(
      "/rag/recall-test/apply", { method: "POST", body: JSON.stringify(c) }),
  reset: () =>
    request<{ reset: boolean; config: RecallConfig; version: number }>(
      "/rag/recall-test/reset", { method: "POST", body: JSON.stringify({}) }),
}
