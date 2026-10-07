/**
 * 文件选择区。职责：点击 → 系统文件资源管理器 → 收文件（立即快照为 File[]）。
 * 风格：原生"打开文件"按钮（无拖拽）
 */
import { useRef } from "react"

const ACCEPT = ".pdf,.md,.markdown,.txt,.log,.jpg,.jpeg,.png,.bmp,.webp," +
  ".tif,.tiff,.docx,.xlsx,.pptx,.html,.htm"

interface Props {
  busy?: boolean
  kbLabel?: string
  onFiles: (files: File[]) => void
}

export function UploadDropzone({ busy, kbLabel, onFiles }: Props) {
  const ref = useRef<HTMLInputElement>(null)

  const pick = () => {
    if (busy) return
    ref.current?.click()
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const list = e.target.files
    if (!list || list.length === 0) {
      console.log("[dropzone] onChange fired, files empty")
      return
    }
    let files = Array.from(list)
    // [MAX_5] 最多 5 个文件
    const MAX_FILES = 5
    if (files.length > MAX_FILES) {
      console.warn(`[dropzone] 一次最多 ${MAX_FILES} 个文件，已截断`)
      files = files.slice(0, MAX_FILES)
    }
    console.log("[dropzone] onChange fired, files=", files.length, files.map(f => f.name))
    e.target.value = ""
    onFiles(files)
  }

  return (
    <div
      style={{
        width: "100%",
        border: "1px solid rgba(118,169,255,.25)",
        borderRadius: 8,
        background: "rgba(118,169,255,.03)",
        padding: "16px 18px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 10,
      }}
    >
      {/* 标题行 */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 20 }}>📁</span>
        <span style={{ fontSize: 13, fontWeight: 500, color: "var(--text, #e8e8ea)" }}>
          选择要上传的文件
        </span>
      </div>

      {/* 支持格式提示 */}
      <div style={{ fontSize: 11, opacity: 0.5, textAlign: "center", lineHeight: 1.5 }}>
        PDF / 图片 / Word / Excel / PPT / HTML / MD / TXT · ≤1GB
      </div>

      {/* 原生风格主按钮 */}
      <button
        type="button"
        onClick={pick}
        disabled={busy}
        style={{
          marginTop: 4,
          padding: "8px 20px",
          fontSize: 13,
          fontWeight: 500,
          color: "#fff",
          background: busy ? "rgba(122,162,247,.4)" : "#5b8def",
          border: "1px solid transparent",
          borderRadius: 6,
          cursor: busy ? "wait" : "pointer",
          font: "inherit",
          transition: "background .12s",
          minWidth: 140,
        }}
        onMouseEnter={(e) => {
          if (!busy) e.currentTarget.style.background = "#4a7ce0"
        }}
        onMouseLeave={(e) => {
          if (!busy) e.currentTarget.style.background = "#5b8def"
        }}
      >
        {busy ? "上传中…" : "浏览文件…"}
      </button>

      {/* 领域标签 */}
      {kbLabel && (
        <div style={{ fontSize: 11, opacity: 0.4 }}>
          领域：{kbLabel}
        </div>
      )}

      {/* 隐藏的原生文件选择器 */}
      <input
        ref={ref}
        type="file"
        multiple
        accept={ACCEPT}
        disabled={busy}
        onChange={handleChange}
        style={{ display: "none" }}
      />
    </div>
  )
}

export default UploadDropzone
