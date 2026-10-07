/** 单模型能力总结卡片 */
import { useEffect, useState } from "react"

interface Summary {
  model: string
  provider: string
  overall_score: number
  verdict: string
  by_category: Record<string, number>
  strongest: string
  weakest: string
  failed_cases: string[]
  passed_count: number
  case_count: number
  summary: string
}

interface Props { runId: string }

const CAT_LABEL: Record<string, string> = {
  latency: "响应速度",
  stability: "稳定性",
  capability: "综合能力",
  cost: "性价比",
}

export function BenchmarkSummary({ runId }: Props) {
  const [s, setS] = useState<Summary | null>(null)
  const [err, setErr] = useState("")

  useEffect(() => {
    if (!runId) return
    fetch(`/api/providers/benchmark/runs/${encodeURIComponent(runId)}/summary`)
      .then((r) => r.ok ? r.json() : Promise.reject(r.statusText))
      .then((d) => setS(d?.data ?? d))
      .catch((e) => setErr(String(e)))
  }, [runId])

  if (err) return <div className="bs-card bs-err">总结加载失败: {err}</div>
  if (!s) return <div className="bs-card bs-loading">总结生成中…</div>

  const tone = s.overall_score >= 0.8 ? "great"
              : s.overall_score >= 0.6 ? "good"
              : s.overall_score >= 0.4 ? "mid" : "low"

  return (
    <div className={`bs-card bs-${tone}`}>
      <div className="bs-head">
        <span className="bs-verdict">{s.verdict}</span>
        <span className="bs-score">{(s.overall_score * 100).toFixed(0)}</span>
        <span className="bs-pass">{s.passed_count}/{s.case_count}</span>
      </div>
      <div className="bs-summary">{s.summary}</div>
      <div className="bs-cats">
        {Object.entries(s.by_category).map(([k, v]) => (
          <div key={k} className="bs-cat">
            <span className="bs-cat-label">{CAT_LABEL[k] ?? k}</span>
            <span className="bs-cat-val" style={{
              color: v >= 0.7 ? "#22c55e" : v >= 0.4 ? "#f59e0b" : "#ef4444"
            }}>{(v * 100).toFixed(0)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default BenchmarkSummary
