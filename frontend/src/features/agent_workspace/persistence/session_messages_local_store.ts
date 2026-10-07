/**
 * Session messages 本地持久化。
 *
 * 工业级契约（对齐 Claude Code 的 session.jsonl 本地存储）：
 *   - 每个 session_id 一份独立记录
 *   - 切换/关闭浏览器后仍可恢复
 *   - 上限 500 条，超出丢最早的
 *   - localStorage 不可用时静默降级
 *
 * 纯函数，无副作用依赖，不 import React。
 */
import type { AgentRuntimeMessage } from "../../../core/contracts/execution_event"

const KEY_PREFIX = "biancheng.ai.session.messages."
const LIMIT = 500

function keyFor(sessionId: string): string {
  return KEY_PREFIX + sessionId
}

export function saveMessages(
  sessionId: string,
  messages: readonly AgentRuntimeMessage[],
): void {
  const sid = sessionId?.trim()
  if (!sid) return
  try {
    const trimmed =
      messages.length > LIMIT
        ? messages.slice(messages.length - LIMIT)
        : messages
    window.localStorage.setItem(
      keyFor(sid),
      JSON.stringify(trimmed),
    )
  } catch {
    /* quota / 隐私模式 → 静默降级 */
  }
}

export function loadMessages(
  sessionId: string,
): AgentRuntimeMessage[] {
  const sid = sessionId?.trim()
  if (!sid) return []
  try {
    const raw = window.localStorage.getItem(keyFor(sid))
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed)
      ? (parsed as AgentRuntimeMessage[])
      : []
  } catch {
    return []
  }
}

export function clearMessages(sessionId: string): void {
  const sid = sessionId?.trim()
  if (!sid) return
  try {
    window.localStorage.removeItem(keyFor(sid))
  } catch {
    /* ignore */
  }
}

export function listStoredSessionIds(): string[] {
  const out: string[] = []
  try {
    for (let i = 0; i < window.localStorage.length; i++) {
      const k = window.localStorage.key(i)
      if (k && k.startsWith(KEY_PREFIX)) {
        out.push(k.slice(KEY_PREFIX.length))
      }
    }
  } catch {
    /* ignore */
  }
  return out
}

export const SESSION_MESSAGES_LIMIT = LIMIT
