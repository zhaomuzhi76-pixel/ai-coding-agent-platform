import { useCallback, useEffect, useState } from "react"

const STORAGE_KEY = "biancheng.editor.preferences"
const DEFAULT_FONT_SIZE = 13
const MIN_FONT_SIZE = 10
const MAX_FONT_SIZE = 28
const DEFAULT_FOREGROUND = "#d9e2ec"

export interface EditorPreferences {
  fontSize: number
  foreground: string
}

function clamp(v: number, lo: number, hi: number): number {
  return v < lo ? lo : v > hi ? hi : v
}

function readStored(): EditorPreferences {
  const fallback: EditorPreferences = {
    fontSize: DEFAULT_FONT_SIZE,
    foreground: DEFAULT_FOREGROUND,
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return fallback
    const parsed = JSON.parse(raw) as Partial<EditorPreferences>
    const fs =
      typeof parsed.fontSize === "number"
        ? clamp(parsed.fontSize, MIN_FONT_SIZE, MAX_FONT_SIZE)
        : DEFAULT_FONT_SIZE
    const fg =
      typeof parsed.foreground === "string" && parsed.foreground.trim()
        ? parsed.foreground
        : DEFAULT_FOREGROUND
    return { fontSize: fs, foreground: fg }
  } catch {
    return fallback
  }
}

function applyToDocument(prefs: EditorPreferences): void {
  const root = document.documentElement
  // 真正生效的变量（editor_surface.css 使用）
  root.style.setProperty("--editor-font-size", `${prefs.fontSize}px`)
  root.style.setProperty("--editor-fg", prefs.foreground)
  // 兼容别名，以防有组件引用 codex-*
  root.style.setProperty("--codex-font-size", `${prefs.fontSize}px`)
  root.style.setProperty("--codex-fg", prefs.foreground)
}

export interface EditorPreferencesApi {
  preferences: EditorPreferences
  setFontSize: (px: number) => void
  setForeground: (color: string) => void
  increaseFontSize: () => void
  decreaseFontSize: () => void
  reset: () => void
}

export function useEditorPreferences(): EditorPreferencesApi {
  const [preferences, setPreferences] = useState<EditorPreferences>(readStored)

  useEffect(() => {
    applyToDocument(preferences)
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences))
    } catch {
      /* localStorage 不可用则静默 */
    }
  }, [preferences])

  const setFontSize = useCallback((px: number) => {
    setPreferences((p) => ({
      ...p,
      fontSize: clamp(px, MIN_FONT_SIZE, MAX_FONT_SIZE),
    }))
  }, [])
  const setForeground = useCallback((color: string) => {
    setPreferences((p) => ({ ...p, foreground: color }))
  }, [])
  const increaseFontSize = useCallback(() => {
    setPreferences((p) => ({
      ...p,
      fontSize: clamp(p.fontSize + 1, MIN_FONT_SIZE, MAX_FONT_SIZE),
    }))
  }, [])
  const decreaseFontSize = useCallback(() => {
    setPreferences((p) => ({
      ...p,
      fontSize: clamp(p.fontSize - 1, MIN_FONT_SIZE, MAX_FONT_SIZE),
    }))
  }, [])
  const reset = useCallback(() => {
    setPreferences({
      fontSize: DEFAULT_FONT_SIZE,
      foreground: DEFAULT_FOREGROUND,
    })
  }, [])

  return {
    preferences,
    setFontSize,
    setForeground,
    increaseFontSize,
    decreaseFontSize,
    reset,
  }
}
