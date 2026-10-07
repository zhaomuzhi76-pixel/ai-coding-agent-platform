import { test } from "@playwright/test"
test.setTimeout(20000)
test("白屏诊断", async ({ page }) => {
  const errors: string[] = []
  page.on("pageerror", (e) => errors.push(e.message.slice(0, 300)))
  page.on("console", (m) => {
    if (m.type() === "error") errors.push("[c] " + m.text().slice(0, 300))
  })
  await page.goto("/", { waitUntil: "domcontentloaded" })
  await page.waitForTimeout(3000)
  const rootLen = await page.locator("#root").innerHTML().then((s) => s.length).catch(() => -1)
  console.log(`#root length: ${rootLen}`)
  console.log("--- errors ---")
  errors.slice(0, 10).forEach((e) => console.log(e))
})
