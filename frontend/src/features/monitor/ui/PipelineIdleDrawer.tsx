/**
 * RAG Pipeline 空闲回收 —— 覆盖式详情 Drawer。
 * 模式对齐 GpuDetailDrawer（遮罩 + 居中面板）。
 */
import { useCallback, useEffect, useState } from "react"
import {
  pipelineIdleApi,
  type PipelineSnapshot,
  type ReleaseHistory,
} from "../dashboard/pipeline_idle_api"

const RETENTION_OPTIONS = [30, 60, 90] as const

function fmtTs(ts: number): string {
  if (!ts || ts <= 0) return "—"
  const d = new Date(ts * 1000)
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
         `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function KpiCell({ label, value, tone }: {
  label: string; value: string; tone: string
}) {
  return (
    <div style={{ padding: "10px 12px", borderRadius: 6,
                  background: "rgba(255,255,255,.03)",
                  border: "1px solid rgba(255,255,255,.06)" }}>
      <div style={{ fontSize: 11, color: "var(--text-soft)",
                    marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 600,
                    color: tone, fontFamily: "monospace" }}>{value}</div>
    </div>
  )
}

export function PipelineIdleDrawer({ onClose }: { onClose: () => void }) {
  const [stats, setStats] = useState<PipelineSnapshot | null>(null)
  const [history, setHistory] = useState<ReleaseHistory | null>(null)
  const [err, setErr] = useState("")
  const [saving, setSaving] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const [s, h] = await Promise.all([
        pipelineIdleApi.idleStats(),
        pipelineIdleApi.releaseHistory(24, 30),
      ])
      setStats(s); setHistory(h); setErr("")
    } catch (e) {
      setErr(String(e))
    }
  }, [])

  useEffect(() => {
    void refresh()
    const id = window.setInterval(refresh, 5000)
    return () => window.clearInterval(id)
  }, [refresh])

  const setRetention = useCallback(async (days: number) => {
    setSaving(true)
    try {
      const cfg = await pipelineIdleApi.getConfig()
      cfg.idle_history_days = days
      await pipelineIdleApi.saveConfig(cfg)
      await refresh()
    } catch (e) {
      setErr(String(e))
    } finally {
      setSaving(false)
    }
  }, [refresh])

  const snap = stats?.snapshot
  const retention = stats?.config?.retention_days ?? 60
  const s24 = history?.stats ?? { count: 0, total_vram_freed_mb: 0, last_ts: 0 }

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
        {/* 头部 */}
        <div style={{
          padding: "14px 20px",
          borderBottom: "1px solid rgba(118,169,255,.15)",
          display: "flex", justifyContent: "space-between",
          alignItems: "center",
        }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600 }}>
              ⚙️ RAG Pipeline 空闲回收
            </div>
            <div style={{ fontSize: 11, opacity: 0.55, marginTop: 4 }}>
              {stats?.scheduler_active ? "✓ 已启用" : "× 未启用"} · 
              每 5 秒刷新 · DB: {stats?.db_path ?? "?"}
            </div>
          </div>
          <button className="ind-btn" onClick={onClose}>✕</button>
        </div>

        {/* 内容区 */}
        <div style={{ flex: 1, overflow: "auto", padding: 20 }}>
          {err && (
            <div style={{ padding: 10, background: "rgba(239,133,133,.1)",
                          color: "#ef8585", borderRadius: 6,
                          fontSize: 12, marginBottom: 12 }}>
              ⚠️ {err}
            </div>
          )}

          {/* KPI 4 卡片 */}
          <div style={{ display: "grid",
                        gridTemplateColumns: "repeat(4, 1fr)",
                        gap: 10, marginBottom: 14 }}>
            <KpiCell label="任务层"
                      value={stats?.task_idle ? "空闲" : "忙碌"}
                      tone={stats?.task_idle ? "#22c55e" : "#f59e0b"} />
            <KpiCell label="硬件层"
                      value={stats?.hw_idle ? "空闲" : "忙碌"}
                      tone={stats?.hw_idle ? "#22c55e" : "#f59e0b"} />
            <KpiCell label="24h 释放次数" value={`${s24.count}`}
                      tone="#7aa2f7" />
            <KpiCell label="24h 释放显存"
                      value={`${(s24.total_vram_freed_mb / 1024).toFixed(2)} GB`}
                      tone="#22c55e" />
          </div>

          {/* 阻塞状态 */}
          <div style={{ fontSize: 12, color: "var(--text-soft)",
                        marginBottom: 14, padding: "10px 12px",
                        background: "rgba(255,255,255,.03)", borderRadius: 6,
                        lineHeight: 1.7 }}>
            <div>
              <b>当前阻塞：</b>
              <span style={{ color: stats?.hw_idle && stats?.task_idle
                              ? "#22c55e" : "#f59e0b",
                            marginLeft: 6, fontFamily: "monospace" }}>
                {stats?.last_block_reason || "无"}
              </span>
            </div>
            <div>
              <b>hw_streak：</b>
              {stats?.hw_streak ?? 0} / {stats?.config?.consecutive ?? "?"}
              {"  "}·<b> grace：</b>{stats?.config?.grace_s ?? "?"}s
              {"  "}·<b> gpu_util 阈值：</b>{stats?.config?.gpu_util_th ?? "?"}%
              {"  "}·<b> cpu 阈值：</b>{stats?.config?.cpu_pct_th ?? "?"}%
            </div>
            {snap && (
              <div>
                <b>实时快照：</b>
                GPU {snap.gpu.used_mb}MB / {snap.gpu.util}% / {snap.gpu.temp_c}℃
                {"  "}·<b> CPU </b>{snap.cpu.percent.toFixed(1)}%
                {"  "}·<b> 内存可用 </b>
                {(snap.mem.available_mb / 1024).toFixed(2)}GB
              </div>
            )}
          </div>

          {/* 保留天数 */}
          <div style={{ display: "flex", alignItems: "center", gap: 8,
                        marginBottom: 14, flexWrap: "wrap" }}>
            <span style={{ fontSize: 12, color: "var(--text-soft)" }}>
              释放历史保留：
            </span>
            {RETENTION_OPTIONS.map((d) => (
              <button key={d}
                      disabled={saving}
                      onClick={() => void setRetention(d)}
                      style={{
                        padding: "5px 16px", fontSize: 12, cursor: "pointer",
                        borderRadius: 4, border: "1px solid",
                        borderColor: retention === d
                          ? "#22c55e" : "rgba(255,255,255,.15)",
                        background: retention === d
                          ? "rgba(34,197,94,.1)" : "transparent",
                        color: retention === d ? "#22c55e" : "var(--text)",
                        opacity: saving ? 0.5 : 1,
                      }}>
                {d} 天
              </button>
            ))}
            <span style={{ fontSize: 11, color: "var(--text-soft)" }}>
              （改后立即生效，无需重启）
            </span>
          </div>

          {/* 释放明细 */}
          <div style={{ fontSize: 12 }}>
            <div style={{ color: "var(--text-soft)", marginBottom: 8,
                          fontWeight: 600 }}>
              最近 {history?.items?.length ?? 0} 次释放：
            </div>
            {(!history?.items || history.items.length === 0) ? (
              <div style={{ padding: 20, textAlign: "center",
                            color: "var(--text-soft)", fontSize: 12 }}>
                暂无释放记录
              </div>
            ) : (
              <div style={{ maxHeight: 260, overflow: "auto",
                            border: "1px solid rgba(255,255,255,.06)",
                            borderRadius: 6 }}>
                {history.items.map((it) => (
                  <div key={it.id}
                        style={{ display: "flex", alignItems: "center",
                                  gap: 12, padding: "8px 12px",
                                  borderBottom: "1px solid rgba(255,255,255,.05)",
                                  fontFamily: "monospace", fontSize: 11 }}>
                    <span style={{ width: 155, color: "var(--text-soft)" }}>
                      {fmtTs(it.ts)}
                    </span>
                    <span style={{ width: 80,
                                    color: it.delta_vram_mb > 0
                                      ? "#22c55e" : "var(--text-soft)",
                                    textAlign: "right" }}>
                      {it.delta_vram_mb >= 0 ? "−" : "+"}
                      {Math.abs(it.delta_vram_mb)} MB
                    </span>
                    <span style={{ color: "#7aa2f7", minWidth: 60 }}>
                      {it.trigger}
                    </span>
                    <span style={{ color: "var(--text-soft)", flex: 1 }}>
                      {it.freed.join(", ") || "—"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

export default PipelineIdleDrawer
