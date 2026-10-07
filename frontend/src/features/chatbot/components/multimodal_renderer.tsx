/**
 * 多模态响应渲染。职责：把 {text, images[]} 渲染为 DOM。
 * 显示：领域 / 输出模式 / RAG 命中数 / 图片来源角标。
 */
import type { ChatReply, ImageOut } from "../../../core/api/chatbot_api"

const SOURCE_LABEL: Record<string, { text: string; color: string }> = {
  retrieved:  { text: "知识库",  color: "#4a90e2" },
  generated:  { text: "AI 生成", color: "#e29e4a" },
  input_echo: { text: "上传",    color: "#888" },
}

function imgSrc(a: ImageOut): string | null {
  if (a.url) return a.url
  if (a.b64) return `data:${a.mime};base64,${a.b64}`
  return null
}

interface Props { reply: ChatReply | null; error?: string | null }

export function MultimodalRenderer({ reply, error }: Props) {
  if (error) return (
    <div style={{
      padding: "10px 12px", borderRadius: 6,
      background: "rgba(239,133,133,.08)",
      border: "1px solid rgba(239,133,133,.35)",
      color: "#ef8585", fontSize: 12,
    }}>错误：{error}</div>
  )
  if (!reply) return null

  const { response, domain, output_mode, reason } = reply
  const ragHits = Number(response.meta?.["rag_hits"] ?? 0)

  return (
    <div style={{ display: "grid", gap: 10 }}>
      <div style={{
        display: "flex", gap: 8, flexWrap: "wrap",
        fontSize: 11, opacity: 0.75,
      }}>
        <span style={{
          padding: "1px 6px", borderRadius: 3,
          background: "rgba(118,169,255,.12)",
        }}>领域 {domain}</span>
        <span style={{
          padding: "1px 6px", borderRadius: 3,
          background: "rgba(118,169,255,.12)",
        }}>{output_mode}</span>
        {reason && <span style={{ opacity: 0.6 }}>{reason}</span>}
        {ragHits > 0 && (
          <span style={{
            background: "#4a90e2", color: "#fff",
            padding: "1px 8px", borderRadius: 3, fontWeight: 600,
          }}>引用了 {ragHits} 条知识</span>
        )}
      </div>

      <div style={{
        whiteSpace: "pre-wrap", fontSize: 13, lineHeight: 1.7,
        padding: "10px 12px", borderRadius: 6,
        background: "rgba(255,255,255,.02)",
        border: "1px solid rgba(118,169,255,.15)",
      }}>{response.text}</div>

      {response.images.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          {response.images.map((a) => {
            const src = imgSrc(a)
            const tag = SOURCE_LABEL[a.source] ?? { text: a.source, color: "#888" }
            return (
              <div key={a.id} style={{ position: "relative", display: "inline-block" }}>
                {src ? (
                  <img src={src} alt={a.alt_text || a.id}
                    style={{
                      maxWidth: 260, borderRadius: 6, display: "block",
                      border: "1px solid rgba(118,169,255,.2)",
                    }} />
                ) : (
                  <div style={{
                    opacity: 0.5, padding: 12, fontSize: 11,
                    border: "1px dashed rgba(118,169,255,.3)", borderRadius: 6,
                  }}>[image {a.id}]</div>
                )}
                <span style={{
                  position: "absolute", top: 6, left: 6,
                  background: tag.color, color: "#fff",
                  fontSize: 10, padding: "1px 6px", borderRadius: 3,
                  fontWeight: 600,
                }}>{tag.text}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
