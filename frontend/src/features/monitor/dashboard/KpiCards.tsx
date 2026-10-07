/** KPI 卡片组 */
import type { KpiSummary } from "./api"

interface Props { kpi: KpiSummary | null }

export function KpiCards({ kpi }: Props) {
  if (!kpi) return <div className="mon-kpi-grid"><div className="mon-kpi-card">加载中…</div></div>

  const cards = [
    { label: "总调用", value: kpi.total_calls, unit: "" },
    { label: "成功率", value: (kpi.success_rate * 100).toFixed(1), unit: "%" },
    { label: "平均延迟", value: kpi.avg_latency_ms, unit: "ms" },
    { label: "P95 延迟", value: kpi.p95_latency_ms, unit: "ms" },
    { label: "总 Tokens", value: kpi.total_tokens.toLocaleString(), unit: "" },
    { label: "总费用", value: "$" + kpi.total_cost_usd.toFixed(4), unit: "" },
    { label: "线上调用", value: kpi.online_calls, unit: "" },
    { label: "本地调用", value: kpi.offline_calls, unit: "" },
  ]

  return (
    <div className="mon-kpi-grid">
      {cards.map((c) => (
        <div key={c.label} className="mon-kpi-card">
          <div className="mon-kpi-label">{c.label}</div>
          <div className="mon-kpi-value">
            {c.value}<span className="mon-kpi-unit">{c.unit}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

export default KpiCards
