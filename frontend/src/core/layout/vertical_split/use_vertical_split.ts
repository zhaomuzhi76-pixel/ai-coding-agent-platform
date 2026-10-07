import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type PointerEvent,
  type RefObject,
} from "react"

const MIN_RATIO = 0.15
const MAX_RATIO = 0.85
const COLLAPSE_RATIO = 0.999

export interface UseVerticalSplitOptions {
  storageKey: string
  defaultRatio?: number
  minRatio?: number
  maxRatio?: number
}

export interface VerticalSplitApi {
  ratio: number
  isDragging: boolean
  containerRef: RefObject<HTMLElement | null>
  onHandlePointerDown: (event: PointerEvent<HTMLDivElement>) => void
  onHandleDoubleClick: () => void
  onHandleKeyDown: (event: KeyboardEvent<HTMLDivElement>) => void
}

function clamp(v: number, lo: number, hi: number): number {
  return v < lo ? lo : v > hi ? hi : v
}

function readStored(key: string): number | null {
  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return null
    const n = Number.parseFloat(raw)
    return Number.isFinite(n) ? n : null
  } catch {
    return null
  }
}

function writeStored(key: string, value: number): void {
  try {
    window.localStorage.setItem(key, String(value))
  } catch {
    /* localStorage 不可用时静默降级 */
  }
}

export function useVerticalSplit(
  opts: UseVerticalSplitOptions,
): VerticalSplitApi {
  const {
    storageKey,
    defaultRatio = 0.62,
    minRatio = MIN_RATIO,
    maxRatio = MAX_RATIO,
  } = opts

  const containerRef = useRef<HTMLElement | null>(null)
  const [ratio, setRatio] = useState<number>(() => {
    const stored = readStored(storageKey)
    return clamp(stored ?? defaultRatio, minRatio, maxRatio)
  })
  const [isDragging, setIsDragging] = useState(false)
  const lastExpanded = useRef<number>(ratio)

  // 拖拽事件（pointer events：兼容鼠标 + 触屏 + 笔）
  const onHandlePointerDown = useCallback(
    (event: PointerEvent<HTMLDivElement>) => {
      if (event.button !== 0) return
      const handleEl = event.currentTarget as HTMLElement
      const container =
        (handleEl.parentElement as HTMLElement | null)
        ?? containerRef.current
      if (!container) return
      event.preventDefault()

      const rect = container.getBoundingClientRect()
      const startY = event.clientY
      const startRatio = ratio
      const h = rect.height || 1

      setIsDragging(true)
      document.body.classList.add("vertical-split--dragging")

      const onMove = (ev: globalThis.PointerEvent) => {
        const delta = (ev.clientY - startY) / h
        const next = clamp(startRatio + delta, minRatio, maxRatio)
        setRatio(next)
        if (next > minRatio + 0.001 && next < maxRatio - 0.001) {
          lastExpanded.current = next
        }
      }

      const onUp = () => {
        setIsDragging(false)
        document.body.classList.remove("vertical-split--dragging")
        window.removeEventListener("pointermove", onMove)
        window.removeEventListener("pointerup", onUp)
        window.removeEventListener("pointercancel", onUp)
        setRatio((r) => {
          writeStored(storageKey, r)
          return r
        })
      }

      window.addEventListener("pointermove", onMove)
      window.addEventListener("pointerup", onUp)
      window.addEventListener("pointercancel", onUp)
    },
    [ratio, minRatio, maxRatio, storageKey],
  )

  // 双击：折叠 / 展开（VSCode 行为）
  const onHandleDoubleClick = useCallback(() => {
    setRatio((r) => {
      const next =
        r >= COLLAPSE_RATIO
          ? clamp(lastExpanded.current, minRatio, maxRatio)
          : COLLAPSE_RATIO
      writeStored(storageKey, next)
      return next
    })
  }, [minRatio, maxRatio, storageKey])

  // 键盘可访问：上下箭头 ±2%，Home = 默认比例
  const onHandleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>) => {
      const step = 0.02
      let next: number | null = null
      if (event.key === "ArrowUp") next = ratio - step
      else if (event.key === "ArrowDown") next = ratio + step
      else if (event.key === "Home") next = defaultRatio
      if (next === null) return
      event.preventDefault()
      const clamped = clamp(next, minRatio, maxRatio)
      setRatio(clamped)
      lastExpanded.current = clamped
      writeStored(storageKey, clamped)
    },
    [ratio, defaultRatio, minRatio, maxRatio, storageKey],
  )

  // 卸载时清理 body class（防止 HMR 残留）
  useEffect(() => {
    return () => {
      document.body.classList.remove("vertical-split--dragging")
    }
  }, [])

  return {
    ratio,
    isDragging,
    containerRef,
    onHandlePointerDown,
    onHandleDoubleClick,
    onHandleKeyDown,
  }
}
