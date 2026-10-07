const DB_NAME = "biancheng_ai_agent"
const DB_VERSION = 1

let dbPromise: Promise<IDBDatabase> | null = null

function openDb(): Promise<IDBDatabase> {
  if (dbPromise) return dbPromise

  dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)

    req.onupgradeneeded = () => {
      const db = req.result

      if (!db.objectStoreNames.contains("workspaces")) {
        const s = db.createObjectStore("workspaces", { keyPath: "rootPath" })
        s.createIndex("lastOpenedAt", "lastOpenedAt")
      }
      if (!db.objectStoreNames.contains("file_nodes")) {
        const s = db.createObjectStore("file_nodes", { keyPath: "id" })
        s.createIndex("by_workspace_path", ["workspaceId", "path"], { unique: true })
        s.createIndex("by_workspace_parent", ["workspaceId", "parentPath"])
        s.createIndex("by_workspace_expanded", ["workspaceId", "isExpanded"])
      }
      if (!db.objectStoreNames.contains("agent_events")) {
        const s = db.createObjectStore("agent_events", { keyPath: "id", autoIncrement: true })
        s.createIndex("by_session_ts", ["sessionId", "ts"])
      }
      if (!db.objectStoreNames.contains("agent_patches")) {
        const s = db.createObjectStore("agent_patches", { keyPath: "id", autoIncrement: true })
        s.createIndex("by_session_created", ["sessionId", "createdAt"])
      }
      if (!db.objectStoreNames.contains("app_config")) {
        db.createObjectStore("app_config", { keyPath: "key" })
      }
    }

    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })

  return dbPromise
}

export function tx<T>(
  storeName: string,
  mode: IDBTransactionMode,
  fn: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  return openDb().then(
    db =>
      new Promise<T>((resolve, reject) => {
        const t = db.transaction(storeName, mode)
        const store = t.objectStore(storeName)
        const req = fn(store)
        req.onsuccess = () => resolve(req.result)
        req.onerror = () => reject(req.error)
      }),
  )
}

export async function get<T>(store: string, key: IDBValidKey): Promise<T | null> {
  const r = await tx<T | undefined>(store, "readonly", s => s.get(key) as IDBRequest<T | undefined>)
  return r ?? null
}

export async function put<T>(store: string, value: T): Promise<void> {
  await tx(store, "readwrite", s => s.put(value) as IDBRequest<IDBValidKey>)
}

export async function del(store: string, key: IDBValidKey): Promise<void> {
  await tx(store, "readwrite", s => s.delete(key) as IDBRequest<undefined>)
}

export async function bulkPut<T>(store: string, values: T[]): Promise<void> {
  if (values.length === 0) return
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const t = db.transaction(store, "readwrite")
    const s = t.objectStore(store)
    for (const v of values) s.put(v as unknown as Record<string, unknown>)
    t.oncomplete = () => resolve()
    t.onerror = () => reject(t.error)
  })
}

export async function bulkDelete(store: string, keys: IDBValidKey[]): Promise<void> {
  if (keys.length === 0) return
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const t = db.transaction(store, "readwrite")
    const s = t.objectStore(store)
    for (const k of keys) s.delete(k)
    t.oncomplete = () => resolve()
    t.onerror = () => reject(t.error)
  })
}

export interface IdxQuery {
  index: string
  key: IDBValidKey | IDBKeyRange
}

export async function queryIndex<T>(store: string, q: IdxQuery): Promise<T[]> {
  return new Promise((resolve, reject) => {
    void openDb().then(db => {
      const t = db.transaction(store, "readonly")
      const s = t.objectStore(store)
      const idx = s.index(q.index)
      const req = idx.getAll(q.key)
      req.onsuccess = () => resolve(req.result as T[])
      req.onerror = () => reject(req.error)
    })
  })
}

export async function queryAll<T>(store: string): Promise<T[]> {
  return tx<T[]>(store, "readonly", s => s.getAll() as IDBRequest<T[]>)
}
