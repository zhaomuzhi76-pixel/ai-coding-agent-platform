import type { ReactNode } from "react"

interface Props {
  children: ReactNode
}

export function AppShell(
  props: Props,
) {
  return (
    <div className="app-shell">
      {props.children}
    </div>
  )
}
