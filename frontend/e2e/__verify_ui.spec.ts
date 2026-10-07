import { test } from "@playwright/test"
import * as fs from "node:fs"
import * as os from "node:os"
import * as path from "node:path"

const FIXTURE = fs.mkdtempSync(path.join(os.tmpdir(), "verify-ui-"))
for (let i = 0; i < 5; i++) {
  fs.writeFileSync(path.join(FIXTURE, `m${i}.py`), "")
}

test.setTimeout(60000)

test("UI 是否显示 query 结果", async ({ page }) => {
  const url = `/#/coding?workspace=${encodeURIComponent(FIXTURE)}`
  await page.goto(url, { waitUntil: "domcontentloaded" })
  await page.reload({ waitUntil: "domcontentloaded" })

  await page.waitForFunction(
    () => document.querySelector(".agent-composer__status")?.textContent?.trim() === "Ready",
    { timeout: 30000 },
  ).catch(() => undefined)

  const ta = page.locator("textarea[aria-label='Agent message']")
  await ta.fill("当前项目有多少个 py 文件")
  await page.keyboard.press("Control+Enter")

  await page.waitForTimeout(8000)

  const body = await page.locator("body").innerText()

  console.log("\n════ 关键判断 ════")
  console.log(`  含 "5 个 .py"        : ${body.includes("5 个 .py")}`)
  console.log(`  含 "无回答"          : ${body.includes("(无回答)")}`)
  console.log(`  含 "timeline-final"  : ${await page.locator(".timeline-final").count()}`)
  console.log(`  含 "answer-markdown" : ${await page.locator(".answer-markdown").count()}`)

  console.log("\n════ body 尾部 500 字符 ════")
  console.log(body.slice(-500))

  await page.screenshot({ path: "e2e/screenshots/__verify_ui.png" })
  console.log("\n[截图] e2e/screenshots/__verify_ui.png")
})
