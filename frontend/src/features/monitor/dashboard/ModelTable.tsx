/** 按模型分组的统计表 */
import type { ModelStat } from "./api"

interface Props { rows: ModelStat[] }

export function ModelTable({ rows }: Props) {
  if (rows.length === 0) {
    return <div className="mon-empty">暂无模型调用记录</div>
  }
  return (
    <table className="mon-table">
      <thead>
        <tr>
          <th>模型</th>
          <th>Provider</th>
          <th>调用</th>
          <th>成功率</th>
          <th>Tokens</th>
          <th>平均延迟</th>
          <th>费用</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.model + r.provider}>
            <td className="mon-mono">{r.model}</td>
            <td className="mon-muted">{r.provider}</td>
            <td>{r.calls}</td>
            <td>{(r.success_rate * 100).toFixed(1)}%</td>
            <td>{r.tokens.toLocaleString()}</td>
            <td>{r.avg_latency_ms}ms</td>
            <td className={r.cost_usd > 0 ? "mon-cost" : "mon-muted"}>
              ${r.cost_usd.toFixed(4)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default ModelTable
