import {
  useSyncExternalStore,
} from "react"

import {
  snapshotTheme,
  subscribeTheme,
  toggleTheme,
  type Theme,
} from "../../../core/theme/theme"
import { useI18n } from "../../../core/i18n/i18n"
import type { Locale } from "../../../core/i18n/locale"
import type { MessageKey } from "../../../core/i18n/messages"

import "./global_nav.css"

export type NavTab =
  | "coding"
  | "chatbot"
  | "platform"
  | "models"
  | "finetune"
  | "rag"
  | "mcp"
  | "security"
  | "monitor"
  | "providers"

interface TabDef {
  id: NavTab
  labelKey: MessageKey
  icon: string
}

const TABS: TabDef[] = [
  { id: "coding", labelKey: "nav.coding", icon: "⌨" },
  { id: "chatbot", labelKey: "nav.chatbot", icon: "🤖" },
  { id: "platform", labelKey: "nav.platform", icon: "▦" },
  { id: "models", labelKey: "nav.models", icon: "◆" },
  { id: "finetune", labelKey: "nav.finetune", icon: "⚙" },
  { id: "rag", labelKey: "nav.rag", icon: "📚" },
  { id: "mcp", labelKey: "nav.mcp", icon: "⛭" },
  { id: "security", labelKey: "nav.security", icon: "🔒" },
  { id: "monitor", labelKey: "nav.monitor", icon: "◉" },
  { id: "providers", labelKey: "nav.providers", icon: "⚛" },
]

function subscribeHash(listener: () => void): () => void {
  window.addEventListener("hashchange", listener)
  return () => window.removeEventListener("hashchange", listener)
}

function readTab(): NavTab {
  const raw = window.location.hash.replace(/^#\/?/, "")
  const found = TABS.find((t) => t.id === raw)
  return found ? found.id : "coding"
}

export function useNavTab(): NavTab {
  return useSyncExternalStore(subscribeHash, readTab, readTab)
}

export function navigate(tab: NavTab): void {
  window.location.hash = `#/${tab}`
}

export function GlobalNav() {
  const active = useNavTab()
  const { t, locale, setLocale } = useI18n()
  const theme = useSyncExternalStore<Theme>(
    subscribeTheme,
    snapshotTheme,
    snapshotTheme,
  )

  const toggleLocale = () => {
    setLocale(locale === "zh-CN" ? "en-US" : "zh-CN" as Locale)
  }

  return (
    <header className="global-nav">
      <div className="global-nav__brand">
        <div className="global-nav__logo">AI</div>
        <span className="global-nav__name">
          Biancheng · {t("nav.brand")}
        </span>
      </div>
      <nav className="global-nav__tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={
              "global-nav__tab"
              + (tab.id === active
                ? " global-nav__tab--active"
                : "")
            }
            onClick={() => navigate(tab.id)}
            aria-label={t(tab.labelKey)}
          >
            <span className="global-nav__icon">{tab.icon}</span>
            <span>{t(tab.labelKey)}</span>
          </button>
        ))}
      </nav>
      <div className="global-nav__right">
        <span className="global-nav__status">
          <span className="global-nav__dot" />
          <span>{t("nav.connected")}</span>
        </span>
        <button
          className="theme-toggle"
          data-action="locale"
          aria-label={locale === "zh-CN" ? "中文" : "EN"}
          onClick={toggleLocale}
          title={locale === "zh-CN" ? "Switch to English" : "切换到中文"}
        >
          <span className="theme-toggle__icon">🌐</span>
          <span>{locale === "zh-CN" ? "中文" : "EN"}</span>
        </button>
        <button
          className="theme-toggle"
          data-action="theme"
          aria-label={theme === "dark" ? "Light" : "Dark"}
          onClick={() => toggleTheme()}
          title={
            theme === "dark"
              ? t("theme.toLight")
              : t("theme.toDark")
          }
        >
          <span className="theme-toggle__icon">
            {theme === "dark" ? "☀" : "☾"}
          </span>
          <span>
            {theme === "dark" ? t("theme.light") : t("theme.dark")}
          </span>
        </button>
        <span>v0.1.0</span>
      </div>
    </header>
  )
}
