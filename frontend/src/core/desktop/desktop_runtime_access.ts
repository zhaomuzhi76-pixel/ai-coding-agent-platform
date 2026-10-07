import type { DesktopRuntime } from "./desktop_runtime_contract"

export function getDesktopRuntime(): DesktopRuntime | null {
  if (typeof window === "undefined") return null
  return window.desktopRuntime ?? null
}

export function requireDesktopRuntime(): DesktopRuntime {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    throw new Error(
      "desktop runtime unavailable: run inside Electron shell",
    )
  }
  return runtime
}

export function hasDesktopRuntime(): boolean {
  return getDesktopRuntime() !== null
}
