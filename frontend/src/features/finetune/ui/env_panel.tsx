/**
 * EnvPanel: 训练环境检测（D）。
 *
 * 职责：
 *   - 展示 torch/cuda/peft/... 安装状态
 *   - GPU 显存 + compute capability
 *   - ollama 是否可用
 *   - "能否真训"判定 + 未装时安装指引
 *
 * 不负责：安装依赖（用户手动）
 */
import { useCallback, useEffect, useState } from "react"

import { finetuneApi } from "../../../core/api/finetune_api"
import type { EnvPackage, EnvReport } from "../../../core/contracts/finetune"
import { Badge, EmptyState } from "../../../app/ui/industrial"

function pkgStatus(p: EnvPackage) {
  if (p.installed) return { tone: "success" as const, text: p.version }
  return { tone: "danger" as const, text: "未装" }
}

export function EnvPanel() {
  const [report, setReport] = useState<EnvReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const r = await finetuneApi.envReport()
      setReport(r); setError(null)
    } catch (e) { setError(String(e)) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { void load() }, [load])

  const gpuLabel = () => {
    if (!report) return "—"
    const g = report.gpu
    if (!g.available) return "不可用"
    return `${g.name} · ${g.vram_total_mb}MB · CUDA ${g.cuda_version}`
  }

  return (
    <section style={{ marginTop: 24 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
        <h3 style={{ fontSize: 13, margin: 0, color: "var(--text-soft)", fontWeight: 500 }}>
          训练环境检测
        </h3>
        {report && (
          <Badge tone={report.ready_for_training ? "success" : "warning"}>
            {report.ready_for_training ? "可训练" : "不可训练"}
          </Badge>
        )}
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          style={{
            padding: "4px 12px", borderRadius: 4, fontSize: 11,
            background: loading ? "#374151" : "#1f6feb",
            color: "#fff", border: 0,
            cursor: loading ? "wait" : "pointer",
          }}
        >
          {loading ? "检测中..." : "刷新"}
        </button>
      </div>

      {error && (
        <div style={{
          padding: "8px 12px", borderRadius: 6, marginBottom: 10,
          background: "rgba(239,133,133,.08)",
          color: "var(--danger)", fontSize: 11,
        }}>{error}</div>
      )}

      {!report ? (
        <EmptyState title="加载中..." icon="◈" />
      ) : (
        <>
          <div className="ind-card" style={{ padding: 12, marginBottom: 12 }}>
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
              gap: 8, fontSize: 11,
            }}>
              <div>
                <div style={{ color: "var(--muted)" }}>GPU</div>
                <div style={{ fontFamily: "ui-monospace, monospace" }}>{gpuLabel()}</div>
              </div>
              <div>
                <div style={{ color: "var(--muted)" }}>显存</div>
                <div style={{ fontFamily: "ui-monospace, monospace" }}>
                  {report.gpu.available ? `${report.gpu.vram_free_mb} / ${report.gpu.vram_total_mb} MB` : "—"}
                </div>
              </div>
              <div>
                <div style={{ color: "var(--muted)" }}>Compute</div>
                <div style={{ fontFamily: "ui-monospace, monospace" }}>
                  {report.gpu.compute_capability || "—"}
                </div>
              </div>
              <div>
                <div style={{ color: "var(--muted)" }}>ollama</div>
                <div style={{ fontFamily: "ui-monospace, monospace" }}>
                  {report.ollama_available ? "✅ 可用" : "❌ 未装"}
                </div>
              </div>
            </div>
          </div>

          <div style={{ marginBottom: 12 }}>
            <div style={{
              fontSize: 11, color: "var(--muted)", marginBottom: 6,
              textTransform: "uppercase", letterSpacing: 0.4,
            }}>依赖包（{report.packages.filter(p => p.installed).length}/{report.packages.length}）</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {report.packages.map((p) => {
                const s = pkgStatus(p)
                return (
                  <span key={p.name} style={{
                    padding: "4px 10px", borderRadius: 6, fontSize: 11,
                    background: p.installed ? "rgba(79,214,154,.08)" : "rgba(239,133,133,.08)",
                    border: "1px solid " + (p.installed ? "rgba(79,214,154,.3)" : "rgba(239,133,133,.3)"),
                    color: p.installed ? "#4fd69a" : "#ef8585",
                    fontFamily: "ui-monospace, monospace",
                  }}>
                    {p.name}{" "}
                    <span style={{ color: "var(--muted)" }}>{s.text}</span>
                  </span>
                )
              })}
            </div>
          </div>

          {report.warnings.length > 0 && (
            <div style={{
              padding: 10, borderRadius: 6, marginBottom: 10,
              background: "rgba(227,184,109,.06)",
              border: "1px solid rgba(227,184,109,.3)",
              fontSize: 11, color: "#e3b86d",
            }}>
              {report.warnings.map((w, i) => <div key={i}>⚠️ {w}</div>)}
            </div>
          )}

          {report.suggestions.length > 0 && (
            <details style={{
              padding: 10, borderRadius: 6,
              background: "rgba(118,169,255,.05)",
              border: "1px solid rgba(118,169,255,.3)",
              fontSize: 11,
            }} open>
              <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
                安装指引（{report.suggestions.length} 步）
              </summary>
              <div style={{ marginTop: 8, fontFamily: "ui-monospace, monospace", color: "var(--text-soft)" }}>
                {report.suggestions.map((s, i) => (
                  <div key={i} style={{ marginBottom: 4 }}># {i+1}. {s}</div>
                ))}
              </div>
            </details>
          )}
        </>
      )}
    </section>
  )
}
