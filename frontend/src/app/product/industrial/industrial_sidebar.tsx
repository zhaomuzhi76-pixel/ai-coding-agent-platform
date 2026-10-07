import type { Locale } from "../../../core/i18n/locale"
import { industrialText } from "./industrial_copy"

export type IndustrialNav =
  | "projects"
  | "settings"

interface IndustrialSidebarProps {
  locale: Locale
  active: IndustrialNav
  socketState: string
  onNavigate(
    value: IndustrialNav,
  ): void
}

const NAV: Array<{
  id: IndustrialNav
  icon: string
  key: Parameters<typeof industrialText>[1]
}> = [
  {
    id: "projects",
    icon: "⌂",
    key: "projects",
  },
  {
    id: "settings",
    icon: "⚙",
    key: "settings",
  },
]

export function IndustrialSidebar(
  props: IndustrialSidebarProps,
) {
  return (
    <aside className="industrial-sidebar">
      <div className="industrial-brand">
        <div className="industrial-brand__mark">
          ✦
        </div>

        <div>
          <strong>
            BIANCHENG
          </strong>
          <span>
            AI AGENT
          </span>
        </div>
      </div>

      <nav className="industrial-nav">
        {NAV.map(item => (
          <button
            type="button"
            key={item.id}
            className={
              item.id === props.active
                ? "industrial-nav__item industrial-nav__item--active"
                : "industrial-nav__item"
            }
            onClick={() =>
              props.onNavigate(item.id)
            }
          >
            <span>
              {item.icon}
            </span>

            {industrialText(
              props.locale,
              item.key,
            )}
          </button>
        ))}
      </nav>

      <div className="industrial-sidebar__footer">
        <span className="industrial-health-dot" />

        <span>
          {props.socketState}
        </span>
      </div>
    </aside>
  )
}
