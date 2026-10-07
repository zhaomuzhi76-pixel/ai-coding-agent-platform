/**
 * 启动安全：清损坏 storage + 上报上次崩溃。
 * 契约：可重入、无副作用、幂等。
 */
const CRASH_KEY = "biancheng.last.crash"

function safeRemove(k: string): void {
  try { window.localStorage.removeItem(k) } catch { /* noop */ }
}

export function safeStartup(): void {
  if (typeof window === "undefined") return

  // 1. 检查损坏的 JSON key（非法 JSON → 清掉，防后续解析炸）
  const keysToCheck = [
    "biancheng.ai.workspace.base",
    "biancheng.ai.workspace.patches",
    "biancheng.ai.workspace.current",
    "biancheng.workspace.base",
    "biancheng.workspace.patches",
    "biancheng.workspace.current",
    "biancheng.ai.model.preference",
    "biancheng.theme",
    "biancheng.workspace.recent",
  ]
  for (const k of keysToCheck) {
    try {
      const raw = window.localStorage.getItem(k)
      if (raw === null) continue
      // theme 是纯字符串，不测 JSON
      if (k === "biancheng.theme") continue
      JSON.parse(raw)
    } catch {
      // eslint-disable-next-line no-console
      console.warn("[startup-safe] corrupt storage removed:", k)
      safeRemove(k)
    }
  }

  // 2. 上报上次崩溃（仅 Console，供用户诊断）
  try {
    const raw = window.localStorage.getItem(CRASH_KEY)
    if (raw) {
      const crash = JSON.parse(raw)
      // eslint-disable-next-line no-console
      console.warn("[startup-safe] previous crash:", crash)
      safeRemove(CRASH_KEY)
    }
  } catch {
    safeRemove(CRASH_KEY)
  }
}
