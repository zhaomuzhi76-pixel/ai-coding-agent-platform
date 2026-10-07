/** MCP 管理页 —— 已替换为工业级 McpDashboard */
import { McpDashboard } from "../../../features/mcp_client/McpDashboard"

export function McpPage() {
  return (
    <div style={{ width: "100%", height: "100%" }}>
      <McpDashboard />
    </div>
  )
}

export default McpPage
