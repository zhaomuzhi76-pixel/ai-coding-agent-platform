export function EmptyState(props: {
  title: string
  hint?: string
  icon?: string
}) {
  return (
    <div className="ind-empty">
      <div className="ind-empty__icon">{props.icon ?? "◇"}</div>
      <div>{props.title}</div>
      {props.hint && (
        <div className="ind-empty__hint">{props.hint}</div>
      )}
    </div>
  )
}
