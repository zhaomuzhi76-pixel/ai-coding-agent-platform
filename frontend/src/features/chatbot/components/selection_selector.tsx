/**
 * 通用选择器。职责：渲染一个下拉 + 触发 onChange。
 * 不做模态判定、不发网络请求、不存储状态。
 */
import type { ModelItem } from "../../../core/api/chatbot_api"

interface Props {
  kind: "llm" | "image_gen" | "embedding" | "rerank"
  label: string
  items: ModelItem[]
  value: string | null
  onChange: (id: string | null) => void
  disabled?: boolean
  disabledReason?: string
  emptyOptionLabel?: string
  allowEmpty?: boolean
}

export function SelectionSelector(props: Props) {
  const {
    kind, label, items, value, onChange, disabled, disabledReason,
    emptyOptionLabel, allowEmpty,
  } = props
  return (
    <label style={{ display: "grid", gap: 4, minWidth: 180 }}>
      <span style={{ fontSize: 11, opacity: 0.6, letterSpacing: 0.5 }}>
        {label}
      </span>
      <select
        className="ind-input"
        value={value ?? ""}
        disabled={!!disabled}
        title={disabled ? disabledReason : undefined}
        onChange={(e) => onChange(e.target.value || null)}
        style={{ padding: "4px 8px", fontSize: 12 }}
      >
        {/* [FOLLOW_ROLE_OPTION] LLM 专用：跟随角色配置 */}
        {kind === "llm" && (
          <option value="__auto__">✨ 跟随角色配置（按任务自动选模型）</option>
        )}
        {(allowEmpty || !value) && (
          <option value="">{emptyOptionLabel ?? "（默认）"}</option>
        )}
        {items.map((m) => (
          <option key={`${m.provider}:${m.id}`} value={m.id}>
            {m.display}
          </option>
        ))}
      </select>
    </label>
  )
}
