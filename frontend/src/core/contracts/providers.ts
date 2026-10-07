export interface ProviderModelInfo {
  id: string
  display_name: string
  context_window: number
  max_output: number
  supports_tool_call: boolean
  supports_stream: boolean
  supports_embedding: boolean
  cost_input_per_1k: number
  cost_output_per_1k: number
  strengths: string[]
}

export interface ProviderInfo {
  name: string
  type: string
  display_name: string
  base_url: string
  has_api_key: boolean
  models: ProviderModelInfo[]
}

export interface ModelRef {
  provider: string
  model: string
}

export interface EmbeddingInfo {
  name: string
  provider: string
  model: string
  dimension: number
  default: boolean
}

export interface RerankerInfo {
  name: string
  provider: string
  model: string
  default: boolean
}

export interface VectorStoreInfo {
  driver: string
  path: string
  collection: string
  default_embedding: string
  default_reranker: string
  top_k: number
  rerank_top_k: number
}

export interface ProviderConfig {
  source: string
  default_provider: string
  default_model: string
  providers: ProviderInfo[]
  skipped: string[]
  agent_routing: Record<string, ModelRef[]>
  embeddings: EmbeddingInfo[]
  rerankers: RerankerInfo[]
  vector_store: VectorStoreInfo
}

export interface HealthRecord {
  provider: string
  status: string
  latency_ms: number
  error: string
  checked_at: number
  consecutive_failures: number
}

export interface CostSummary {
  total: {
    calls: number
    cost: number
    input_tokens: number
    output_tokens: number
  }
  by_provider: Record<string, { calls: number; cost: number; errors: number }>
  by_model: Record<string, { calls: number; cost: number; errors: number }>
  by_role: Record<string, { calls: number; cost: number }>
}
