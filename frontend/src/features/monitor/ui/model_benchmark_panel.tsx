/**
 * ModelBenchmarkPanel: 模型能力测试面板（多选/单跑/批量/对比/下载）。
 *
 * 职责：
 *   - 从 /benchmark/models 拉可测模型
 *   - 单选跑 / 多选批量跑
 *   - 展示最新结果 + 报告
 *   - 多历史对比 + 下载报告（.txt / .md）
 *
 * 不负责：
 *   - 跑测逻辑（后端）
 *   - 评分逻辑（后端）
 *   - 持久化（后端 SQLite）
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react"

import {
  benchmarkApi,
  type BenchmarkCaseResult,
  type BenchmarkResult,
  type BenchmarkRunSummary,
  type CompareResponse,
  type TestableModel,
} from "../../../core/api/benchmark_api"
import {
  Badge, EmptyState, Sparkline,
} from "../../../app/ui/industrial"

import { BenchmarkPanelView } from "../dashboard/BenchmarkPanelView";
import { INTERVALS } from "../../../core/config/intervals"

const RATING_TONE: Record<string, "success" | "warning" | "danger" | "info"> = {
  "A+": "success", "A": "success", "B+": "info", "B": "info",
  "C": "warning", "D": "danger",
}

const CATEGORY_LABEL: Record<string, string> = {
  capability: "能力", latency: "延迟",
  stability: "稳定性", cost: "成本",
}

function fmtMs(v: number): string {
  if (v >= 1000) return `${(v / 1000).toFixed(2)}s`
  return `${v.toFixed(0)}ms`
}

function fmtCost(v: number): string {
  if (v === 0) return "$0"
  if (v < 0.0001) return `$${v.toExponential(2)}`
  return `$${v.toFixed(4)}`
}

function bar(pct: number, width = 12): string {
  const filled = Math.max(0, Math.min(width, Math.round((pct / 100) * width)))
  return "█".repeat(filled) + "░".repeat(width - filled)
}

function caseMetric(c: BenchmarkCaseResult): string {
  if (c.case_id === "first_token") return `${c.first_token_ms.toFixed(0)}ms`
  if (c.case_id === "full_latency") return fmtMs(c.latency_ms)
  if (c.case_id === "success_rate") return `${c.successes}/${c.attempts}`
  if (c.case_id === "cost_per_call") return fmtCost(c.cost)
  return c.passed ? "通过" : "未通过"
}

function downloadBlob(filename: string, content: string, mime = "text/plain") {
  const blob = new Blob([content], { type: mime + ";charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), INTERVALS.objectUrlRevoke)
}

export function ModelBenchmarkPanel() {
  const [models, setModels] = useState<TestableModel[]>([])
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set())
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState("")
  const [latest, setLatest] = useState<BenchmarkResult | null>(null)
  const [history, setHistory] = useState<BenchmarkRunSummary[]>([])
  const [reportText, setReportText] = useState("")
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null)
  const [selectedRuns, setSelectedRuns] = useState<Set<string>>(new Set())
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<number | null>(null)

  const loadModels = useCallback(async () => {
    try {
      const r = await benchmarkApi.testableModels()
      const visible = (r.models || []).filter((m) => m.is_healthy)
      setModels(visible)
    } catch (e) { setError(String(e)) }
  }, [])

  const loadHistory = useCallback(async () => {
    try {
      const r = await benchmarkApi.runs({ limit: 20 })
      setHistory(r.runs || [])
    } catch (e) { setError(String(e)) }
  }, [])

  // 首次加载：拉模型 + 历史（只跑一次）
  useEffect(() => { void loadModels(); void loadHistory() }, [loadModels, loadHistory])

  // 首次拿到模型列表时默认选第一个（只 1 次，不覆盖用户操作）
  const _firstPickDone = useRef(false)
  useEffect(() => {
    if (_firstPickDone.current) return
    if (models.length === 0) return
    _firstPickDone.current = true
    setSelectedKeys(new Set([`${models[0].provider}::${models[0].model}`]))
  }, [models])

  useEffect(() => {
    timerRef.current = window.setInterval(() => { void loadHistory() }, INTERVALS.fast)
    return () => { if (timerRef.current !== null) window.clearInterval(timerRef.current) }
  }, [loadHistory])

  const selectedModels = useMemo(() => {
    return Array.from(selectedKeys).map((k) => {
      const i = k.indexOf("::")
      return { provider: k.slice(0, i), model: k.slice(i + 2) }
    })
  }, [selectedKeys])

  const toggleModel = (key: string) => {
    const next = new Set(selectedKeys)
    if (next.has(key)) next.delete(key); else next.add(key)
    setSelectedKeys(next)
  }

  const toggleRun = (rid: string) => {
    const next = new Set(selectedRuns)
    if (next.has(rid)) next.delete(rid); else next.add(rid)
    setSelectedRuns(next)
  }

  const handleDeleteRun = async (runId: string) => {
    try {
      await benchmarkApi.delete(runId)
      await loadHistory()
    } catch (e) { setError(String(e)) }
  }

  const handleRun = async () => {
    if (selectedModels.length === 0) { setError("请先选择至少一个模型"); return }
    setError(null); setRunning(true)
    setProgress(`正在跑 ${selectedModels.length} 个模型 × 10 用例...`)
    try {
      let lastRunId = ""
      if (selectedModels.length === 1) {
        const m = selectedModels[0]
        const r = await benchmarkApi.run({ provider: m.provider, model: m.model })
        lastRunId = r.run_id
      } else {
        const r = await benchmarkApi.runBatch({ targets: selectedModels })
        const ok = r.results.filter((x) => !x.error)
        lastRunId = ok.length > 0 && ok[ok.length - 1].run_id ? ok[ok.length - 1].run_id! : ""
      }
      setProgress(`完成，最近 run_id=${lastRunId}`)
      if (lastRunId) {
        const detail = await benchmarkApi.detail(lastRunId)
        setLatest(detail)
        const rep = await benchmarkApi.report(lastRunId)
        setReportText(rep.report)
      }
      await loadHistory()
    } catch (e) {
      setError(String(e)); setProgress("")
    } finally {
      setRunning(false)
    }
  }

  const handlePickRun = async (runId: string) => {
    try {
      const d = await benchmarkApi.detail(runId)
      setLatest(d)
      const r = await benchmarkApi.report(runId)
      setReportText(r.report)
    } catch (e) { setError(String(e)) }
  }

  const handleCompare = async () => {
    if (selectedRuns.size < 2) { setError("请选择至少 2 个历史记录对比"); return }
    try {
      const r = await benchmarkApi.compare(Array.from(selectedRuns))
      setCompareResult(r)
    } catch (e) { setError(String(e)) }
  }

  const handleDownloadRun = async (runId: string, model: string) => {
    try {
      const r = await benchmarkApi.report(runId)
      downloadBlob(`benchmark-${model}-${runId}.txt`, r.report)
    } catch (e) { setError(String(e)) }
  }

  const handleDownloadCompare = () => {
    if (!compareResult) return
    downloadBlob(
      `benchmark-compare-${selectedRuns.size}models.md`,
      compareResult.report_markdown,
      "text/markdown",
    )
  }

  const trendScores = history.slice(-12).map((r) => r.score)

  return (
    <BenchmarkPanelView
      CATEGORY_LABEL={CATEGORY_LABEL}
      RATING_TONE={RATING_TONE}
      bar={bar}
      caseMetric={caseMetric}
      compareResult={compareResult}
      error={error}
      handleCompare={handleCompare}
      handleDownloadCompare={handleDownloadCompare}
      handleDownloadRun={handleDownloadRun}
      handleDeleteRun={handleDeleteRun}
      handlePickRun={handlePickRun}
      handleRun={handleRun}
      history={history}
      latest={latest}
      models={models}
      progress={progress}
      reportText={reportText}
      running={running}
      selectedKeys={selectedKeys}
      selectedModels={selectedModels}
      selectedRuns={selectedRuns}
      toggleModel={toggleModel}
      toggleRun={toggleRun}
      trendScores={trendScores}
    />
  )
}
