import { request } from "../http/http_client"

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

export interface TestableModel {
  provider: string
  model: string
  type: string
  display_name: string
  is_local: boolean
  is_healthy: boolean
}

export interface CompareTableRow {
  metric: string
  label: string
  values: string[]
}

export interface CompareResponse {
  table: CompareTableRow[]
  report_text: string
  report_markdown: string
}

export interface BenchmarkCase {
  case_id: string
  name: string
  category: "latency" | "stability" | "capability" | "cost"
  prompt: string
  system: string
  expected: string
  max_tokens: number
  temperature: number
  weight: number
  repeats: number
  judge: string
  stream: boolean
}

export interface BenchmarkCaseResult {
  case_id: string
  name: string
  category: string
  passed: boolean
  score: number
  latency_ms: number
  first_token_ms: number
  cost: number
  input_tokens: number
  output_tokens: number
  note: string
  evidence: string
  attempts: number
  successes: number
  error: string
}

export interface BenchmarkResult {
  provider: string
  model: string
  started_at: number
  finished_at: number
  elapsed_sec: number
  score: number
  rating: string
  by_category: Record<string, number>
  cases: BenchmarkCaseResult[]
  error: string
}

export interface BenchmarkRunSummary {
  run_id: string
  provider: string
  model: string
  started_at: number
  finished_at: number
  score: number
  rating: string
  case_count: number
  passed_count: number
  error: string
}

export interface RunBenchmarkResponse {
  run_id: string
  provider: string
  model: string
  score: number
  rating: string
  elapsed_sec: number
  by_category: Record<string, number>
  passed: number
  total: number
  error: string
}

export const benchmarkApi = {
  testableModels(): Promise<{ models: TestableModel[]; count: number }> {
    return call("/providers/benchmark/models")
  },
  cases(): Promise<{ cases: BenchmarkCase[]; count: number }> {
    return call("/providers/benchmark/cases")
  },
  run(payload: {
    provider: string
    model: string
    case_timeout_sec?: number
    total_timeout_sec?: number
  }): Promise<RunBenchmarkResponse> {
    return call("/providers/benchmark/run", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
  runs(params: { provider?: string; model?: string; limit?: number } = {}): Promise<{
    runs: BenchmarkRunSummary[]
    count: number
  }> {
    const qs = new URLSearchParams()
    if (params.provider) qs.set("provider", params.provider)
    if (params.model) qs.set("model", params.model)
    qs.set("limit", String(params.limit ?? 20))
    return call(`/providers/benchmark/runs?${qs.toString()}`)
  },
  detail(runId: string): Promise<BenchmarkResult> {
    return call(`/providers/benchmark/runs/${encodeURIComponent(runId)}`)
  },
  report(runId: string): Promise<{ run_id: string; report: string }> {
    return call(
      `/providers/benchmark/runs/${encodeURIComponent(runId)}/report`,
    )
  },
  latest(provider: string, model: string): Promise<{
    result: BenchmarkResult | null
  }> {
    const qs = new URLSearchParams({ provider, model })
    return call(`/providers/benchmark/latest?${qs.toString()}`)
  },
  delete(runId: string): Promise<{ deleted: boolean }> {
    return call(`/providers/benchmark/runs/${encodeURIComponent(runId)}`, {
      method: "DELETE",
    })
  },
  runBatch(payload: {
    targets: Array<{ provider: string; model: string }>
    case_timeout_sec?: number
    total_timeout_sec?: number
  }): Promise<{
    results: Array<{
      provider: string
      model: string
      run_id?: string
      score?: number
      rating?: string
      elapsed_sec?: number
      by_category?: Record<string, number>
      passed?: number
      total?: number
      error?: string
    }>
    count: number
  }> {
    return call("/providers/benchmark/run-batch", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
  compare(runIds: string[]): Promise<CompareResponse> {
    return call("/providers/benchmark/compare", {
      method: "POST",
      body: JSON.stringify({ run_ids: runIds }),
    })
  },
  downloadRunReportUrl(runId: string): string {
    return `/api/providers/benchmark/runs/${encodeURIComponent(runId)}/report.txt`
  },

}
