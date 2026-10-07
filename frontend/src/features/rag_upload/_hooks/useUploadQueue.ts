// [FIX_OVERWRITE]
/** 队列层：管理 pending File[] + IndexedDB 持久化 */
import { useCallback, useEffect, useState } from "react"
import {
  savePendingFiles, loadPendingFiles, clearPendingFiles,
} from "../persistence/pending_store"

export function useUploadQueue(restored: boolean) {
  const [pending, setPending] = useState<File[]>([])

  // 初始恢复
  useEffect(() => {
    if (!restored) return
    ;(async () => {
      const files = await loadPendingFiles()
      if (files.length > 0) {
        console.log("[useUploadQueue] restored from IDB:", files.length)
        // [FIX_OVERWRITE] 只在 pending 为空时恢复，避免覆盖新加的文件
        setPending((prev) => prev.length === 0 ? files : prev)
      }
    })()
  }, [restored])

  // pending 变化 → 写 IndexedDB
  useEffect(() => {
    if (!restored) return
    if (pending.length === 0) void clearPendingFiles()
    else void savePendingFiles(pending)
  }, [pending, restored])

  // ★ 改为接收 File[]（已在 Dropzone 层做过 FileList → File[] 快照）
  const add = useCallback((files: File[]) => {
    if (!files || files.length === 0) return
    console.log("[useUploadQueue.add] received:", files.length)
    setPending((prev) => [...prev, ...files])
  }, [])

  const remove = useCallback((idx: number) => {
    setPending((prev) => prev.filter((_, i) => i !== idx))
  }, [])

  const clear = useCallback(async () => {
    setPending([])
    await clearPendingFiles()
  }, [])

  return { pending, add, remove, clear }
}
