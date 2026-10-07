/**
 * 系统资源实时监控面板（CPU / 内存 / GPU / 进程）。
 * CPU / 内存 / GPU 三个卡片可点击 → 弹出详细任务抽屉。
 */
import { useEffect, useState } from "react"
import { GpuDetailDrawer } from "./GpuDetailDrawer"
import { ProcessDetailDrawer } from "./ProcessDetailDrawer"

interface CpuInfo { percent: number; cores: number; load: number[] }
interface MemInfo { total_gb: number; used_gb: number; available_gb: number; percent: number }
interface GpuInfo { ok: boolean; name?: string; vram_used_mb?: number; vram_total_mb?: number;
                    util?: number; temp_c?: number; vram_percent?: number; error?: string }
interface ProcInfo { pid: number; cmd: string; cpu: number; rss_mb: number }
interface Health { cpu?: CpuInfo; memory?: MemInfo; gpu?: GpuInfo; processes?: ProcInfo[] }

type DrawerKind = "cpu" | "memory" | "gpu" | null

function Bar({ pct, color, label }: { pct: number; color: string; label: string }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 4 }}>
        <span>{label}</span>
        <span style={{ fontFamily: "monospace", color }}>{pct.toFixed(1)}%</span>
      </div>
      <div style={{ height: 8, background: "#2a2a2e", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${Math.min(100, pct)}%`,
                      background: color, transition: "width .4s" }} />
      </div>
    </div>
  )
}

function Card({ title, children, color = "#7aa2f7", clickable = false, onClick }: {
  title: string; children: React.ReactNode; color?: string
  clickable?: boolean; onClick?: () => void
}) {
  const inner = (
    <div className="ind-card" style={{ padding: 14,
         borderTop: `3px solid ${color}`, minHeight: 130,
         cursor: clickable ? "pointer" : "default" }}>
      <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 10,
                    opacity: 0.9, color }}>{title}</div>
      {children}
    </div>
  )
  if (!clickable || !onClick) return inner
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => { if (e.key === "Enter") onClick() }}
      style={{ outline: "none" }}
      title="点击查看详细任务"
    >
      {inner}
    </div>
  )
}

export function SystemResourcePanel() {
  const [h, setH] = useState<Health | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [drawer, setDrawer] = useState<DrawerKind>(null)

  useEffect(() => {
    let alive = true
    const tick = async () => {
      try {
        const r = await fetch("/api/system/health")
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const d = await r.json()
        if (alive) { setH(d.data ?? d); setErr(null) }
      } catch (e) {
        if (alive) setErr(String(e))
      }
    }
    tick()
    const t = window.setInterval(tick, 2000)
    return () => { alive = false; window.clearInterval(t) }
  }, [])

  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between",
                    alignItems: "center", marginBottom: 10 }}>
        <span style={{ fontSize: 14, fontWeight: 600 }}>💻 系统资源监控</span>
        <span style={{ fontSize: 11, opacity: 0.5 }}>
          2 秒自动刷新 · 点击卡片查看详情
        </span>
      </div>

      {err && (
        <div style={{ padding: 10, background: "rgba(239,133,133,.1)",
                      color: "#ef8585", borderRadius: 6, fontSize: 12 }}>
          加载失败: {err}
        </div>
      )}

      <div style={{ display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                    gap: 12 }}>
        {/* CPU（可点击） */}
        <Card title="🖥 CPU（点击查看详情）" color="#7aa2f7"
              clickable onClick={() => setDrawer("cpu")}>
          {h?.cpu ? (
            <>
              <Bar pct={h.cpu.percent} color="#7aa2f7" label={`占用 (${h.cpu.cores} 核)`} />
              <div style={{ fontSize: 11, opacity: 0.6, marginTop: 8,
                            fontFamily: "monospace" }}>
                load {h.cpu.load.map(x => x.toFixed(2)).join(" / ")}
              </div>
              <div style={{ fontSize: 10, color: "#7aa2f7",
                            marginTop: 6, opacity: 0.8 }}>
                查看进程排行 →
              </div>
            </>
          ) : <div style={{ opacity: 0.4 }}>加载中...</div>}
        </Card>

        {/* 内存（可点击） */}
        <Card title="🧠 内存（点击查看详情）" color="#4fd69a"
              clickable onClick={() => setDrawer("memory")}>
          {h?.memory ? (
            <>
              <Bar pct={h.memory.percent} color="#4fd69a"
                   label={`${h.memory.used_gb} / ${h.memory.total_gb} GB`} />
              <div style={{ fontSize: 11, opacity: 0.6, marginTop: 8 }}>
                可用 <b style={{ color: "#4fd69a" }}>{h.memory.available_gb} GB</b>
              </div>
              <div style={{ fontSize: 10, color: "#4fd69a",
                            marginTop: 6, opacity: 0.8 }}>
                查看进程排行 →
              </div>
            </>
          ) : <div style={{ opacity: 0.4 }}>加载中...</div>}
        </Card>

        {/* GPU（可点击） */}
        <Card title={`🎮 GPU ${h?.gpu?.ok ? "（点击查看详情）" : "(未检测)"}`}
              color={h?.gpu?.ok ? "#e29e4a" : "#6b7280"}
              clickable={!!h?.gpu?.ok} onClick={() => setDrawer("gpu")}>
          {h?.gpu?.ok ? (
            <>
              <Bar pct={h.gpu.util ?? 0} color="#e29e4a" label="利用率" />
              <Bar pct={h.gpu.vram_percent ?? 0} color="#ec4899"
                   label={`显存 ${(h.gpu.vram_used_mb ?? 0) / 1024}GB / ${(h.gpu.vram_total_mb ?? 0) / 1024}GB`} />
              <div style={{ fontSize: 11, opacity: 0.6, marginTop: 8 }}>
                温度 <b>{h.gpu.temp_c ?? "?"}°C</b>
              </div>
              <div style={{ fontSize: 10, color: "#e29e4a",
                            marginTop: 6, opacity: 0.8 }}>
                查看 GPU 详情 →
              </div>
            </>
          ) : <div style={{ opacity: 0.4 }}>GPU 不可用</div>}
        </Card>

        {/* 关键进程 */}
        <Card title="⚙ 关键进程" color="#a78bfa">
          {h?.processes && h.processes.length > 0 ? (
            <div style={{ display: "grid", gap: 4, fontSize: 11 }}>
              {h.processes.slice(0, 5).map((p) => (
                <div key={p.pid} style={{ display: "flex", gap: 6 }}>
                  <span style={{ opacity: 0.5, fontFamily: "monospace" }}>
                    {p.pid}
                  </span>
                  <span style={{ flex: 1, overflow: "hidden",
                                 textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {p.cmd.split(" ").slice(0, 3).join(" ")}
                  </span>
                  <span style={{ color: p.cpu > 50 ? "#e29e4a" : "#4fd69a",
                                 fontFamily: "monospace" }}>
                    {p.cpu.toFixed(0)}% · {p.rss_mb.toFixed(0)}MB
                  </span>
                </div>
              ))}
            </div>
          ) : <div style={{ opacity: 0.4 }}>无关键进程</div>}
        </Card>
      </div>

      {/* 抽屉 */}
      {drawer === "gpu" && <GpuDetailDrawer onClose={() => setDrawer(null)} />}
      {(drawer === "cpu" || drawer === "memory") && (
        <ProcessDetailDrawer kind={drawer} onClose={() => setDrawer(null)} />
      )}
    </div>
  )
}

export default SystemResourcePanel
