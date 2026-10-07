import { test, expect } from "@playwright/test"
import { resetLocalStorageOnce } from "./support/reset"

test.describe("Theme toggle", () => {
  test("toggles theme and persists", async ({ page }) => {
    await resetLocalStorageOnce(page)
    await page.goto("/#/platform")
    await page.waitForSelector(".global-nav", { timeout: 8000 })

    const html = page.locator("html")
    await expect(html).toHaveAttribute("data-theme", /dark|light/)
    const initial = await html.getAttribute("data-theme")
    const expected = initial === "dark" ? "light" : "dark"
    console.log(`  [theme] initial=${initial} expected=${expected}`)

    // 精确选择主题按钮
    await page.locator('[data-action="theme"]').click()

    await expect(html).toHaveAttribute("data-theme", expected)
    console.log(`  [theme] toggled to ${expected}`)

    // reload 后保持
    await page.reload()
    await expect(html).toHaveAttribute("data-theme", expected)
    console.log(`  [theme] persisted across reload`)

    // 切回
    await page.locator('[data-action="theme"]').click()
    await expect(html).toHaveAttribute("data-theme", initial)
    console.log(`  [theme] toggled back to ${initial}`)
  })
})
