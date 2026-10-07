/**
 * RAG Pipeline 空闲回收 —— 紧凑入口。
 * 点击「详情」→ 弹出覆盖式 Drawer。
 */
import { useCallback, useEffect, useState } from "react"
import { pipelineIdleApi, type PipelineSnapshot } from "../dashboard/pipeline_idle_api"
import { PipelineIdleDrawer } from "./PipelineIdleDrawer"

function fmtAge(ts: number): string {
  if (!ts || ts <= 0) return "从未"
  const age = Math.max(0, Date.now() / 1000 - ts)
  if (age < 60) return `${Math.round(age)}秒前`
  if (age < 3600) return `${Math.round(age / 60)}分钟前`
  if (age < 86400) return `${Math.round(age / 3600)}小时前`
  return `${Math.round(age / 86400)}天前`
}

export function PipelineIdlePanel() {
  const [stats, setStats] = useState<PipelineSnapshot | null>(null)
  const [open, setOpen] = useState(false)

  const refresh = useCallback(async () => {
    try { setStats(await pipelineIdleApi.idleStats()) } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    void refresh()
    const id = window.setInterval(refresh, 15_000)
    return () => window.clearInterval(id)
  }, [refresh])

  const bothIdle = !!stats?.task_idle && !!stats?.hw_idle
  const s24 = stats?.stats_24h ?? { count: 0, total_vram_freed_mb: 0, last_ts: 0 }
  const gpuMb = stats?.snapshot?.gpu?.used_mb ?? 0

  return (
    <>
      <div className="ind-card" style={{
        padding: "10px 14px", marginBottom: 12,
        display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap",
      }}>
        <span style={{ fontSize: 13, fontWeight: 600 }}>
          ⚙️ RAG Pipeline 空闲回收
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%",
                         background: bothIdle ? "#22c55e" : "#f59e0b",
                         boxShadow: `0 0 6px ${bothIdle ? "#22c55e" : "#f59e0b"}` }} />
          <span style={{ fontSize: 12, color: bothIdle ? "#22c55e" : "#f59e0b" }}>
            {bothIdle ? "空闲" : "忙碌"}
          </span>
        </span>
        <span style={{ fontSize: 11, color: "var(--text-soft)" }}>
          24h 释放 <b style={{ color: "#22c55e" }}>{s24.count}</b> 次 · 
          <b style={{ color: "#22c55e", marginLeft: 4 }}>
            {(s24.total_vram_freed_mb / 1024).toFixed(2)} GB
          </b>
        </span>
        <span style={{ fontSize: 11, color: "var(--text-soft)" }}>
          GPU {gpuMb} MB · 最近释放 {fmtAge(s24.last_ts)}
        </span>
        <button className="ind-btn" style={{ marginLeft: "auto" }}
                onClick={() => setOpen(true)}>
          详情 →
        </button>
      </div>
      {open && <PipelineIdleDrawer onClose={() => setOpen(false)} />}
    </>
  )
}

export default PipelineIdlePanel
