import type { CSSProperties, KeyboardEvent, PointerEvent } from "react"

export interface VerticalSplitHandleProps {
  ariaLabel: string
  onPointerDown: (event: PointerEvent<HTMLDivElement>) => void
  onDoubleClick: () => void
  onKeyDown: (event: KeyboardEvent<HTMLDivElement>) => void
  className?: string
  style?: CSSProperties
}

export function VerticalSplitHandle(props: VerticalSplitHandleProps) {
  const cls = props.className
    ? `vertical-split__handle ${props.className}`
    : "vertical-split__handle"
  return (
    <div
      role="separator"
      aria-orientation="horizontal"
      aria-label={props.ariaLabel}
      tabIndex={0}
      className={cls}
      style={{
        pointerEvents: "auto",
        zIndex: 100,
        ...props.style,
      }}
      onPointerDownCapture={props.onPointerDown}
      onPointerDown={props.onPointerDown}
      onDoubleClick={props.onDoubleClick}
      onKeyDown={props.onKeyDown}
    />
  )
}
