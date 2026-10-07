import type { ReactNode } from "react"

export function IdeSidebar(
  props: { children: ReactNode },
) {
  return (
    <div className="ide-sidebar">
      {props.children}
    </div>
  )
}
