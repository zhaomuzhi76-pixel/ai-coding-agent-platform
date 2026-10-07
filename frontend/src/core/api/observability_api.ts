import { request } from "../http/http_client"
import type {
  AlertEvent,
  ObservabilitySummary,
  SpanInfo,
} from "../contracts/observability"

interface Envelope<T> {
  ok: boolean
  data?: T
  error?: { code: string; message: string; detail?: string }
}

async function call<T>(path: string): Promise<T> {
  const payload = await request<Envelope<T>>(path)
  if (!payload.ok || payload.data === undefined) {
    const msg = payload.error
      ? `${payload.error.code}: ${payload.error.message}`
      : "unknown error"
    throw new Error(msg)
  }
  return payload.data
}

export const observabilityApi = {
  summary(): Promise<ObservabilitySummary> {
    return call("/observability/summary")
  },
  spans(limit = 200): Promise<{ total: number; spans: SpanInfo[] }> {
    return call(`/observability/spans?limit=${limit}`)
  },
  byName(
    name: string,
  ): Promise<{
    name: string
    count: number
    summary: {
      count: number
      p50: number
      p95: number
      p99: number
      max: number
    }
    spans: SpanInfo[]
  }> {
    return call(
      `/observability/spans/by-name/${encodeURIComponent(name)}`,
    )
  },
  errors(): Promise<{ errors: SpanInfo[] }> {
    return call("/observability/errors")
  },
  alerts(): Promise<{ events: AlertEvent[] }> {
    return call("/observability/alerts")
  },
  report(buckets = 8): Promise<{ data: unknown; text: string }> {
    return call(`/observability/report?buckets=${buckets}`)
  },
  reset(): Promise<{ reset: boolean }> {
    return request<Envelope<{ reset: boolean }>>(
      "/observability/reset",
      { method: "POST" },
    ).then((p) => p.data ?? { reset: false })
  },
}
