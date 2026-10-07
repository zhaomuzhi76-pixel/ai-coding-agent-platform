/** 排序模型门控面板 —— 嵌入配置中心。
 *  只显示后端"链路测试通过"的模型在下拉中。 */
import { useCallback, useEffect, useState } from "react"

import {
  l23RerankerApi,
  type RerankerCard,
} from "../../core/api/l23_review_api"
import { Badge, KpiCard, KpiRow } from "../../app/ui/industrial"

import "./l23_review.css"

export function RerankerCenter() {
  const [cards, setCards] = useState<RerankerCard[]>([])
  const [passing, setPassing] = useState(0)
  const [selected, setSelected] = useState("")
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const r = await l23RerankerApi.cards()
      setCards(r.cards)
      setPassing(r.passing)
      setSelected(r.selected)
      setError(null)
    } catch (e) {
      setError(String(e))
    }
  }, [])

  useEffect(() => { void load() }, [load])

  const onProbe = async (id: string) => {
    setBusy(id)
    try {
      const r = await l23RerankerApi.probe(id)
      await load()
      if (r.outcome !== "ok") setError(`探测失败: ${r.message}`)
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(null)
    }
  }

  const onSelect = async (id: string) => {
    try {
      const r = await l23RerankerApi.select(id)
      if (r.selected) setSelected(r.current)
      else setError("该模型未通过链路测试，不可选")
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <section className="l23-panel">
      <div className="l23-panel__head">
        <div>
          <div className="l23-panel__title">排序模型门控</div>
          <div className="l23-panel__sub">
            只有通过链路测试的模型才能被选用
          </div>
        </div>
        <button className="ind-btn" onClick={() => void load()}>
          刷新
        </button>
      </div>

      <KpiRow>
        <KpiCard label="模型总数" value={cards.length} />
        <KpiCard label="已通过" value={passing} />
        <KpiCard label="当前选中" value={selected || "—"} />
      </KpiRow>

      {error && <div className="l23-error">{error}</div>}

      <div className="l23-cards">
        {cards.map((c) => (
          <div key={c.model_id} className="l23-card">
            <div className="l23-card__head">
              <div className="l23-card__name">{c.display_name}</div>
              <Badge tone={toneOf(c.status)}>
                {c.status_label}
              </Badge>
            </div>
            <div className="l23-card__meta">
              <span className="l23-pill">{c.backend_kind}</span>
              {c.last_latency_ms > 0 && (
                <span className="l23-pill">{c.last_latency_ms.toFixed(0)}ms</span>
              )}
              {c.selected && <span className="l23-pill l23-pill--ok">当前选中</span>}
            </div>
            {c.last_message && (
              <div className="l23-card__msg">{c.last_message}</div>
            )}
            <div className="l23-card__actions">
              <button
                className="ind-btn"
                disabled={busy === c.model_id}
                onClick={() => void onProbe(c.model_id)}
              >
                {busy === c.model_id ? "测试中…" : "链路测试"}
              </button>
              <button
                className="ind-btn"
                disabled={!c.selectable || c.selected}
                onClick={() => void onSelect(c.model_id)}
              >
                {c.selected ? "已选中" : "选择"}
              </button>
            </div>
          </div>
        ))}
        {cards.length === 0 && (
          <div className="l23-empty">暂无排序模型</div>
        )}
      </div>
    </section>
  )
}

function toneOf(status: string): "ok" | "warn" | "off" {
  if (status === "passing") return "ok"
  if (status === "failing") return "warn"
  return "off"
}
