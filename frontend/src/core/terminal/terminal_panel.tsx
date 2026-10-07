import { useState } from "react"
import { TerminalView } from "./terminal_view"

type PanelTab = "terminal" | "output" | "problems" | "debug"

const TABS: Array<{ id: PanelTab; label: string }> = [
  { id: "problems", label: "PROBLEMS" },
  { id: "output", label: "OUTPUT" },
  { id: "debug", label: "DEBUG CONSOLE" },
  { id: "terminal", label: "TERMINAL" },
]

export function TerminalPanel() {
  const [tab, setTab] = useState<PanelTab>("terminal")

  return (
    <div className="terminal-panel">
      <div className="terminal-panel__tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={`terminal-panel__tab${tab === t.id ? " is-active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="terminal-panel__body">
        {tab === "terminal" && <TerminalView />}
        {tab === "output" && <PanelPlaceholder label="Output" />}
        {tab === "problems" && <PanelPlaceholder label="No problems detected" />}
        {tab === "debug" && <PanelPlaceholder label="Debug console ready" />}
      </div>
    </div>
  )
}

function PanelPlaceholder({ label }: { label: string }) {
  return <div className="terminal-panel__empty">{label}</div>
}
