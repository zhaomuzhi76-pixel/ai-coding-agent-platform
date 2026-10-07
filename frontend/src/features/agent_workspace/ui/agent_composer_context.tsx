/** Agent composer 底部上下文条：Workspace + Model + Events 计数。 */
import { useEffect, useState } from "react"
import type { AgentWorkspaceState } from "../agent_workspace_state"
import type { BackendModel } from "../../../core/models/backend_models_source"

import { workspaceLabel, modelLabel } from "./agent_workspace_label"
const FOLLOW_ROLE = "__follow_role__"

interface RoleCard {
  role: string
  label: string
  primary: string
  primary_provider?: string
  fallback?: string | null
}

/** 解析"跟随角色配置"下实际会用哪个模型。
 *  优先级与后端 gateway._resolve_auto_model 一致：
 *  complex > intent > plan > code > review */
function resolveAutoModel(cards: RoleCard[]): string {
  for (const r of ["complex", "intent", "plan", "code", "review"]) {
    const c = cards.find((x) => x.role === r)
    if (c && c.primary) return c.primary
  }
  return ""
}

export function AgentComposerContext({
  state, backendModels, executing, timelineCount, onSelectModel,
}: {
  state: AgentWorkspaceState
  backendModels: BackendModel[]
  executing: boolean
  timelineCount: number
  onSelectModel: (id: string) => void
}) {
  const currentValue = state.model.model === FOLLOW_ROLE
    ? FOLLOW_ROLE
    : (state.model.model || FOLLOW_ROLE)
  const [roleCards, setRoleCards] = useState<RoleCard[]>([])

  // 拉 ROLE ROUTING 配置（用于显示"跟随角色配置"下的实际模型）
  useEffect(() => {
    let alive = true
    fetch("/api/model-registry/roles")
      .then((r) => r.json())
      .then((d) => {
        if (!alive) return
        // 兼容多种返回结构
        const arr = Array.isArray(d) ? d
                  : Array.isArray(d?.data) ? d.data
                  : Array.isArray(d?.roles) ? d.roles
                  : []
        setRoleCards(arr)
      })
      .catch(() => { /* 忽略 */ })
    return () => { alive = false }
  }, [])

  const autoModel = resolveAutoModel(roleCards)
  const showAutoHint = currentValue === FOLLOW_ROLE && !!autoModel

  const handleChange = (v: string) => {
    if (v === FOLLOW_ROLE) {
      onSelectModel(FOLLOW_ROLE)   // 魔法值 = 跟随角色配置
    } else {
      onSelectModel(v)
    }
  }

  return (
    <div className="agent-composer__context">
      <span className="agent-composer__chip" title={workspaceLabel(state)}>
        <span>Workspace</span>
        <strong>{workspaceLabel(state)}</strong>
      </span>

      <span className="agent-composer__chip"
            title={showAutoHint
              ? `跟随角色配置 → 实际使用 ${autoModel}`
              : modelLabel(state)}>
        <span>{showAutoHint ? "自动" : "Model"}</span>
        <select
          value={currentValue}
          onChange={(e) => handleChange(e.target.value)}
          disabled={executing}
          style={{
            background: "transparent", border: "none",
            color: "inherit", font: "inherit",
            maxWidth: 170, minWidth: 0, textOverflow: "ellipsis", cursor: "pointer", outline: "none",
          }}
        >
          <option value={FOLLOW_ROLE}>✨ 跟随角色配置（按任务自动选模型）</option>
          <optgroup label="─── 手动指定（全局覆盖） ───">
            {backendModels.length === 0 ? (
              <option value={state.model.model || ""}>
                {modelLabel(state) || "（无可用模型）"}
              </option>
            ) : (
              backendModels.map((m) => (
                <option key={`${m.provider}/${m.model}`} value={m.model}>
                  {m.display_name} · {m.provider}
                </option>
              ))
            )}
          </optgroup>
        </select>
        {showAutoHint && (
          <span
            title={`实际使用模型：${autoModel}`}
            style={{
              fontSize: 10, padding: "1px 6px", borderRadius: 8,
              background: "rgba(79,214,154,.15)",
              color: "#4fd69a", whiteSpace: "nowrap",
              maxWidth: 140, overflow: "hidden",
              textOverflow: "ellipsis",
            }}>
            → {autoModel}
          </span>
        )}
      </span>

      {/* [REMOVED] AgentDomainChips：领域选择属 AI 助手，不属于工作区 */}

      <span className="agent-composer__stats">
        <span
          className={`agent-composer__status-dot${
            state.session?.session_id ? " is-on" : " is-off"
          }`}
          aria-hidden="true"
        />
        <span className="agent-composer__stat">
          {state.session?.session_id ? "Session active" : "No session"}
        </span>
        <span className="agent-composer__stat-sep" aria-hidden="true">·</span>
        <span className="agent-composer__stat agent-composer__stat--dim">
          {timelineCount} events
        </span>
      </span>
    </div>
  )
}