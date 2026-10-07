/* FinetunePage 辅助常量 + 格式化函数。 */

export const STATE_TONE: Record<string, "info" | "success" | "warning" | "danger" | "muted"> = {
  pending: "info",
  running: "warning",
  succeeded: "success",
  failed: "danger",
  cancelled: "muted",
}

export const STATE_LABEL: Record<string, string> = {
  pending: "等待中",
  running: "进行中",
  succeeded: "已完成",
  failed: "失败",
  cancelled: "已取消",
}

export function fmtTime(ts: number): string {
  if (!ts) return "—"
  const d = new Date(ts * 1000)
  const h = String(d.getHours()).padStart(2, "0")
  const m = String(d.getMinutes()).padStart(2, "0")
  return `${h}:${m}`
}

export function fmtSeconds(s: number): string {
  if (s < 60) return `${s.toFixed(0)}s`
  if (s < 3600) return `${(s / 60).toFixed(1)}m`
  return `${(s / 3600).toFixed(1)}h`
}
