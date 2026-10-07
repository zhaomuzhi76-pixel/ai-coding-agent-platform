import { useCallback, useEffect, useRef } from "react"
import "./sidebar_resizer.css"

const MIN_W = 160
const MAX_W = 640
const KEY = "biancheng.ide.sidebar.width"

function readStored(): number | null {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return null
    const n = parseFloat(raw)
    return Number.isFinite(n) ? n : null
  } catch {
    return null
  }
}

function applyWidth(w: number) {
  document.documentElement.style.setProperty("--sidebar-width", `${w}px`)
}

export function SidebarResizer() {
  const dragging = useRef(false)

  useEffect(() => {
    const w = readStored()
    if (w) applyWidth(w)
  }, [])

  const onDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    const startX = e.clientX
    const sidebarEl = document.querySelector(
      ".ide-workspace-sidebar",
    ) as HTMLElement | null
    const startW = sidebarEl
      ? sidebarEl.getBoundingClientRect().width
      : readStored() ?? 248
    dragging.current = true
    document.body.classList.add("sidebar-resize--active")

    const onMove = (ev: MouseEvent) => {
      if (!dragging.current) return
      const w = Math.max(MIN_W, Math.min(MAX_W, startW + (ev.clientX - startX)))
      applyWidth(w)
    }
    const onUp = () => {
      if (!dragging.current) return
      dragging.current = false
      document.body.classList.remove("sidebar-resize--active")
      window.removeEventListener("mousemove", onMove)
      window.removeEventListener("mouseup", onUp)
      const w = getComputedStyle(document.documentElement)
        .getPropertyValue("--sidebar-width")
      try {
        localStorage.setItem(KEY, w.replace("px", "").trim())
      } catch {
        /* ignore */
      }
    }
    window.addEventListener("mousemove", onMove)
    window.addEventListener("mouseup", onUp)
  }, [])

  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label="Resize sidebar"
      className="sidebar-resizer"
      style={{
        position: "absolute",
        top: 0,
        bottom: 0,
        left: "calc(var(--sidebar-width, 248px) - 5px)",
        width: "10px",
        cursor: "col-resize",
        zIndex: 200,
      }}
      onMouseDown={onDown}
    />
  )
}
