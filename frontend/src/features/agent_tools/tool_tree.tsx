/** 工具树：按 domain 折叠分组 + 组级/单工具勾选（工业级紧凑布局）。 */
import { useState } from "react"

import type { ToolItem } from "../../core/api/agent_tools_api"

interface Props {
  groups: Record<string, ToolItem[]>
  enabled: Set<string>
  onToggle: (name: string) => void
  /** 领域批量开关（点击领域 checkbox 触发） */
  onToggleDomain?: (domain: string) => void
  /** 领域标签映射 */
  domainLabel?: Record<string, string>
  busy?: boolean
}

const DEFAULT_LABEL: Record<string, string> = {
  tcm: "中医", agriculture: "农业", finance: "金融",
  general: "通用", medicine: "医学", history: "历史", law: "法律",
}

function groupByDomain(groups: Record<string, ToolItem[]>) {
  const out: Record<string, { group: string; tool: ToolItem }[]> = {}
  for (const [gk, items] of Object.entries(groups)) {
    for (const t of items) {
      const d = t.domain || "general"
      if (!out[d]) out[d] = []
      out[d].push({ group: gk, tool: t })
    }
  }
  return out
}

export function ToolTree({
  groups, enabled, onToggle, onToggleDomain, domainLabel, busy,
}: Props) {
  const byDomain = groupByDomain(groups)
  const domains = Object.keys(byDomain).sort()
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())
  const LABEL = { ...DEFAULT_LABEL, ...(domainLabel || {}) }

  if (domains.length === 0) {
    return <div style={{ opacity: 0.6, fontSize: 12, padding: 12 }}>暂无工具</div>
  }

  const toggleCollapse = (d: string) => {
    const s = new Set(collapsed)
    if (s.has(d)) s.delete(d); else s.add(d)
    setCollapsed(s)
  }

  return (
    <div style={{ display: "grid", gap: 4 }}>
      {domains.map((d) => {
        const items = byDomain[d]
        const on = items.filter((x) => enabled.has(x.tool.name)).length
        const allOn = items.length > 0 && on === items.length
        const someOn = on > 0 && !allOn
        const isOpen = !collapsed.has(d)

        return (
          <div key={d}>
            <div
              style={{
                display: "flex", alignItems: "center", gap: 6,
                padding: "6px 10px", borderRadius: 4, fontSize: 12,
                background: isOpen ? "rgba(118,169,255,.06)" : "transparent",
                borderLeft: "2px solid " + (on > 0 ? "#7aa2f7" : "transparent"),
              }}
            >
              {/* 组级复选框：点击=批量开关 */}
              <input
                type="checkbox"
                checked={allOn}
                ref={(el) => {
                  if (el) el.indeterminate = someOn
                }}
                disabled={busy}
                onChange={(e) => {
                  e.stopPropagation()
                  onToggleDomain?.(d)
                }}
                onClick={(e) => e.stopPropagation()}
                title={allOn ? `取消 ${LABEL[d] ?? d} 全部` : `全选 ${LABEL[d] ?? d}`}
                style={{ cursor: "pointer", flexShrink: 0 }}
              />
              {/* 折叠三角 + 名称：点击=展开/收起 */}
              <span
                onClick={() => toggleCollapse(d)}
                style={{
                  flex: 1, cursor: "pointer", opacity: 0.9,
                  userSelect: "none",
                }}
              >
                <span onClick={(e) => { e.stopPropagation(); toggleCollapse(d) }}
                      style={{ marginRight: 4 }}>
                  {isOpen ? "▾" : "▸"}
                </span>
                <span onClick={(e) => { e.stopPropagation(); onToggleDomain?.(d) }}
                      style={{ flex: 1 }}>
                  {LABEL[d] ?? d}
                </span>
              </span>
              <span style={{ opacity: 0.5, fontSize: 10 }}>
                {on}/{items.length}
              </span>
            </div>

            {isOpen && (
              <div style={{ display: "grid", gap: 2, marginLeft: 12, marginTop: 2 }}>
                {items.map(({ tool }) => {
                  const isOn = enabled.has(tool.name)
                  return (
                    <label key={tool.name} title={tool.description} style={{
                      display: "flex", alignItems: "center", gap: 6,
                      padding: "4px 8px", borderRadius: 3, fontSize: 11,
                      background: isOn ? "rgba(118,169,255,.08)" : "transparent",
                      cursor: busy ? "not-allowed" : "pointer",
                    }}>
                      <input type="checkbox" checked={isOn} disabled={busy}
                        onChange={() => onToggle(tool.name)} />
                      <span style={{
                        fontFamily: "ui-monospace, monospace",
                        overflow: "hidden", textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}>{tool.name}</span>
                    </label>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default ToolTree
