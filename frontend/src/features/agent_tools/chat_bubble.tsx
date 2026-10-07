/** 消息气泡。职责：渲染单轮 user/assistant + 工具链。 */
import type { AgentChatReply } from "../../core/api/agent_tools_api"
import { ChatTrace } from "./chat_trace"

interface Turn {
  user: string
  reply?: AgentChatReply
  error?: string
}

interface Props { turn: Turn }

export function ChatBubble({ turn }: Props) {
  return (
    <div style={{ display: "grid", gap: 8 }}>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <div style={{
          maxWidth: "75%", padding: "8px 12px", borderRadius: 10,
          background: "rgba(118,169,255,.18)",
          border: "1px solid rgba(118,169,255,.3)",
          fontSize: 13, whiteSpace: "pre-wrap", lineHeight: 1.6,
        }}>{turn.user}</div>
      </div>

      {turn.error && (
        <div style={{ display: "flex" }}>
          <div style={{
            maxWidth: "85%", padding: "8px 12px", borderRadius: 10,
            background: "rgba(239,133,133,.08)",
            border: "1px solid rgba(239,133,133,.3)",
            color: "#ef8585", fontSize: 12,
          }}>错误：{turn.error}</div>
        </div>
      )}

      {turn.reply && (
        <div style={{ display: "flex" }}>
          <div style={{
            maxWidth: "85%", padding: "10px 14px", borderRadius: 10,
            background: "rgba(255,255,255,.03)",
            border: "1px solid rgba(118,169,255,.15)",
            fontSize: 13, lineHeight: 1.7, whiteSpace: "pre-wrap",
          }}>
            {turn.reply.answer}
                {/* [IMG_RENDER] 图文同返 */}
                {(() => {
                  const imgs: any[] = []
                  for (const im of (turn.reply.images || [])) imgs.push(im)
                  for (const t of (turn.reply.tool_trace || [])) {
                    const ms = (t.meta as any)?.images
                    if (Array.isArray(ms)) for (const im of ms) imgs.push(im)
                  }
                  if (imgs.length === 0) return null
                  const seen = new Set<string>()
                  const uniq = imgs.filter((im: any) => {
                    const k = im?.id || im?.url || ""
                    if (!k || seen.has(k)) return false
                    seen.add(k); return true
                  })
                  return (
                    <div style={{
                      display: "flex", gap: 8, flexWrap: "wrap",
                      marginTop: 10, paddingTop: 8,
                      borderTop: "1px dashed rgba(118,169,255,.15)",
                    }}>
                      {uniq.slice(0, 8).map((im: any) => {
                        const s = im.url || ""
                        if (!s) return null
                        return (
                          <a key={im.id} href={s} target="_blank"
                             rel="noreferrer" title={im.alt_text || im.id}>
                            <img src={s} alt={im.alt_text || im.id}
                                 style={{
                                   maxWidth: 130, maxHeight: 130,
                                   borderRadius: 6, display: "block",
                                   border: "1px solid rgba(118,169,255,.3)",
                                   cursor: "zoom-in",
                                 }} />
                          </a>
                        )
                      })}
                    </div>
                  )
                })()}
            <ChatTrace trace={turn.reply.tool_trace} />
            {turn.reply.steps > 0 && (
              <div style={{
                marginTop: 6, fontSize: 10, opacity: 0.45,
                borderTop: "1px dashed rgba(118,169,255,.15)", paddingTop: 4,
              }}>
                {turn.reply.steps} 步 · 调工具 {turn.reply.tool_trace.length} 次
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
