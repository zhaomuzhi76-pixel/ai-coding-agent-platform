import { get, put } from "./indexed_db"

interface ConfigRecord<T> {
  key: string
  value: T
}

export async function getConfig<T>(key: string): Promise<T | null> {
  const r = await get<ConfigRecord<T>>("app_config", key)
  return r ? r.value : null
}

export async function setConfig<T>(key: string, value: T): Promise<void> {
  await put("app_config", { key, value } as ConfigRecord<T>)
}

export const CONFIG_KEYS = {
  backendUrl: "backend.url",
  lastRoot: "workspace.lastRoot",
} as const
