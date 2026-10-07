/** 大模型能力测试面板（Dify 风格）—— 组合子组件，主控状态 */
import { useState } from "react"

import type {
  BenchmarkCaseResult, BenchmarkResult, BenchmarkRunSummary,
  CompareResponse, TestableModel,
} from "../../../core/api/benchmark_api"
import { ModelSelectorGrid, fmtScore } from "./ModelSelectorGrid"
import { LatestResultSection } from "./LatestResultSection"
import { HistoryTable } from "./HistoryTable"
import { RunDetailModal } from "./RunDetailModal"

export interface BenchmarkPanelProps {
  CATEGORY_LABEL: Record<string, string>
  RATING_TONE: Record<string, string>
  bar: (v: number) => React.ReactNode
  caseMetric: (c: BenchmarkCaseResult) => string
  compareResult: CompareResponse | null
  error: string | null
  handleCompare: () => void
  handleDownloadCompare: () => void
  handleDownloadRun: (runId: string, model: string) => void
  handlePickRun: (runId: string) => void
  handleRun: () => void
  handleDeleteRun?: (runId: string) => void
  history: BenchmarkRunSummary[]
  latest: BenchmarkResult | null
  models: TestableModel[]
  progress: string
  reportText: string
  running: boolean
  selectedKeys: Set<string>
  selectedModels: TestableModel[]
  selectedRuns: Set<string>
  toggleModel: (k: string) => void
  toggleRun: (k: string) => void
  trendScores: number[]
}

export function BenchmarkPanelView(p: BenchmarkPanelProps) {
  const [detail, setDetail] = useState<BenchmarkRunSummary | null>(null)

  return (
    <div className="bm-dashboard">
      <div className="bm-section-head">
        <h3>大模型能力测试</h3>
        <div className="bm-actions">
          <button className="bm-btn" onClick={p.handleRun}
                  disabled={p.running || p.selectedKeys.size === 0}>
            {p.running ? "测试中…" : `跑测试 (${p.selectedKeys.size})`}
          </button>
          <button className="bm-btn bm-btn-secondary" onClick={p.handleCompare}
                  disabled={p.selectedRuns.size < 2}>
            对比 ({p.selectedRuns.size})
          </button>
          <button className="bm-btn bm-btn-secondary"
                  onClick={p.handleDownloadCompare}
                  disabled={!p.compareResult}>
            导出对比
          </button>
        </div>
      </div>

      {p.error && <div className="bm-err">{p.error}</div>}
      {p.progress && <div className="bm-progress">{p.progress}</div>}

      <ModelSelectorGrid
        models={p.models}
        selectedKeys={p.selectedKeys}
        toggleModel={p.toggleModel}
      />

      {p.latest && (
        <LatestResultSection
          latest={p.latest}
          categoryLabel={p.CATEGORY_LABEL}
          bar={p.bar}
          caseMetric={p.caseMetric}
          onDownload={p.handleDownloadRun}
        />
      )}

      <HistoryTable
        history={p.history}
        selectedRuns={p.selectedRuns}
        toggleRun={p.toggleRun}
        onOpenDetail={setDetail}
        onDownload={p.handleDownloadRun}
        onDelete={p.handleDeleteRun}
      />

      {p.compareResult && (
        <CompareSection
          compareResult={p.compareResult}
          categoryLabel={p.CATEGORY_LABEL}
          onDownload={p.handleDownloadCompare}
        />
      )}

      {!p.latest && p.history.length === 0 && (
        <div className="bm-empty">
          勾选上方模型 → 点【跑测试】→ 结果自动展示
        </div>
      )}

      {detail && (
        <RunDetailModal
          run={detail}
          categoryLabel={p.CATEGORY_LABEL}
          onClose={() => setDetail(null)}
          onDownload={p.handleDownloadRun}
        />
      )}
    </div>
  )
}

/* ============ 对比结果表 ============ */
function CompareSection({
  compareResult, categoryLabel, onDownload,
}: {
  compareResult: CompareResponse
  categoryLabel: Record<string, string>
  onDownload: () => void
}) {
  return (
    <div className="bm-block">
      <div className="bm-block-title">
        对比结果（{compareResult.rows.length} 个模型）
        <button className="bm-btn-mini" onClick={onDownload}>
          下载 Markdown
        </button>
      </div>
      <table className="bm-table">
        <thead>
          <tr>
            <th>模型</th><th>Provider</th>
            <th>{categoryLabel.latency ?? "延迟"}</th>
            <th>{categoryLabel.stability ?? "稳定性"}</th>
            <th>{categoryLabel.capability ?? "能力"}</th>
            <th>{categoryLabel.cost ?? "成本"}</th>
            <th>总分</th>
          </tr>
        </thead>
        <tbody>
          {compareResult.rows.map((r: any) => (
            <tr key={r.run_id ?? r.model}>
              <td className="bm-mono">{r.model}</td>
              <td className="bm-muted">{r.provider}</td>
              <td>{fmtScore(r.by_category?.latency ?? 0)}</td>
              <td>{fmtScore(r.by_category?.stability ?? 0)}</td>
              <td>{fmtScore(r.by_category?.capability ?? 0)}</td>
              <td>{fmtScore(r.by_category?.cost ?? 0)}</td>
              <td className={r.score >= 70 ? "bm-ok" : "bm-warn"}>
                {fmtScore(r.score)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <details className="bm-report">
        <summary>查看完整报告</summary>
        <pre>{compareResult.report_text}</pre>
      </details>
    </div>
  )
}

export default BenchmarkPanelView
