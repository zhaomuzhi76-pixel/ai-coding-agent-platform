import type { ReactNode } from "react"

interface Props {
  children: ReactNode
}

export function ContextPanel({ children }: Props) {
  return (
    <aside className="ai-context-panel">
      {children}
    </aside>
  )
}
