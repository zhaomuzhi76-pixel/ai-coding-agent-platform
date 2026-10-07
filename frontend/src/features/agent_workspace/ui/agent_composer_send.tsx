/** Agent composer 发送按钮（含状态）。 */
export function AgentComposerSend({
  executing, unavailable,
}: {
  executing: boolean
  unavailable: boolean
}) {
  return (
    <button
      type="submit"
      className="agent-composer__send"
      disabled={unavailable}
      aria-label={
        executing ? "Agent is running" : "Send message to Agent"
      }
    >
      <span>{executing ? "Running" : "Send"}</span>
      <span className="agent-composer__send-icon" aria-hidden="true">↑</span>
    </button>
  )
}
