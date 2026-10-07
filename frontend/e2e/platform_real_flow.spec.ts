import { test, expect } from "@playwright/test"
import * as fs from "fs"
import * as os from "os"
import * as path from "path"

test.setTimeout(180000)

test("platform real flow", async ({ page }) => {
  const ws = fs.mkdtempSync(path.join(os.tmpdir(), "e2e_"))
  fs.writeFileSync(
    path.join(ws, "calc.py"),
    'def add(a, b):\n    return a - b\n',
  )
  console.log(`  [ws] ${ws}`)

  // 抓所有 API 请求
  page.on("request", (req) => {
    if (req.url().includes("/api/")) {
      console.log(`  [req] ${req.method()} ${req.url()}`)
    }
  })
  page.on("response", async (res) => {
    if (res.url().includes("/api/platform/")) {
      let body = ""
      try { body = (await res.text()).slice(0, 200) } catch {}
      console.log(`  [res] ${res.status()} ${res.url()} ${body}`)
    }
  })

  await page.goto("/#/platform")
  await page.waitForTimeout(2000)

  // 1. workspace
  const wsInput = page.locator("input[placeholder='/path/to/project']")
  await expect(wsInput).toBeVisible({ timeout: 10000 })
  await wsInput.fill(ws)
  await wsInput.press("Enter")
  console.log("  [1] workspace set")

  // 2. 选模型：优先 3.8 或 dashscope-maas
  const modelSelect = page.locator("select").first()
  const options = await modelSelect.locator("option").allTextContents()
  console.log(`  [2] options: ${options.join(" | ")}`)
  const target = options.find((o) => o.includes("3.8") || o.includes("maas"))
  if (!target) throw new Error("no qwen3.8 option found")
  await modelSelect.selectOption({ label: target })
  console.log(`  [2] selected: ${target}`)

  // 3. 会话
  await page.getByRole("button", { name: "新建会话" }).click()
  await page.waitForFunction(
    () => {
      const bar = document.querySelector(".session-bar")
      return bar && bar.textContent && bar.textContent.includes("会话")
    },
    { timeout: 20000 },
  )
  console.log("  [3] session created")

  // 4. 提案
  const textarea = page.locator("textarea").first()
  await textarea.fill("修复 add 函数的 bug：让 add(1, 2) 等于 3")
  const filesInput = page.locator("input[placeholder*='目标文件']")
  await filesInput.fill("calc.py")
  console.log("  [4] 点击生成提案...")
  await page.getByRole("button", { name: "生成提案" }).click()

  // 5. 等提案出现（最长 120s）
  const cards = page.locator(".proposal-card")
  await expect(cards.first()).toBeVisible({ timeout: 120000 })
  console.log("  [5] proposal visible")

  // 6. 批准
  await page.getByRole("button", { name: "批准" }).click()
  await page.waitForTimeout(1500)
  console.log("  [6] approved")

  // 7. 应用
  await page.getByRole("button", { name: "应用" }).click()
  await page.waitForTimeout(3000)
  console.log("  [7] applied")

  // 8. 验证文件
  const content = fs.readFileSync(path.join(ws, "calc.py"), "utf-8")
  console.log("  [8] 文件内容：")
  for (const line of content.split("\n")) {
    console.log(`      ${line}`)
  }
  expect(content).toContain("return a + b")
  console.log("  ✓ PASS")
})
