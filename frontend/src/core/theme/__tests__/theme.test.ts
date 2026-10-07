import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest"

import {
  getTheme,
  initTheme,
  setTheme,
  subscribeTheme,
  toggleTheme,
} from "../theme"

beforeEach(() => {
  window.localStorage.clear()
})

describe("theme", () => {
  it("initializes as dark when system prefers dark", () => {
    vi.stubGlobal("matchMedia", (q: string) => ({
      matches: false,
      media: q,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
    const t = initTheme()
    expect(t).toBe("dark")
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark")
  })

  it("initializes as light when system prefers light", () => {
    vi.stubGlobal("matchMedia", (q: string) => ({
      matches: q.includes("light"),
      media: q,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
    const t = initTheme()
    expect(t).toBe("light")
  })

  it("prefers stored value over system preference", () => {
    window.localStorage.setItem("biancheng.theme", "light")
    vi.stubGlobal("matchMedia", () => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
    const t = initTheme()
    expect(t).toBe("light")
  })

  it("setTheme persists to localStorage", () => {
    setTheme("light")
    expect(window.localStorage.getItem("biancheng.theme")).toBe("light")
    expect(getTheme()).toBe("light")
  })

  it("toggleTheme alternates dark/light", () => {
    setTheme("dark")
    expect(toggleTheme()).toBe("light")
    expect(toggleTheme()).toBe("dark")
  })

  it("notifies subscribers on change", () => {
    const listener = vi.fn()
    const unsubscribe = subscribeTheme(listener)
    setTheme("light")
    expect(listener).toHaveBeenCalledTimes(1)
    setTheme("dark")
    expect(listener).toHaveBeenCalledTimes(2)
    unsubscribe()
    setTheme("light")
    expect(listener).toHaveBeenCalledTimes(2)
  })
})
