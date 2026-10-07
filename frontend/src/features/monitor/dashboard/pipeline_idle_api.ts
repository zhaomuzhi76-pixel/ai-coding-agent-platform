/** Pipeline 空闲回收 API 客户端 */

export interface PipelineSnapshot {
  task_idle: boolean
  hw_idle: boolean
  hw_block_reason: string
  hw_streak: number
  idle_since: number | null
  last_release_ts: number
  last_block_reason: string
  scheduler_active: boolean
  config: {
    grace_s: number
    recheck_s: number
    consecutive: number
    gpu_util_th: number
    cpu_pct_th: number
    min_release_interval_s: number
    retention_days: number
  }
  snapshot: {
    cpu: { percent: number; cores: number; load_1min: number }
    mem: { available_mb: number; percent: number; total_mb: number }
    gpu: { ok: boolean; used_mb: number; util: number; temp_c: number }
  } | null
  db_path: string
  stats_24h: { count: number; total_vram_freed_mb: number; last_ts: number }
}

export interface ReleaseItem {
  id: number
  ts: number
  reasons: string[]
  freed: string[]
  delta_vram_mb: number
  delta_cpu_pct: number
  delta_mem_pct: number
  trigger: string
}

export interface ReleaseHistory {
  hours: number
  items: ReleaseItem[]
  stats: { count: number; total_vram_freed_mb: number; last_ts: number }
}

async function _j<T>(path: string): Promise<T> {
  const r = await fetch(path)
  const body = await r.json()
  if (!body.ok) throw new Error(body.error || `HTTP ${r.status}`)
  return body.data as T
}

export const pipelineIdleApi = {
  idleStats: () => _j<PipelineSnapshot>("/api/rag/pipeline/idle-stats"),
  releaseHistory: (hours = 24, limit = 20) =>
    _j<ReleaseHistory>(
      `/api/rag/pipeline/release-history?hours=${hours}&limit=${limit}`),
  purgeHistory: (days = 0) =>
    fetch("/api/rag/pipeline/purge-history", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ days }),
    }).then(r => r.json()),
  /** 读完整 config（用于 merge 语义） */
  getConfig: async (): Promise<Record<string, unknown>> => {
    const r = await fetch("/api/rag/config")
    const body = await r.json()
    return body.config || {}
  },
  /** 保存完整 config */
  saveConfig: async (cfg: Record<string, unknown>): Promise<void> => {
    await fetch("/api/rag/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cfg),
    })
  },
}
