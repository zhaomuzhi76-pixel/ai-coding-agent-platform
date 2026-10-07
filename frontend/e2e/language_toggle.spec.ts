import { test, expect } from "@playwright/test"
import { resetLocalStorageOnce } from "./support/reset"

test.describe("Language toggle", () => {
  test("toggles language and persists", async ({ page }) => {
    await resetLocalStorageOnce(page)
    await page.goto("/#/platform")
    await page.waitForSelector(".global-nav", { timeout: 8000 })

    const nav = page.locator(".global-nav")
    // 检测初始语言
    const platformZh = nav.getByRole("button", {
      name: "平台", exact: true,
    })
    const initialIsZh = (await platformZh.count()) > 0
    const initialLabel = initialIsZh ? "平台" : "Platform"
    const expectedLabel = initialIsZh ? "Platform" : "平台"
    console.log(`  [lang] initial=${initialLabel} expected=${expectedLabel}`)

    // 精确选择语言按钮
    await page.locator('[data-action="locale"]').click()

    await expect(
      nav.getByRole("button", { name: expectedLabel, exact: true }),
    ).toBeVisible()
    console.log(`  [lang] switched to ${expectedLabel}`)

    // reload 后保持
    await page.reload()
    await expect(
      nav.getByRole("button", { name: expectedLabel, exact: true }),
    ).toBeVisible()
    console.log(`  [lang] persisted across reload`)

    // 切回
    await page.locator('[data-action="locale"]').click()
    await expect(
      nav.getByRole("button", { name: initialLabel, exact: true }),
    ).toBeVisible()
    console.log(`  [lang] toggled back to ${initialLabel}`)
  })
})
