export type BadgeTone =
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "muted"

export function Badge(props: {
  tone?: BadgeTone
  children: React.ReactNode
}) {
  const tone = props.tone ?? "muted"
  return (
    <span className={`ind-badge ind-badge--${tone}`}>
      {props.children}
    </span>
  )
}
