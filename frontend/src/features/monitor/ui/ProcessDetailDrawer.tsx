/** 进程排行榜抽屉（CPU / 内存通用）。按 kind 决定排序和标题。 */
import { useEffect, useState } from "react"

interface ProcRow {
  pid: number; name: string; cmd: string; user: string
  cpu_percent: number; rss_mb: number
  create_time: number; status: string
}

export function ProcessDetailDrawer({
  kind, onClose,
}: {
  kind: "cpu" | "memory"
  onClose: () => void
}) {
  const [procs, setProcs] = useState<ProcRow[]>([])
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    const load = async () => {
      try {
        const r = await fetch(`/api/system/processes?sort=${kind}&limit=30`)
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const j = await r.json()
        if (alive) { setProcs(j?.data?.processes ?? []); setErr(null) }
      } catch (e) { if (alive) setErr(String(e)) }
    }
    load()
    const t = window.setInterval(load, 2000)
    return () => { alive = false; window.clearInterval(t) }
  }, [kind])

  const title = kind === "cpu" ? "🖥 CPU 详细任务" : "🧠 内存详细任务"
  const sortLabel = kind === "cpu" ? "CPU 使用率" : "内存 (RSS)"
  const sortColor = kind === "cpu" ? "#7aa2f7" : "#4fd69a"

  const fmtTime = (ts: number) => {
    if (!ts) return "-"
    const dt = new Date(ts * 1000)
    const pad = (n: number) => String(n).padStart(2, "0")
    return `${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`
  }

  const maxVal = Math.max(1, ...procs.map((p) =>
    kind === "cpu" ? p.cpu_percent : p.rss_mb))

  return (
    <>
      <div onClick={onClose} style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,.55)",
        zIndex: 998,
      }} />
      <div style={{
        position: "fixed", top: "8vh", left: "50%",
        transform: "translateX(-50%)",
        width: "min(880px, 92vw)", maxHeight: "84vh",
        background: "#0d1117", borderRadius: 10,
        border: "1px solid rgba(118,169,255,.25)",
        zIndex: 999, display: "flex", flexDirection: "column",
        boxShadow: "0 20px 60px rgba(0,0,0,.6)",
      }}>
        <div style={{
          padding: "14px 20px",
          borderBottom: "1px solid rgba(118,169,255,.15)",
          display: "flex", justifyContent: "space-between",
          alignItems: "center",
        }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600 }}>{title}</div>
            <div style={{ fontSize: 11, opacity: 0.55, marginTop: 4 }}>
              按 {sortLabel} 排序 · 每 2 秒刷新 · Top 30
            </div>
          </div>
          <button className="ind-btn" onClick={onClose}>✕</button>
        </div>

        <div style={{ flex: 1, overflow: "auto", padding: 20 }}>
          {err && (
            <div style={{ padding: 10, background: "rgba(239,133,133,.1)",
                          color: "#ef8585", borderRadius: 6,
                          fontSize: 12, marginBottom: 12 }}>
              加载失败: {err}
            </div>
          )}

          {procs.length === 0 && !err && (
            <div style={{ padding: 30, textAlign: "center",
                          opacity: 0.5, fontSize: 12 }}>
              暂无进程数据
            </div>
          )}

          {procs.map((p, i) => {
            const val = kind === "cpu" ? p.cpu_percent : p.rss_mb
            const pct = (val / maxVal) * 100
            return (
              <div key={p.pid} className="ind-card"
                   style={{ padding: 12, marginBottom: 8 }}>
                <div style={{ display: "flex", gap: 12,
                              alignItems: "center", flexWrap: "wrap",
                              marginBottom: 6 }}>
                  <span style={{
                    width: 22, textAlign: "right",
                    fontFamily: "monospace", opacity: 0.4, fontSize: 11,
                  }}>#{i + 1}</span>
                  <span style={{ fontFamily: "monospace",
                                 color: "#7aa2f7", fontSize: 13 }}>
                    PID {p.pid}
                  </span>
                  <span style={{ fontSize: 12 }}>{p.user || "-"}</span>
                  <span style={{
                    marginLeft: "auto", fontSize: 13, fontWeight: 600,
                    color: sortColor, fontFamily: "monospace",
                  }}>
                    {kind === "cpu"
                      ? `${p.cpu_percent.toFixed(1)}%`
                      : `${p.rss_mb.toFixed(0)} MB`}
                  </span>
                </div>
                {/* 条形图 */}
                <div style={{
                  height: 4, background: "#2a2a2e", borderRadius: 2,
                  overflow: "hidden", marginBottom: 6,
                }}>
                  <div style={{
                    height: "100%", width: `${pct}%`,
                    background: sortColor, transition: "width .4s",
                  }} />
                </div>
                <div style={{
                  fontSize: 11, fontFamily: "monospace", opacity: 0.75,
                  whiteSpace: "nowrap", overflow: "hidden",
                  textOverflow: "ellipsis", marginBottom: 4,
                }} title={p.cmd}>
                  {p.cmd || p.name}
                </div>
                <div style={{ display: "flex", gap: 16, fontSize: 10,
                              opacity: 0.5 }}>
                  <span>RSS {p.rss_mb.toFixed(0)} MB</span>
                  <span>CPU {p.cpu_percent.toFixed(1)}%</span>
                  <span>启动 {fmtTime(p.create_time)}</span>
                  <span>{p.status}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </>
  )
}

export default ProcessDetailDrawer
