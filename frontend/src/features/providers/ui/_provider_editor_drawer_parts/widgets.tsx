/* ProviderEditorDrawer 子组件：状态条 + 表单字段。 */
import type React from "react"
import type { TestResult } from "../../../core/api/providers_api"

export function TestStatusBar(props: {
  status: "idle" | "testing" | "success" | "error"
  result: TestResult | null
  error: string | null
}) {
  const { status, result, error } = props

  let bg = "#1a2330"
  let border = "#2b3b51"
  let iconColor = "#68778b"
  let icon = "○"
  let title = "未测试"
  let detail = "填写表单后点「测试连接」验证可用性"
  let spin = false

  if (status === "testing") {
    bg = "rgba(122,162,247,.10)"
    border = "rgba(122,162,247,.5)"
    iconColor = "#7aa2f7"
    icon = "◐"
    title = "正在测试连接…"
    detail = "真实调用远程 API，请稍候"
    spin = true
  } else if (status === "success" && result) {
    bg = "rgba(74,222,128,.10)"
    border = "rgba(74,222,128,.5)"
    iconColor = "#4ade80"
    icon = "✓"
    title = "连接成功"
    detail = `${result.models_count || 0} 个模型 · ${result.latency_ms?.toFixed(0) ?? "?"}ms`
  } else if (status === "error") {
    bg = "rgba(239,133,133,.10)"
    border = "rgba(239,133,133,.5)"
    iconColor = "#ef8585"
    icon = "✗"
    title = "连接失败"
    detail = result?.error || error || "未知错误"
  }

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "12px 14px",
        marginBottom: 14,
        borderRadius: 8,
        background: bg,
        border: `1.5px solid ${border}`,
        transition: "all .15s ease",
      }}
    >
      <div
        style={{
          fontSize: 22,
          lineHeight: 1,
          color: iconColor,
          animation: spin
            ? "spin 0.9s linear infinite"
            : undefined,
        }}
      >
        {icon}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: iconColor,
            marginBottom: 2,
          }}
        >
          {title}
        </div>
        <div
          style={{
            fontSize: 11.5,
            color: "#a8b8cd",
            wordBreak: "break-all",
          }}
        >
          {detail}
        </div>
      </div>
      {status === "success" && (
        <div
          style={{
            fontSize: 10,
            padding: "2px 8px",
            borderRadius: 4,
            background: "rgba(74,222,128,.20)",
            color: "#4ade80",
            fontWeight: 600,
            letterSpacing: 0.5,
          }}
        >
          READY
        </div>
      )}
      {status === "error" && (
        <div
          style={{
            fontSize: 10,
            padding: "2px 8px",
            borderRadius: 4,
            background: "rgba(239,133,133,.20)",
            color: "#ef8585",
            fontWeight: 600,
            letterSpacing: 0.5,
          }}
        >
          BLOCKED
        </div>
      )}
    </div>
  )
}

export function Field(props: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{
        fontSize: 11, color: "var(--muted)",
        marginBottom: 4, textTransform: "uppercase",
        letterSpacing: 0.4,
      }}>
        {props.label}
      </div>
      {props.children}
    </div>
  )
}
