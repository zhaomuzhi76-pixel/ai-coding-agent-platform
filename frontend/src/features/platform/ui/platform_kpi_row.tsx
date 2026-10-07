import type { PlatformState } from "../platform_state"

export function PlatformKpiRow(props: { state: PlatformState }) {
  const { session, proposals, models, domains } = props.state
  const applied = proposals.filter((p) => p.status === "applied").length
  const pending = proposals.filter((p) => p.status === "pending").length
  return (
    <div className="kpi-row">
      <div className="kpi-card">
        <div className="kpi-card__label">会话</div>
        <div className="kpi-card__value">
          {session ? session.session_id.slice(0, 8) : "—"}
        </div>
        <div className="kpi-card__hint mono">
          {session?.model ?? "未选择模型"}
        </div>
      </div>
      <div className="kpi-card">
        <div className="kpi-card__label">提案总数</div>
        <div className="kpi-card__value">{proposals.length}</div>
        <div className="kpi-card__hint">
          待审批 {pending} · 已应用 {applied}
        </div>
      </div>
      <div className="kpi-card">
        <div className="kpi-card__label">可用模型</div>
        <div className="kpi-card__value">{models.length}</div>
        <div className="kpi-card__hint">
          由用户选择，不做后端路由
        </div>
      </div>
      <div className="kpi-card">
        <div className="kpi-card__label">领域</div>
        <div className="kpi-card__value">{domains.length}</div>
        <div className="kpi-card__hint">
          {domains.map((d) => d.name).join(" / ") || "—"}
        </div>
      </div>
    </div>
  )
}
