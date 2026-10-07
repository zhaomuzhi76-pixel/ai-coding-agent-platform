/** 模型首次调用提示（本地显存换入 6~12s）。 */
export function AgentWarmupHint({ show }: { show: boolean }) {
  if (!show) return null
  return (
    <div
      data-testid="model-warmup-hint"
      style={{
        padding: "6px 10px",
        marginBottom: 6,
        borderRadius: 6,
        fontSize: 11,
        background: "rgba(227,184,109,.08)",
        border: "1px solid rgba(227,184,109,.25)",
        color: "#e3b86d",
        fontFamily: "ui-monospace, monospace",
      }}
    >
      ⏳ 首次调用该模型预计 6~12s（本地显存换入）；同模型后续请求约 2s
    </div>
  )
}
