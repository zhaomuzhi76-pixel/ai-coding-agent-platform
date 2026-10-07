/** 最新测试结果 + 用例明细 */
import type { BenchmarkResult } from "../../../core/api/benchmark_api"
import { BenchmarkSummary } from "./BenchmarkSummary"
import { fmtScore } from "./ModelSelectorGrid"

const CATS = ["latency", "stability", "capability", "cost"] as const

interface Props {
  latest: BenchmarkResult
  categoryLabel: Record<string, string>
  bar: (v: number) => React.ReactNode
  caseMetric: (c: any) => string
  onDownload: (rid: string, model: string) => void
}

export function LatestResultSection({
  latest, categoryLabel, bar, caseMetric, onDownload,
}: Props) {
  return (
    <>
      <BenchmarkSummary runId={latest.run_id} />
      <div className="bm-block">
        <div className="bm-block-title">
          最新结果 · {latest.model} ·
          <span className={latest.score >= 70 ? "bm-ok" : "bm-warn"}>
            总分 {fmtScore(latest.score)}
          </span>
          {latest.rating && <span className="bm-tag">{latest.rating}</span>}
          <span className="bm-muted">
            {latest.passed_count}/{latest.case_count} 通过
          </span>
          <button className="bm-btn-mini" style={{ marginLeft: "auto" }}
                  onClick={() => onDownload(latest.run_id, latest.model)}>
            下载
          </button>
        </div>
        <div className="bm-cat-grid">
          {CATS.map((cat) => {
            const cs = latest.cases.filter((c) => c.category === cat)
            if (cs.length === 0) return null
            const avg = cs.reduce((s, c) => s + c.score, 0) / cs.length
            return (
              <div key={cat} className="bm-cat-card">
                <div className="bm-cat-label">{categoryLabel[cat] ?? cat}</div>
                <div className="bm-cat-score">{fmtScore(avg)}</div>
                <div className="bm-cat-bar">{bar(avg)}</div>
              </div>
            )
          })}
        </div>
        <table className="bm-table">
          <thead>
            <tr>
              <th>用例</th><th>类别</th><th>通过</th>
              <th>分数</th><th>延迟</th><th>详情</th>
            </tr>
          </thead>
          <tbody>
            {latest.cases.map((c) => (
              <tr key={c.case_id}>
                <td>{c.name}</td>
                <td className="bm-muted">{categoryLabel[c.category] ?? c.category}</td>
                <td>{c.passed ? "✅" : "❌"}</td>
                <td>{fmtScore(c.score)}</td>
                <td className="bm-mono">{c.latency_ms.toFixed(0)}ms</td>
                <td className="bm-muted bm-small">{caseMetric(c)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

export default LatestResultSection
