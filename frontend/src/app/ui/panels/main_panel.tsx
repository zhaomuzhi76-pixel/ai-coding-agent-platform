import type { ReactNode } from "react"

interface Props {
  children: ReactNode
}

export function MainPanel({ children }: Props) {
  return (
    <main className="ai-main-panel">
      {children}
    </main>
  )
}
