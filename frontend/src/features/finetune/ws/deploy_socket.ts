/**
 * Deploy WS 订阅者：/ws/finetune/deploy/{task_id}。
 *
 * Owns:
 *   - URL 构造（按 task_id）
 *   - 原生 WebSocket（部署窗口 ~15-30s，无需重连）
 *
 * Not:
 *   - 事件累积（use_deploy_task 管）
 *   - UI 渲染（adapter_panel 管）
 */

function backendHost(): string {
  if (typeof window === "undefined") return "127.0.0.1:9022"
  const port = window.location.port
  if (port === "9022") return window.location.host
  return "127.0.0.1:9022"
}

export function openDeploySocket(taskId: string): WebSocket {
  const proto = window.location.protocol === "https:" ? "wss" : "ws"
  return new WebSocket(
    `${proto}://${backendHost()}/ws/finetune/deploy/${taskId}`,
  )
}

export type { WebSocket }
