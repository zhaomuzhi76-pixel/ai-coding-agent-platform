/**
 * Apply WS 订阅者：/ws/platform/apply/{task_id}。
 *
 * 与 finetune/ws/deploy_socket 领域不同（不重复职责）：
 *   - deploy_socket 连 finetune 部署（adapter 领域）
 *   - apply_socket  连 platform 代码应用（proposal 领域）
 */

function backendHost(): string {
  if (typeof window === "undefined") return "127.0.0.1:9022"
  const port = window.location.port
  if (port === "9022") return window.location.host
  return "127.0.0.1:9022"
}

export function openApplySocket(taskId: string): WebSocket {
  const proto = window.location.protocol === "https:" ? "wss" : "ws"
  return new WebSocket(
    `${proto}://${backendHost()}/ws/platform/apply/${taskId}`,
  )
}

export type { WebSocket }
