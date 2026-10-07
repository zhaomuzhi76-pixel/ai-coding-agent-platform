/** AI 助手领域多选（空 = 全部领域） */
import { useEffect, useState } from "react"

const DOMAINS = [
  { value: "tcm", label: "中医" },
  { value: "agriculture", label: "农业" },
  { value: "finance", label: "金融" },
  { value: "general", label: "通用" },
]

const KEY = "biancheng.agent.domains"

export function loadDomains(): string[] {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return []
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? arr : []
  } catch { return [] }
}

export function saveDomains(d: string[]) {
  try { localStorage.setItem(KEY, JSON.stringify(d)) } catch { /* ignore */ }
}

interface Props {
  onChange?: (domains: string[]) => void
}

export function AgentDomainChips({ onChange }: Props) {
  const [selected, setSelected] = useState<Set<string>>(
    () => new Set(loadDomains()),
  )

  useEffect(() => { saveDomains(Array.from(selected)) }, [selected])

  const toggle = (v: string) => {
    setSelected((prev) => {
      const n = new Set(prev)
      if (n.has(v)) n.delete(v); else n.add(v)
      const arr = Array.from(n)
      onChange?.(arr)
      return n
    })
  }

  return (
    <div style={{ display: "flex", gap: 6, alignItems: "center",
                  fontSize: 12, flexWrap: "wrap" }}>
      <span style={{ color: "var(--text-soft)" }}>领域</span>
      {DOMAINS.map((d) => {
        const on = selected.has(d.value)
        return (
          <button key={d.value} type="button" onClick={() => toggle(d.value)}
                  style={{
                    padding: "2px 10px", borderRadius: 12,
                    border: "1px solid " + (on ? "#2563eb" : "#33333a"),
                    background: on ? "rgba(37,99,235,.2)" : "transparent",
                    color: on ? "#93c5fd" : "#9a9aa0",
                    fontSize: 11, cursor: "pointer",
                  }}>
            {d.label}
          </button>
        )
      })}
      {selected.size === 0 && (
        <span style={{ fontSize: 10, color: "#6b7280" }}>（空=全部）</span>
      )}
    </div>
  )
}

export default AgentDomainChips
