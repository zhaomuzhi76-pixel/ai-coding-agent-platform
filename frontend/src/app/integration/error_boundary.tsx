/**
 * ErrorBoundary: React 组件树异常兜底。
 * 契约：任何子组件抛错 → 显示错误面板（不再白屏）。
 */
import { Component, type ReactNode } from "react"

interface Props {
  children: ReactNode
  label?: string
  onError?: (error: Error, info: string) => void
}

interface State {
  error: Error | null
  info: string
}

const CRASH_KEY = "biancheng.last.crash"

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null, info: "" }

  static getDerivedStateFromError(error: Error): State {
    return { error, info: "" }
  }

  componentDidCatch(error: Error, info: { componentStack?: string }): void {
    const infoStr = info.componentStack || ""
    this.setState({ info: infoStr })
    // 记录到 localStorage 供下次启动诊断
    try {
      window.localStorage.setItem(
        CRASH_KEY,
        JSON.stringify({
          label: this.props.label || "app",
          message: String(error?.message || error),
          stack: String(error?.stack || ""),
          componentStack: infoStr,
          at: Date.now(),
        }),
      )
    } catch { /* quota */ }
    // eslint-disable-next-line no-console
    console.error("[app-crash]", this.props.label || "app", error, infoStr)
    this.props.onError?.(error, infoStr)
  }

  private reload = (): void => {
    window.location.reload()
  }

  private clearAndReload = (): void => {
    try {
      // 只清 UI 状态类 key（不动用户数据）
      for (const k of Object.keys(window.localStorage)) {
        if (k.startsWith("biancheng.workspace.base")
          || k.startsWith("biancheng.workspace.patches")
          || k.startsWith("biancheng.workspace.mode")
          || k.startsWith("biancheng.ai.workspace.mode")
          || k === CRASH_KEY) {
          window.localStorage.removeItem(k)
        }
      }
    } catch { /* noop */ }
    window.location.reload()
  }

  private copyError = (): void => {
    const text = [
      "=== APP CRASH ===",
      "label: " + (this.props.label || "app"),
      "message: " + String(this.state.error?.message || this.state.error),
      "stack:",
      String(this.state.error?.stack || ""),
      "componentStack:",
      this.state.info,
    ].join("\n")
    try {
      void navigator.clipboard?.writeText(text)
      alert("错误信息已复制到剪贴板")
    } catch {
      alert(text.slice(0, 2000))
    }
  }

  render(): ReactNode {
    const { error, info } = this.state
    if (!error) return this.props.children

    return (
      <div
        data-testid="app-error-boundary"
        style={{
          position: "fixed", inset: 0, zIndex: 99999,
          background: "#0b0f14", color: "#e7edf6",
          padding: 24, overflow: "auto",
          fontFamily: "ui-monospace, Menlo, Consolas, monospace",
          fontSize: 13, lineHeight: 1.6,
        }}
      >
        <div style={{
          maxWidth: 900, margin: "40px auto",
          padding: 24, borderRadius: 10,
          background: "rgba(239,133,133,.06)",
          border: "1px solid rgba(239,133,133,.35)",
        }}>
          <div style={{ fontSize: 20, marginBottom: 8, color: "#ef8585" }}>
            ⚠️ 页面渲染出错（已捕获）
          </div>
          <div style={{ color: "#b4c0d0", marginBottom: 16 }}>
            位置：{this.props.label || "app"} · 页面不会白屏，可点击下方按钮恢复
          </div>

          <div style={{
            padding: 12, borderRadius: 6, marginBottom: 16,
            background: "#09101a", color: "#c0cbda",
            whiteSpace: "pre-wrap", wordBreak: "break-word",
            maxHeight: 320, overflow: "auto",
          }}>
            <div style={{ color: "#e3b86d", marginBottom: 6 }}>
              {String(error.message || error)}
            </div>
            <details>
              <summary style={{ cursor: "pointer", color: "#77869a" }}>
                展开完整堆栈
              </summary>
              <div style={{ marginTop: 8, color: "#8795a5" }}>
                {String(error.stack || "")}
                {info && "\n\n--- componentStack ---\n" + info}
              </div>
            </details>
          </div>

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button
              type="button"
              onClick={this.reload}
              style={{
                padding: "8px 16px", borderRadius: 6,
                background: "#1f6feb", color: "#fff",
                border: 0, cursor: "pointer", fontSize: 13,
              }}
            >
              重新加载
            </button>
            <button
              type="button"
              onClick={this.clearAndReload}
              style={{
                padding: "8px 16px", borderRadius: 6,
                background: "#151f2a", color: "#d9e4ef",
                border: "1px solid #304052", cursor: "pointer", fontSize: 13,
              }}
            >
              清缓存并重载
            </button>
            <button
              type="button"
              onClick={this.copyError}
              style={{
                padding: "8px 16px", borderRadius: 6,
                background: "#151f2a", color: "#d9e4ef",
                border: "1px solid #304052", cursor: "pointer", fontSize: 13,
              }}
            >
              复制错误信息
            </button>
          </div>
        </div>
      </div>
    )
  }
}
