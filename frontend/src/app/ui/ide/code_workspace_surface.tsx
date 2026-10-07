import type { ReactNode } from "react"

interface Props {
  children: ReactNode
}

export function CodeWorkspaceSurface(props: Props) {
  return (
    <section className="ide-code-surface">
      {props.children}
    </section>
  )
}
