import type { ReactNode } from "react"

interface Props {
  children: ReactNode
}

export function BottomPanel({ children }: Props) {
  return (
    <section className="ai-bottom-panel">
      {children}
    </section>
  )
}
