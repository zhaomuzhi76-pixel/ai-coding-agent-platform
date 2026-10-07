/**
 * 连接状态机 + 代际号。
 * Owns: 状态枚举与转移 / 代际号分配（防旧回调干扰新连接）
 * Not:  WebSocket 实例 / 重连策略 / 消息解码
 */

export type SocketPhase =
  | "idle" | "connecting" | "open" | "reconnecting" | "closed"

export interface SocketState {
  phase: SocketPhase
  generation: number
  attempts: number
}

export function initialState(): SocketState {
  return { phase: "idle", generation: 0, attempts: 0 }
}

export function bumpGeneration(state: SocketState): number {
  state.generation += 1
  return state.generation
}

export function isCurrent(state: SocketState, generation: number): boolean {
  return state.generation === generation
}
