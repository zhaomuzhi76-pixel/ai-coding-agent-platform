/**
 * 多模态输入收集。职责：收集文本 / 图片 / 音频 / want_image。
 * 不调 API、不做选择器联动、不做响应渲染。
 */
import { useState } from "react"

export interface ComposerPayload {
  text: string
  images: string[]
  audios: string[]
  want_image: boolean
}

interface Props {
  busy?: boolean
  disabled?: boolean
  onSubmit: (p: ComposerPayload) => void
}

function fileToB64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => {
      const s = String(r.result || "")
      const i = s.indexOf(",")
      resolve(i >= 0 ? s.slice(i + 1) : s)
    }
    r.onerror = () => reject(r.error)
    r.readAsDataURL(file)
  })
}

export function MultimodalComposer({ busy, disabled, onSubmit }: Props) {
  const [text, setText] = useState("")
  const [images, setImages] = useState<string[]>([])
  const [audios, setAudios] = useState<string[]>([])
  const [wantImage, setWantImage] = useState(false)

  const pick = async (kind: "image" | "audio", files: FileList | null) => {
    if (!files || files.length === 0) return
    const bufs: string[] = []
    for (const f of Array.from(files)) bufs.push(await fileToB64(f))
    if (kind === "image") setImages((p) => [...p, ...bufs])
    else setAudios((p) => [...p, ...bufs])
  }

  const send = () => {
    if (!text.trim() && images.length === 0) return
    onSubmit({ text, images, audios, want_image: wantImage })
    setText(""); setImages([]); setAudios([]); setWantImage(false)
  }

  const locked = !!busy || !!disabled

  return (
    <div style={{ display: "grid", gap: 10 }}>
      <textarea
        className="ind-input"
        rows={4}
        value={text}
        disabled={locked}
        placeholder="输入消息…（可与图片/音频一起发送）"
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) send()
        }}
        style={{ width: "100%", resize: "vertical", fontSize: 13 }}
      />

      <div style={{
        display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap",
      }}>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
          <span style={{ opacity: 0.7 }}>图片</span>
          <input type="file" accept="image/*" multiple disabled={locked}
            onChange={(e) => void pick("image", e.target.files)}
            style={{ fontSize: 12 }} />
          {images.length > 0 && <span style={{ opacity: 0.6 }}>({images.length})</span>}
        </label>

        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
          <span style={{ opacity: 0.7 }}>音频</span>
          <input type="file" accept="audio/*" multiple disabled={locked}
            onChange={(e) => void pick("audio", e.target.files)}
            style={{ fontSize: 12 }} />
          {audios.length > 0 && <span style={{ opacity: 0.6 }}>({audios.length})</span>}
        </label>

        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
          <input type="checkbox" checked={wantImage} disabled={locked}
            onChange={(e) => setWantImage(e.target.checked)} />
          同时生成图片
        </label>

        <button
          className="ind-btn ind-btn--primary"
          style={{ marginLeft: "auto" }}
          disabled={locked || (!text.trim() && images.length === 0)}
          onClick={send}
        >{busy ? "发送中…" : "发送"}</button>
      </div>

      <div style={{ fontSize: 11, opacity: 0.5 }}>
        待发送：{images.length} 图 / {audios.length} 音频 · Ctrl+Enter 快捷发送
      </div>
    </div>
  )
}
