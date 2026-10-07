/** 监控 API 客户端 */
export interface KpiSummary {
  window_hours: number
  total_calls: number
  success_rate: number
  avg_latency_ms: number
  p95_latency_ms: number
  total_tokens: number
  total_cost_usd: number
  online_calls: number
  offline_calls: number
}

export interface TrendPoint {
  bucket: string
  calls: number
  tokens: number
  cost: number
  avg_latency_ms: number
}

export interface ModelStat {
  model: string
  provider: string
  calls: number
  success_rate: number
  tokens: number
  cost_usd: number
  avg_latency_ms: number
}

async function _j<T>(path: string): Promise<T> {
  const r = await fetch(path)
  if (!r.ok) throw new Error(`${r.status}`)
  return r.json()
}

export const monitorApi = {
  summary: (h: number) => _j<KpiSummary>(`/api/monitor/summary?hours=${h}`),
  trend: (h: number, g: "hour" | "day" = "hour") =>
    _j<TrendPoint[]>(`/api/monitor/trend?hours=${h}&granularity=${g}`),
  byModel: (h: number) => _j<ModelStat[]>(`/api/monitor/by-model?hours=${h}`),
  calls: (limit = 100) => _j<any[]>(`/api/monitor/calls?limit=${limit}`),
  clear: () => fetch("/api/monitor/calls", { method: "DELETE" }).then(r => r.json()),
}
