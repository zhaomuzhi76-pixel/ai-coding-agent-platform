/** 历史 job 快照（localStorage，刷新后立即渲染） */
export interface CachedJob {
  jobId: string
  filename: string
  sizeBytes: number
  status: string
  progress?: { phase: string; current: number; total: number; percent: number }
  error?: string
  chunks: number
  elapsedMs: number
  cachedAt?: number
}

const KEY = "biancheng.rag.upload.cache"
const MAX_AGE_MS = 24 * 60 * 60 * 1000

export function saveJobCache(items: CachedJob[]): void {
  try {
    const trimmed = items.slice(0, 100)
    localStorage.setItem(KEY, JSON.stringify(trimmed))
  } catch { /* ignore */ }
}

export function loadJobCache(): CachedJob[] {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return []
    const arr: CachedJob[] = JSON.parse(raw)
    const now = Date.now()
    return arr.filter((c) => !c.cachedAt || now - c.cachedAt < MAX_AGE_MS)
  } catch { return [] }
}

export function clearJobCache(): void {
  try { localStorage.removeItem(KEY) } catch { /* ignore */ }
}
