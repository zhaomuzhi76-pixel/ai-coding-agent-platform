import { test } from "@playwright/test"

test.setTimeout(60000)

const TABS = [
  ["finetune", "10-finetune-real"],
  ["mcp", "11-mcp-real"],
  ["security", "12-security-real"],
  ["monitor", "13-monitor-real"],
]

for (const [tab, name] of TABS) {
  test(`real data ${tab}`, async ({ page }) => {
    // 抓 API 请求和响应
    page.on("response", async (res) => {
      const url = res.url()
      if (url.includes("/api/") && !url.includes("/src/")) {
        let body = ""
        try {
          body = (await res.text()).slice(0, 120)
        } catch { /* */ }
        console.log(`  [${res.status()}] ${url.replace("http://127.0.0.1:4173", "")}  ${body}`)
      }
    })

    await page.goto(`/#/${tab}`)
    await page.waitForTimeout(2500)

    await page.screenshot({
      path: `e2e/screenshots/${name}.png`,
      fullPage: true,
    })
    console.log(`  [shot] ${name}.png`)
  })
}
