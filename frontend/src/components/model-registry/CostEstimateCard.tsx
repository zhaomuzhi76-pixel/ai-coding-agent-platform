/** 成本预估卡片 */
import { useEffect, useState } from "react"

interface RoleCost {
  role: string; model: string; provider: string; calls: number
  input_tokens: number; output_tokens: number
  cost_usd: number; is_local: boolean
}
interface Estimate { total_usd: number; roles: RoleCost[] }

const ROLE_LABEL: Record<string, string> = {
  intent: "意图理解", plan: "任务规划", code: "代码生成",
  review: "代码审查", complex: "复杂推理",
}

export function CostEstimateCard() {
  const [data, setData] = useState<Estimate | null>(null)

  useEffect(() => {
    fetch("/api/model-registry/cost-estimate")
      .then((r) => r.ok ? r.json() : null)
      .then((d) => setData(d?.data ?? d))
      .catch(() => {})
  }, [])

  if (!data) return null

  return (
    <div className="mr-cost-card">
      <div className="mr-cost-head">
        <span className="mr-cost-title">💰 跑一次任务的预估成本</span>
        <span className="mr-cost-total">
          ${data.total_usd.toFixed(4)}
        </span>
      </div>
      <table className="mr-cost-table">
        <thead>
          <tr><th>角色</th><th>模型</th><th>调用</th><th>Tokens</th><th>费用</th></tr>
        </thead>
        <tbody>
          {data.roles.map((r) => (
            <tr key={r.role}>
              <td>{ROLE_LABEL[r.role] ?? r.role}</td>
              <td className="mr-mono">{r.model}</td>
              <td>{r.calls}x</td>
              <td>{(r.input_tokens + r.output_tokens).toLocaleString()}</td>
              <td className={r.is_local ? "mr-muted" : "mr-cost-val"}>
                {r.is_local ? "免费" : `$${r.cost_usd.toFixed(4)}`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mr-cost-note">
        基于典型任务假设：intent×1, plan×1, code×3, review×1, complex×1
      </div>
    </div>
  )
}
export default CostEstimateCard
