import type { ReactNode } from "react"

export function IdeContextPanel(
  props: { children: ReactNode },
) {
  return (
    <div className="ide-context">
      {props.children}
    </div>
  )
}
