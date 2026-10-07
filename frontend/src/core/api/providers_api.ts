import { request } from "../http/http_client"
import type {
  CostSummary, HealthRecord, ProviderConfig,
} from "../contracts/providers"

interface Envelope<T> {
  ok: boolean
  data?: T
  error?: { code: string; message: string }
}

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const payload = await request<Envelope<T>>(path, init)
  if (!payload.ok || payload.data === undefined) {
    throw new Error(
      payload.error
        ? `${payload.error.code}: ${payload.error.message}`
        : "unknown error",
    )
  }
  return payload.data
}

export interface CallRecord {
  record_id: string
  provider: string
  model: string
  role: string
  input_tokens: number
  output_tokens: number
  cost: number
  latency_ms: number
  success: boolean
  error: string
  created_at: number
  is_local: boolean
}

export interface ProviderUpsertPayload {
  name: string
  type: string
  display_name: string
  base_url: string
  api_key: string
  models: Array<Record<string, unknown>>
}

export interface TestResult {
  success: boolean
  latency_ms?: number
  models_count?: number
  error?: string
  available_models?: string[]
}

export const providersApi = {
  config(): Promise<ProviderConfig> {
    return call("/providers/config")
  },
  health(): Promise<{ records: HealthRecord[]; count: number }> {
    return call("/providers/health")
  },
  cost(): Promise<CostSummary> {
    return call("/providers/cost")
  },
  costStats(days = 7): Promise<CostSummary> {
    return call(`/providers/cost?days=${days}`)
  },
  costSummary(): Promise<CostSummary> {
    return call("/cost/summary")
  },
  costRecent(limit = 50): Promise<{ records: CallRecord[]; count: number }> {
    return call(`/cost/recent?limit=${limit}`)
  },
  rawYaml(): Promise<{ path: string; text: string }> {
    return call("/providers/raw-yaml")
  },
  upsert(payload: ProviderUpsertPayload): Promise<{ saved: boolean; provider: unknown }> {
    return call("/providers/upsert", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
  delete(name: string): Promise<{ deleted: boolean; name: string }> {
    return call(`/providers/${encodeURIComponent(name)}`, {
      method: "DELETE",
    })
  },
  test(payload: {
    type: string
    base_url: string
    api_key: string
    models: Array<Record<string, unknown>>
  }): Promise<TestResult> {
    return call("/providers/test", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
  localModels(name: string, baseUrl = ""): Promise<{
    provider: string
    type: string
    source: string
    models: Array<{ id: string; display_name: string; context_window: number }>
    error?: string
  }> {
    const qs = baseUrl ? `?base_url=${encodeURIComponent(baseUrl)}` : ""
    return call(`/providers/local-models/${encodeURIComponent(name)}${qs}`)
  },
}
