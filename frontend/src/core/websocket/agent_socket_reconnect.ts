/**
 * 指数退避重连策略。
 * Owns: 退避时间计算（指数+抖动+上限）/ 重连计数
 * Not:  WebSocket 实例 / 状态机 / 事件回调
 */

export interface ReconnectConfig {
  readonly baseMs: number
  readonly maxMs: number
  readonly maxAttempts: number
  readonly jitterRatio: number
}

export const DEFAULT_RECONNECT: ReconnectConfig = {
  baseMs: 500, maxMs: 30_000, maxAttempts: 8, jitterRatio: 0.5,
}

export function nextDelay(
  attempt: number,
  config: ReconnectConfig = DEFAULT_RECONNECT,
): number {
  const exp = Math.min(
    config.baseMs * Math.pow(2, Math.max(0, attempt)),
    config.maxMs,
  )
  const jitter = exp * config.jitterRatio * (Math.random() * 2 - 1)
  return Math.max(0, Math.floor(exp + jitter))
}

export function shouldRetry(
  attempt: number,
  config: ReconnectConfig = DEFAULT_RECONNECT,
): boolean {
  return attempt < config.maxAttempts
}
