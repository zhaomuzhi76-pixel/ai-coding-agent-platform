export type Theme = "dark" | "light"

const STORAGE_KEY = "biancheng.theme"

let current: Theme = "dark"
const listeners = new Set<() => void>()

function readStored(): Theme | null {
  try {
    const v = window.localStorage.getItem(STORAGE_KEY)
    if (v === "dark" || v === "light") return v
  } catch {
    // ignore
  }
  return null
}

function detectSystem(): Theme {
  try {
    if (window.matchMedia) {
      if (window.matchMedia("(prefers-color-scheme: light)").matches) {
        return "light"
      }
    }
  } catch {
    // ignore
  }
  return "dark"
}

function apply(theme: Theme): void {
  const root = document.documentElement
  root.setAttribute("data-theme", theme)
  if (theme === "light") {
    root.style.colorScheme = "light"
  } else {
    root.style.colorScheme = "dark"
  }
}

export function initTheme(): Theme {
  const stored = readStored()
  current = stored ?? detectSystem()
  apply(current)
  return current
}

export function getTheme(): Theme {
  return current
}

export function setTheme(theme: Theme): void {
  current = theme
  apply(theme)
  try {
    window.localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // ignore
  }
  listeners.forEach((l) => l())
}

export function toggleTheme(): Theme {
  setTheme(current === "dark" ? "light" : "dark")
  return current
}

export function subscribeTheme(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function snapshotTheme(): Theme {
  return current
}
