interface Props {
  title: string
  hint: string
}

export function PlaceholderView(props: Props) {
  return (
    <div className="view-placeholder">
      <div className="view-placeholder__title">{props.title}</div>
      <div className="view-placeholder__hint">{props.hint}</div>
    </div>
  )
}
