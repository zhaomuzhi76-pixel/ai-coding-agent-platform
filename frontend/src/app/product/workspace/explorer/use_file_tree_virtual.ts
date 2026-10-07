/**
 * 文件树虚拟滚动 hook。
 * 契约：返回滚动容器 ref + 可视区间；监听 scroll / resize，卸载即清理。
 */
import { useEffect, useRef, useState } from "react"

export interface VirtualRange {
  start: number
  end: number
  totalHeight: number
  offsetY: number
}

export function useFileTreeVirtual(
  rowCount: number,
  rowHeight: number,
  overscan = 8,
): {
  ref: React.RefObject<HTMLDivElement | null>
  range: VirtualRange
} {
  const ref = useRef<HTMLDivElement | null>(null)
  const [scrollTop, setScrollTop] = useState(0)
  const [viewportH, setViewportH] = useState(0)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const update = () => {
      setScrollTop(el.scrollTop)
      setViewportH(el.clientHeight)
    }
    update()
    el.addEventListener("scroll", update, { passive: true })
    let ro: ResizeObserver | null = null
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(update)
      ro.observe(el)
    }
    return () => {
      el.removeEventListener("scroll", update)
      if (ro) ro.disconnect()
    }
  }, [])

  const rowH = Math.max(1, Math.floor(rowHeight))
  const total = Math.max(0, Math.floor(rowCount))
  const totalHeight = total * rowH

  if (total === 0 || viewportH === 0) {
    return { ref, range: { start: 0, end: 0, totalHeight, offsetY: 0 } }
  }

  const firstVisible = Math.floor(scrollTop / rowH)
  const visibleCount = Math.ceil(viewportH / rowH) + 1
  const start = Math.max(0, firstVisible - overscan)
  const end = Math.min(total, firstVisible + visibleCount + overscan)
  const offsetY = start * rowH

  return { ref, range: { start, end, totalHeight, offsetY } }
}
