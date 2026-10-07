/** 单个工具卡片（业务组件，Dify 风格） */
import { Badge } from "../../app/ui/industrial"

export interface ToolItem {
  name: string
  description: string
  category: string
  exposed?: boolean
  param_count?: number
  custom?: boolean
  disabled?: boolean
}

interface Props {
  tool: ToolItem
  onToggle: (name: string, enabled: boolean) => void
  onDelete?: (name: string) => void
}

export function ToolCard({ tool, onToggle, onDelete }: Props) {
  const isOff = !!tool.disabled
  return (
    <div className={"mcp-tool-card" + (isOff ? " disabled" : "")}>
      <div className="mcp-tool-head">
        <span className="mcp-tool-icon">{tool.custom ? "🛠" : "🔧"}</span>
        <span className="mcp-tool-name">{tool.name}</span>
        {tool.custom && <Badge tone="info">自定义</Badge>}
        {isOff && <Badge tone="muted">已禁用</Badge>}
      </div>
      <div className="mcp-tool-desc">{tool.description || "无描述"}</div>
      <div className="mcp-tool-foot">
        <span className="mcp-tool-cat">{tool.category}</span>
        {typeof tool.param_count === "number" && (
          <span className="mcp-tool-params">{tool.param_count} 参数</span>
        )}
        <div className="mcp-tool-actions">
          <button onClick={() => onToggle(tool.name, isOff)}>
            {isOff ? "启用" : "禁用"}
          </button>
          {tool.custom && onDelete && (
            <button className="danger" onClick={() => onDelete(tool.name)}>
              删除
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default ToolCard
