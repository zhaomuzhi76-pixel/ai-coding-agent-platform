/** GPU 详细任务面板：每进程显存 + 利用率。 */
import { useEffect, useState } from "react"

export function GpuDetailDrawer({ onClose }: { onClose: () => void }) {
  const [d, setD] = useState<any>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    const load = async () => {
      try {
        const r = await fetch("/api/system/gpu-detail")
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const j = await r.json()
        if (alive) { setD(j.data ?? j); setErr(null) }
      } catch (e) { if (alive) setErr(String(e)) }
    }
    load()
    const t = window.setInterval(load, 2000)
    return () => { alive = false; window.clearInterval(t) }
  }, [])

  const gpu = d ?? {}
  const procs: any[] = gpu.processes ?? []
  const sum = gpu.summary ?? {}

  const fmtTime = (ts: number) => {
    if (!ts) return "-"
    const dt = new Date(ts * 1000)
    const pad = (n: number) => String(n).padStart(2, "0")
    return `${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`
  }

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
            <div style={{ fontSize: 15, fontWeight: 600 }}>
              🎮 GPU 详细任务
            </div>
            <div style={{ fontSize: 11, opacity: 0.55, marginTop: 4 }}>
              {gpu.name ?? "未知"} · 每 2 秒刷新
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

          <div style={{
            display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
            gap: 12, marginBottom: 18,
          }}>
            {[
              { label: "显存占用", value: `${sum.vram_used_mb ?? 0} MB`, sub: `${sum.vram_percent ?? 0}%`, color: "#e29e4a" },
              { label: "显存总量", value: `${sum.vram_total_mb ?? 0} MB`, sub: "", color: "#7aa2f7" },
              { label: "GPU 利用率", value: `${gpu.util ?? 0}%`, sub: `${gpu.temp_c ?? 0}°C`, color: "#4fd69a" },
              { label: "进程数", value: `${sum.process_count ?? 0}`, sub: `${sum.process_vram_mb ?? 0} MB 已归属`, color: "#a78bfa" },
            ].map((x) => (
              <div key={x.label} className="ind-card"
                   style={{ padding: 12, borderTop: `3px solid ${x.color}` }}>
                <div style={{ fontSize: 11, opacity: 0.6 }}>{x.label}</div>
                <div style={{ fontSize: 16, fontWeight: 600,
                              marginTop: 4, color: x.color }}>{x.value}</div>
                {x.sub && <div style={{ fontSize: 10, opacity: 0.5,
                                        marginTop: 2 }}>{x.sub}</div>}
              </div>
            ))}
          </div>

          <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8,
                        opacity: 0.85 }}>
            📋 占用 GPU 的进程（{procs.length}）
          </div>

          {procs.length === 0 && (
            <div style={{ padding: 30, textAlign: "center",
                          opacity: 0.5, fontSize: 12 }}>
              ✅ 当前无进程占用 GPU
            </div>
          )}

          {procs.map((p) => (
            <div key={p.pid} className="ind-card"
                 style={{ padding: 12, marginBottom: 8 }}>
              <div style={{ display: "flex", gap: 12,
                            alignItems: "center", flexWrap: "wrap",
                            marginBottom: 6 }}>
                <span style={{ fontFamily: "monospace",
                               color: "#7aa2f7", fontSize: 13 }}>
                  PID {p.pid}
                </span>
                <span style={{ fontSize: 12 }}>{p.user || "-"}</span>
                <span style={{
                  marginLeft: "auto", fontSize: 12, fontWeight: 600,
                  color: "#e29e4a",
                }}>
                  🎮 {p.vram_mb} MB
                </span>
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
                <span>RSS {p.rss_mb ?? 0} MB</span>
                <span>CPU {p.cpu_percent?.toFixed(1) ?? 0}%</span>
                <span>启动 {fmtTime(p.create_time)}</span>
                <span>{p.status}</span>
              </div>
            </div>
          ))}

          {sum.other_vram_mb > 0 && (
            <div style={{
              marginTop: 12, padding: 10, fontSize: 11,
              background: "rgba(118,169,255,.05)", borderRadius: 6,
              opacity: 0.75,
            }}>
              ℹ️ 另有 <b>{sum.other_vram_mb} MB</b> 显存未归属进程（Paddle/驱动缓存）
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default GpuDetailDrawer
