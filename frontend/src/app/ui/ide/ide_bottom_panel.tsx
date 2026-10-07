import type { ReactNode } from "react"

export function IdeBottomPanel(
  props: { children: ReactNode },
) {
  return (
    <div className="ide-bottom">
      {props.children}
    </div>
  )
}
