import type { ReactNode } from "react"

interface Props {
  children: ReactNode
}

export function SidePanel({ children }: Props) {
  return (
    <aside className="ai-side-panel">
      {children}
    </aside>
  )
}
