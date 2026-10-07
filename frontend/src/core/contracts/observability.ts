export interface SpanInfo {
  name: string
  span_id: string
  parent_id: string | null
  status: string
  duration_ms: number
  error: string
  attributes: Record<string, unknown>
}

export interface LatencySummary {
  count: number
  p50: number
  p95: number
  p99: number
  max: number
}

export interface AlertEvent {
  alert_id: string
  rule: string
  severity: string
  message: string
  context: Record<string, unknown>
  created_at: number
}

export interface ObservabilitySummary {
  overall: LatencySummary
  spans: number
  errors: number
  alerts: number
}

export interface SpanAggregate {
  name: string
  count: number
  p50: number
  p95: number
  max: number
  errors: number
}
