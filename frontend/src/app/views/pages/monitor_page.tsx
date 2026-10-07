/** 监控面板 —— 已替换为工业级 LlmMonitorDashboard */
import { LlmMonitorDashboard } from "../../../features/monitor/dashboard/LlmMonitorDashboard"
import { SystemResourcePanel } from "../../../features/monitor/ui/SystemResourcePanel"
import { PipelineIdlePanel } from "../../../features/monitor/ui/PipelineIdlePanel"

export function MonitorPage() {
  return (
    <div style={{ width: "100%", height: "100%" }}>
      <SystemResourcePanel />
      <PipelineIdlePanel />
      <LlmMonitorDashboard />
    </div>
  )
}

export default MonitorPage