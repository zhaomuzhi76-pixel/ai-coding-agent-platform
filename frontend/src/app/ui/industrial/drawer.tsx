import { createPortal } from "react-dom"
import type { ReactNode } from "react"

export function Drawer(props: {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
  footer?: ReactNode
  className?: string
  style?: React.CSSProperties
}) {
  if (!props.open) return null
  if (typeof document === "undefined") return null

  // [PORTAL] 直接挂到 body，摆脱父级 transform/overflow 陷阱
  return createPortal(
    <>
      <div className="ind-drawer-mask" onClick={props.onClose} />
      <aside className={"ind-drawer" + (props.className ? " " + props.className : "")}
             style={props.style} role="dialog">
        <header className="ind-drawer__head">
          <div className="ind-drawer__title">{props.title}</div>
          <button className="ind-drawer__close"
                  onClick={props.onClose}
                  aria-label="关闭">×</button>
        </header>
        <div className="ind-drawer__body">{props.children}</div>
        {props.footer && (
          <div className="ind-drawer__foot">{props.footer}</div>
        )}
      </aside>
    </>,
    document.body,
  )
}
