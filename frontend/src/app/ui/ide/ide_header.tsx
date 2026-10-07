import type { ReactNode } from "react"

export function IdeHeader(
  props: { children: ReactNode },
) {
  return (
    <header className="ide-header">
      {props.children}
    </header>
  )
}
