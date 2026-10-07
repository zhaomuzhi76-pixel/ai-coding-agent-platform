type Tone = "default" | "success" | "warning" | "danger"

export function KpiRow(props: { children: React.ReactNode }) {
  return <div className="ind-kpi-row">{props.children}</div>
}

export function KpiCard(props: {
  label: string
  value: React.ReactNode
  hint?: string
  tone?: Tone
}) {
  const cls = "ind-kpi" + (props.tone && props.tone !== "default"
    ? ` ind-kpi--${props.tone}` : "")
  return (
    <div className={cls}>
      <div className="ind-kpi__label">{props.label}</div>
      <div className="ind-kpi__value">{props.value}</div>
      {props.hint && <div className="ind-kpi__hint">{props.hint}</div>}
    </div>
  )
}
