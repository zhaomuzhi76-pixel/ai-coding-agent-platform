import type { ReactNode } from "react"
import "./industrial.css"

export function IndustrialPage(props: {
  title: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
}) {
  return (
    <div className="ind-page">
      <header className="ind-page__header">
        <div>
          <h2 className="ind-page__title">{props.title}</h2>
          {props.subtitle && (
            <div className="ind-page__subtitle">{props.subtitle}</div>
          )}
        </div>
        {props.actions && (
          <div className="ind-page__actions">{props.actions}</div>
        )}
      </header>
      <div className="ind-page__body">{props.children}</div>
    </div>
  )
}
