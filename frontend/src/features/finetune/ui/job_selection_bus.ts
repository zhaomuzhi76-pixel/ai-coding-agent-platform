/**
 * job_selection_bus：JobListPanel 与 JobStreamPanel 之间的选中共振。
 *
 * Owns:
 *   - 单个事件名 + 订阅/发布
 *   - 当前选中 jobId 的只读快照
 *
 * Not:
 *   - 业务状态（面板自己管）
 *   - UI（面板自己渲染）
 *   - 跨页面持久化（只内存）
 */
const EVENT = "finetune:job-selected"

let _current: string | null = null

export function selectJob(jobId: string | null): void {
  _current = jobId
  try {
    window.dispatchEvent(new CustomEvent(EVENT, { detail: jobId }))
  } catch { /* ignore SSR */ }
}

export function onSelectJob(
  cb: (jobId: string | null) => void,
): () => void {
  const handler = (e: Event) => {
    const detail = (e as CustomEvent).detail
    cb((detail as string | null) ?? null)
  }
  if (typeof window !== "undefined") {
    window.addEventListener(EVENT, handler)
    return () => window.removeEventListener(EVENT, handler)
  }
  return () => {}
}

export function getSelectedJob(): string | null {
  return _current
}
