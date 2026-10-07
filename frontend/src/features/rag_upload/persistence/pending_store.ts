/** 待处理文件队列的 IndexedDB 持久化（刷新不丢） */
const DB_NAME = "biancheng_rag_upload"
const DB_VERSION = 1
const STORE = "pending_files"

interface PendingRecord {
  id: number
  name: string
  size: number
  lastModified: number
  type: string
  blob: Blob
  addedAt: number
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "id", autoIncrement: true })
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

export async function savePendingFiles(files: File[]): Promise<void> {
  try {
    const db = await openDB()
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite")
      const store = tx.objectStore(STORE)
      store.clear()
      for (const f of files) {
        store.add({
          name: f.name, size: f.size, lastModified: f.lastModified,
          type: f.type, blob: f, addedAt: Date.now(),
        } as PendingRecord)
      }
      tx.oncomplete = () => { db.close(); resolve() }
      tx.onerror = () => { db.close(); reject(tx.error) }
    })
  } catch { /* 隐私模式忽略 */ }
}

export async function loadPendingFiles(): Promise<File[]> {
  try {
    const db = await openDB()
    return await new Promise<File[]>((resolve, reject) => {
      const tx = db.transaction(STORE, "readonly")
      const req = tx.objectStore(STORE).getAll()
      req.onsuccess = () => {
        db.close()
        const recs: PendingRecord[] = req.result || []
        const files: File[] = []
        for (const r of recs.sort((a, b) => a.addedAt - b.addedAt)) {
          try {
            files.push(new File([r.blob], r.name, {
              type: r.type, lastModified: r.lastModified,
            }))
          } catch { /* skip */ }
        }
        resolve(files)
      }
      req.onerror = () => { db.close(); reject(req.error) }
    })
  } catch { return [] }
}

export async function clearPendingFiles(): Promise<void> {
  try {
    const db = await openDB()
    return await new Promise((resolve) => {
      const tx = db.transaction(STORE, "readwrite")
      tx.objectStore(STORE).clear()
      tx.oncomplete = () => { db.close(); resolve() }
      tx.onerror = () => { db.close(); resolve() }
    })
  } catch { /* ignore */ }
}
