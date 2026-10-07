import {
  getDesktopRuntime,
} from "./desktop_runtime_access"

const LOCAL_PREFIX = "biancheng.desktop.persist."

function readLocal(key: string): unknown {
  try {
    const raw = window.localStorage.getItem(LOCAL_PREFIX + key)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function writeLocal(key: string, value: unknown): boolean {
  try {
    window.localStorage.setItem(
      LOCAL_PREFIX + key,
      JSON.stringify(value),
    )
    return true
  } catch {
    return false
  }
}

export async function persistGet(key: string): Promise<unknown> {
  const runtime = getDesktopRuntime()
  if (runtime) {
    return runtime.persistGet(key)
  }
  return readLocal(key)
}

export async function persistSet(
  key: string,
  value: unknown,
): Promise<boolean> {
  const runtime = getDesktopRuntime()
  if (runtime) {
    return runtime.persistSet(key, value)
  }
  return writeLocal(key, value)
}

export async function persistLogAppend(
  key: string,
  record: unknown,
): Promise<boolean> {
  const runtime = getDesktopRuntime()
  if (runtime) {
    return runtime.persistLogAppend(key, record)
  }

  const current = readLocal(key)
  const records = Array.isArray(current)
    ? current
    : []

  records.push(record)

  return writeLocal(key, records)
}

export async function persistLogRead(
  key: string,
): Promise<unknown> {
  const runtime = getDesktopRuntime()
  if (runtime) {
    return runtime.persistLogRead(key)
  }

  const current = readLocal(key)

  return Array.isArray(current)
    ? current
    : []
}
