import type { PlatformProposal } from "../../../core/contracts/platform"

export function PlatformProposalDetail(props: {
  proposal: PlatformProposal | null
}) {
  const p = props.proposal
  if (!p) {
    return (
      <div className="muted">
        未选择提案。左侧列表选择，或新建一个。
      </div>
    )
  }
  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        <div className="muted">任务</div>
        <div style={{ marginTop: 4 }}>{p.task}</div>
      </div>
      {p.plan && (
        <div style={{ marginBottom: 12 }}>
          <div className="muted">计划</div>
          <div style={{ marginTop: 4, fontSize: 12 }}>{p.plan}</div>
        </div>
      )}
      <div className="muted" style={{ marginBottom: 8 }}>
        变更 ({p.changes.length})
      </div>
      {p.changes.map((c, i) => (
        <div key={i} className="change-item">
          <div className="change-item__head">
            <span className="change-item__file">{c.file}</span>
            <span className="change-item__kind">{c.kind}</span>
          </div>
          <pre className="change-item__text">
            {c.text.length > 2000
              ? c.text.slice(0, 2000) + "\n…(截断)"
              : c.text}
          </pre>
        </div>
      ))}
      {p.error && (
        <div className="error-banner" style={{ marginTop: 12 }}>
          <span>{p.error}</span>
        </div>
      )}
    </div>
  )
}
