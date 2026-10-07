import { test } from "@playwright/test"

test.setTimeout(60000)

test("monitor 真数据", async ({ page }) => {
  await page.goto("/#/monitor")
  await page.waitForTimeout(3000)

  // 检查 LLM 面板是否有数据
  const body = await page.locator("body").innerText()
  const hasCost = /\$0\.0\d+/.test(body)
  const hasSpan = /\b\d+\s*次/.test(body)

  console.log(`  [KPI 内容]`)
  const kpis = await page.locator(".ind-kpi__value").allTextContents()
  console.log(`    ${kpis.join(" | ")}`)

  console.log(`  [有成本数字] ${hasCost}`)
  console.log(`  [有调用次数] ${hasSpan}`)

  await page.screenshot({
    path: "e2e/screenshots/20-monitor-real-data.png",
    fullPage: true,
  })
  console.log("  [shot] 20-monitor-real-data.png")
})
