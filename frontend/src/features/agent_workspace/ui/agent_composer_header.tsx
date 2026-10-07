/** Agent composer 顶部：品牌 + 状态 + 模型徽章 + 提示。 */
import type { AgentWorkspaceState } from "../agent_workspace_state"

export function AgentComposerHeader({
  state, statusLabel,
}: {
  state: AgentWorkspaceState
  statusLabel: string
}) {
  return (
    <header className="agent-composer__header">
      <div className="agent-composer__identity">
        <span className="agent-composer__mark" aria-hidden="true">✦</span>
        <strong>Agent</strong>
        <span className="agent-composer__status">{statusLabel}</span>
      </div>

      <div className="agent-composer__meta">
        <span
          className="agent-composer__model-badge"
          title={`${state.model.provider} / ${state.model.model || "未选"}`}
          data-provider={state.model.provider || "none"}
        >
          <span className="agent-composer__model-dot" />
          <span className="agent-composer__model-name">
            {state.model.model || "未选择模型"}
          </span>
          <span className="agent-composer__model-provider">
            {state.model.provider || ""}
          </span>
        </span>
        <span className="agent-composer__hint">Ctrl/Cmd + Enter</span>
      </div>
    </header>
  )
}
