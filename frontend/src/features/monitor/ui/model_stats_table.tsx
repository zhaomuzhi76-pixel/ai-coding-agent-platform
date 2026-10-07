import type { ModelBucket } from "../../../core/contracts/cost"
import { Badge } from "../../../app/ui/industrial"

function fmtCost(v: number): string {
  if (v === 0) return "$0"
  if (v < 0.0001) return `$${v.toExponential(2)}`
  return `$${v.toFixed(4)}`
}

function fmtMs(v: number): string {
  if (v >= 1000) return `${(v / 1000).toFixed(2)}s`
  return `${v.toFixed(0)}ms`
}

function fmtTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`
  return String(n)
}

export function ModelStatsTable(props: {
  models: Record<string, ModelBucket>
}) {
  const entries = Object.entries(props.models).sort(
    (a, b) => b[1].calls - a[1].calls,
  )

  return (
    <div className="ind-table-wrap">
      <table className="ind-table">
        <thead>
          <tr>
            <th>模型</th>
            <th>Provider</th>
            <th style={{ textAlign: "right" }}>调用</th>
            <th style={{ textAlign: "right" }}>成功</th>
            <th style={{ textAlign: "right" }}>错误</th>
            <th style={{ textAlign: "right" }}>Tokens</th>
            <th style={{ textAlign: "right" }}>P50</th>
            <th style={{ textAlign: "right" }}>P95</th>
            <th style={{ textAlign: "right" }}>成本</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([model, b]) => (
            <tr key={model}>
              <td className="ind-table__mono">
                {model}
                {b.is_local && (
                  <span style={{
                    marginLeft: 6, fontSize: 10,
                    color: "#4fd69a",
                  }}>本地</span>
                )}
              </td>
              <td className="ind-table__mono" style={{ color: "var(--muted)" }}>
                {b.provider}
              </td>
              <td className="ind-table__mono" style={{ textAlign: "right" }}>
                {b.calls}
              </td>
              <td className="ind-table__mono" style={{ textAlign: "right" }}>
                {b.success}
              </td>
              <td className="ind-table__mono" style={{ textAlign: "right" }}>
                {b.errors > 0 ? (
                  <Badge tone="danger">{b.errors}</Badge>
                ) : "—"}
              </td>
              <td className="ind-table__mono" style={{ textAlign: "right" }}>
                {fmtTokens(b.input_tokens)}→{fmtTokens(b.output_tokens)}
              </td>
              <td className="ind-table__mono" style={{ textAlign: "right" }}>
                {fmtMs(b.latency_p50)}
              </td>
              <td className="ind-table__mono" style={{ textAlign: "right" }}>
                {fmtMs(b.latency_p95)}
              </td>
              <td
                className="ind-table__mono"
                style={{
                  textAlign: "right",
                  color: b.is_local ? "var(--muted)" : "var(--warning)",
                }}
              >
                {b.is_local ? "—" : fmtCost(b.cost)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
