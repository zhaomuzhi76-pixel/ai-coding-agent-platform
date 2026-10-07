/**
 * 全局错误捕获（同步 + 异步 + 资源加载）。
 * 契约：任何未捕获错误 → Console [app-crash] + 记录 localStorage。
 */
const CRASH_KEY = "biancheng.last.crash"

function record(tag: string, payload: Record<string, unknown>): void {
  try {
    window.localStorage.setItem(
      CRASH_KEY,
      JSON.stringify({ tag, at: Date.now(), ...payload }),
    )
  } catch { /* quota */ }
}

export function installGlobalErrorHandler(): void {
  if (typeof window === "undefined") return
  const w = window as unknown as { __appErrorHandlerInstalled?: boolean }
  if (w.__appErrorHandlerInstalled) return
  w.__appErrorHandlerInstalled = true

  // 1. 同步错误
  window.addEventListener("error", (ev) => {
    const e = ev.error
    const message = ev.message || (e && e.message) || "unknown"
    // eslint-disable-next-line no-console
    console.error("[app-crash] window.error", message, ev.filename, ev.lineno, e)
    record("window.error", {
      message: String(message),
      filename: ev.filename,
      lineno: ev.lineno,
      stack: e ? String(e.stack || "") : "",
    })
  })

  // 2. 未处理的 Promise 拒绝
  window.addEventListener("unhandledrejection", (ev) => {
    const r = ev.reason
    const message = (r && (r.message || String(r))) || "unknown"
    // eslint-disable-next-line no-console
    console.error("[app-crash] unhandledrejection", r)
    record("unhandledrejection", {
      message: String(message),
      stack: r && r.stack ? String(r.stack) : "",
    })
  })

  // 3. Vite 动态 chunk 加载失败（HMR/网络抖动）→ 自动 reload 一次
  window.addEventListener("vite:preloadError", () => {
    // eslint-disable-next-line no-console
    console.warn("[app-crash] vite:preloadError → reload once")
    const FLAG = "biancheng.preload.reloaded"
    try {
      if (!sessionStorage.getItem(FLAG)) {
        sessionStorage.setItem(FLAG, "1")
        window.location.reload()
      }
    } catch { /* noop */ }
  })
}
