/** 模型切换提示 hook：切模型后 N 秒内显示"首次加载中"。 */
import { useEffect, useRef, useState } from "react"

const HINT_MS = 8000

export function useModelWarmupHint(currentModel: string) {
  const [show, setShow] = useState(false)
  const prevRef = useRef<string>(currentModel)

  useEffect(() => {
    const prev = prevRef.current
    const next = currentModel
    if (prev && prev !== next) {
      setShow(true)
      prevRef.current = next
      const t = setTimeout(() => setShow(false), HINT_MS)
      return () => clearTimeout(t)
    }
    prevRef.current = next
  }, [currentModel])

  return { showModelWarmupHint: show }
}
