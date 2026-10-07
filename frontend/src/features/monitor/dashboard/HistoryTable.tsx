/** 历史记录表（勾选/详情/下载/删除） */
import type { BenchmarkRunSummary } from "../../../core/api/benchmark_api"
import { fmtScore } from "./ModelSelectorGrid"

interface Props {
  history: BenchmarkRunSummary[]
  selectedRuns: Set<string>
  toggleRun: (rid: string) => void
  onOpenDetail: (r: BenchmarkRunSummary) => void
  onDownload: (rid: string, model: string) => void
  onDelete?: (rid: string) => void
}

export function HistoryTable({
  history, selectedRuns, toggleRun, onOpenDetail, onDownload, onDelete,
}: Props) {
  if (history.length === 0) return null
  return (
    <div className="bm-block">
      <div className="bm-block-title">
        历史记录（{history.length}）· 勾选 2+ 可对比
      </div>
      <table className="bm-table">
        <thead>
          <tr>
            <th style={{ width: 40 }}></th>
            <th>模型</th><th>Provider</th>
            <th>总分</th><th>通过/总</th><th>时间</th>
            <th style={{ width: 180 }}>操作</th>
          </tr>
        </thead>
        <tbody>
          {history.slice(0, 30).map((r) => (
            <tr key={r.run_id}>
              <td>
                <div className={"bm-checkbox bm-checkbox--sm" +
                                (selectedRuns.has(r.run_id) ? " on" : "")}
                     onClick={() => toggleRun(r.run_id)}>
                  {selectedRuns.has(r.run_id) ? "✓" : ""}
                </div>
              </td>
              <td className="bm-mono bm-clickable"
                  onClick={() => onOpenDetail(r)}>{r.model}</td>
              <td className="bm-muted">{r.provider}</td>
              <td className={r.score >= 70 ? "bm-ok" : "bm-warn"}>
                {fmtScore(r.score)}
              </td>
              <td>{r.passed_count}/{r.case_count}</td>
              <td className="bm-muted bm-small">
                {new Date(r.started_at * 1000).toLocaleString()}
              </td>
              <td>
                <button className="bm-btn-mini"
                        onClick={() => onOpenDetail(r)}>详情</button>
                <button className="bm-btn-mini"
                        onClick={() => onDownload(r.run_id, r.model)}>下载</button>
                {onDelete && (
                  <button className="bm-btn-mini bm-btn-danger"
                          onClick={() => {
                            if (window.confirm(`删除 ${r.model} @ ${r.run_id}？`)) {
                              onDelete(r.run_id)
                            }
                          }}>删除</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default HistoryTable
