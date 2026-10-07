/** LLM 监控仪表盘（Dify 风格） */
import { useCallback, useEffect, useState } from "react"

import { monitorApi, type KpiSummary, type ModelStat, type TrendPoint } from "./api"
import { KpiCards } from "./KpiCards"
import { TrendChart } from "./TrendChart"
import { ModelTable } from "./ModelTable"
import { ModelBenchmarkPanel } from "../ui/model_benchmark_panel"

type Range = 1 | 6 | 24 | 168

export function LlmMonitorDashboard() {
  const [range, setRange] = useState<Range>(24)
  const [kpi, setKpi] = useState<KpiSummary | null>(null)
  const [trend, setTrend] = useState<TrendPoint[]>([])
  const [models, setModels] = useState<ModelStat[]>([])
  const [err, setErr] = useState("")

  const refresh = useCallback(async () => {
    try {
      const [k, t, m] = await Promise.all([
        monitorApi.summary(range),
        monitorApi.trend(range, range <= 24 ? "hour" : "day"),
        monitorApi.byModel(range),
      ])
      setKpi(k); setTrend(t); setModels(m); setErr("")
    } catch (e) {
      setErr(String(e))
    }
  }, [range])

  useEffect(() => {
    void refresh()
    const id = window.setInterval(refresh, 30_000)  // 30 秒自动刷新
    return () => window.clearInterval(id)
  }, [refresh])

  return (
    <div className="mon-dashboard">
      <header className="mon-topbar">
        <h2>📊 大模型监控</h2>
        <div className="mon-range">
          {([1, 6, 24, 168] as Range[]).map((h) => (
            <button key={h}
                    className={range === h ? "active" : ""}
                    onClick={() => setRange(h)}>
              {h === 1 ? "1h" : h === 6 ? "6h" : h === 24 ? "24h" : "7d"}
            </button>
          ))}
          <button className="mon-refresh" onClick={() => void refresh()}>↻</button>
        </div>
      </header>

      {err && <div className="mon-err">加载失败: {err}</div>}

      <KpiCards kpi={kpi} />

      <section className="mon-section">
        <h3>调用趋势</h3>
        <TrendChart points={trend} />
      </section>

      <section className="mon-section">
        <h3>模型统计</h3>
        <ModelTable rows={models} />
      </section>

      <section className="mon-section">
        <ModelBenchmarkPanel />
      </section>
    </div>
  )
}

export default LlmMonitorDashboard
