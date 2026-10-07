import { useEffect, useState } from "react"
import {
  probeBackend,
  sourceLabel,
  type BackendStatus,
} from "../../../core/api/backend_client"
import { INTERVALS } from "../../../core/config/intervals"

export function BackendStatusBadge() {
  const [status, setStatus] = useState<BackendStatus | null>(null)

  useEffect(() => {
    let cancelled = false
    const tick = async () => {
      const s = await probeBackend()
      if (!cancelled) setStatus(s)
    }
    void tick()
    const id = window.setInterval(tick, INTERVALS.slow)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [])

  const color = !status
    ? "#77869a"
    : status.reachable
      ? "#4fd69a"
      : "#ef8585"

  const label = !status
    ? "连接中…"
    : status.reachable
      ? `后端在线 (${sourceLabel(status.source)}, ${status.latencyMs}ms)`
      : `后端离线 · ${sourceLabel(status.source)}`

  return (
    <div
      className="backend-status-badge"
      title={status?.url ?? ""}
      data-source={status?.source ?? "unknown"}
    >
      <span
        className="backend-status-dot"
        style={{ background: color }}
      />
      <span className="backend-status-text">{label}</span>
    </div>
  )
}
