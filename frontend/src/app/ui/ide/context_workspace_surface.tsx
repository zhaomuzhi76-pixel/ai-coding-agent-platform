import type { ReactNode } from "react"

interface Props {
  children: ReactNode
}

export function ContextWorkspaceSurface(props: Props) {
  return (
    <section className="ide-context-surface">
      {props.children}
    </section>
  )
}
