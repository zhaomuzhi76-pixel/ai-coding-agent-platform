/** Benchmark 报告详情 Modal（异步拉详情 + 领域能力矩阵） */
import { useEffect, useState } from "react"
import type { BenchmarkRunSummary } from "../../../core/api/benchmark_api"

interface DomainStat {
  domain: string
  score: number
  passed: number
  total: number
}

interface Props {
  run: BenchmarkRunSummary
  categoryLabel: Record<string, string>
  onClose: () => void
  onDownload: (rid: string, model: string) => void
}

function fmt(v: number): string {
  return (v > 1 ? v : v * 100).toFixed(0)
}

export function RunDetailModal({ run, categoryLabel, onClose, onDownload }: Props) {
  const [cases, setCases] = useState<any[]>([])
  const [byDomain, setByDomain] = useState<Record<string, DomainStat>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    fetch(`/api/providers/benchmark/runs/${encodeURIComponent(run.run_id)}`)
      .then((r) => r.ok ? r.json() : Promise.reject(r.statusText))
      .then((d) => {
        const data = d?.data ?? d
        setCases(data.cases ?? [])
      })
      .catch(() => setCases([]))
      .finally(() => setLoading(false))

    fetch(`/api/providers/benchmark/runs/${encodeURIComponent(run.run_id)}/summary`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => {
        const s = d?.data ?? d
        if (s?.by_domain) setByDomain(s.by_domain)
      })
      .catch(() => {})
  }, [run.run_id])

  const elapsed = ((run.finished_at - run.started_at) * 1000).toFixed(0)
  const domains = Object.values(byDomain)

  return (
    <div className="bm-modal-mask" onClick={onClose}>
      <div className="bm-modal" onClick={(e) => e.stopPropagation()}>
        <div className="bm-modal-head">
          <h3>报告详情</h3>
          <button className="bm-btn-mini" onClick={onClose}>✕</button>
        </div>
        <div className="bm-modal-body">
          <div className="bm-detail-head">
            <span className="bm-mono">{run.model}</span>
            <span className="bm-muted"> · {run.provider}</span>
            <span style={{ marginLeft: "auto" }}>
              总分 <b className={run.score >= 70 ? "bm-ok" : "bm-warn"}>
                {fmt(run.score)}
              </b>
            </span>
          </div>
          <div className="bm-detail-meta">
            <span>Run ID: <code>{run.run_id}</code></span>
            <span>通过: {run.passed_count}/{run.case_count}</span>
            <span>耗时: {elapsed}ms</span>
            <span>{new Date(run.started_at * 1000).toLocaleString()}</span>
          </div>

          {/* 领域能力矩阵 */}
          <h4 style={{ fontSize: 12, color: "#9a9aa0", marginTop: 16 }}>
            能力领域（{domains.length}）
          </h4>
          {domains.length > 0 ? (
            <div className="bm-domain-grid">
              {domains.map((d) => (
                <div key={d.domain} className="bm-domain-card">
                  <div className="bm-domain-name">{d.domain}</div>
                  <div className="bm-domain-score"
                       style={{ color: d.score >= 70 ? "#22c55e"
                                      : d.score >= 40 ? "#f59e0b" : "#ef4444" }}>
                    {d.score.toFixed(0)}
                  </div>
                  <div className="bm-domain-sub">{d.passed}/{d.total} 通过</div>
                  <div className="bm-domain-bar">
                    <div style={{
                      width: `${d.score}%`,
                      background: d.score >= 70 ? "#22c55e"
                                : d.score >= 40 ? "#f59e0b" : "#ef4444",
                    }} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="bm-muted">领域数据未生成</p>
          )}

          {/* 用例明细 */}
          <h4 style={{ fontSize: 12, color: "#9a9aa0", marginTop: 16 }}>
            用例明细（{cases.length}）
          </h4>
          {loading ? (
            <p className="bm-muted">加载中…</p>
          ) : cases.length > 0 ? (
            <table className="bm-table">
              <thead>
                <tr>
                  <th>用例</th><th>类别</th><th>通过</th>
                  <th>分数</th><th>延迟</th><th>备注</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((c: any) => (
                  <tr key={c.case_id}>
                    <td>{c.name}</td>
                    <td className="bm-muted">
                      {categoryLabel[c.category] ?? c.category}
                    </td>
                    <td>{c.passed ? "✅" : "❌"}</td>
                    <td>{fmt(c.score)}</td>
                    <td className="bm-mono">{c.latency_ms?.toFixed(0)}ms</td>
                    <td className="bm-muted bm-small">
                      {c.note || c.evidence || ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="bm-muted">无逐用例数据</p>
          )}
        </div>
        <div className="bm-modal-actions">
          <button className="bm-btn"
                  onClick={() => onDownload(run.run_id, run.model)}>
            下载报告
          </button>
          <button className="bm-btn bm-btn-secondary" onClick={onClose}>关闭</button>
        </div>
      </div>
    </div>
  )
}

export default RunDetailModal
