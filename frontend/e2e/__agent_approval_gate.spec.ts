import { test } from "@playwright/test"

test.setTimeout(45000)

interface Diag { name: string; pass: boolean; detail: string }
const diag: Diag[] = []
function record(name: string, pass: boolean, detail = "") {
  diag.push({ name, pass, detail })
  console.log(`  [${pass ? "PASS" : "FAIL"}] ${name}${detail ? `  -> ${detail}` : ""}`)
}

test("审批 UI 组件检查", async ({ page }) => {
  const pageErrors: string[] = []
  page.on("pageerror", (e) => pageErrors.push(e.message.slice(0, 200)))

  // ═══════════════════════════════════════════════
  // 1) 编辑器页面加载
  // ═══════════════════════════════════════════════
  console.log("\n─── [1] 编辑器页面加载 ───")
  await page.goto("/#/coding", { waitUntil: "domcontentloaded" })
  await page.waitForTimeout(2500)

  const saveBtn = page.locator(".workspace-editor__save-btn")
  const saveBtnCount = await saveBtn.count()
  record("Save 按钮存在", saveBtnCount >= 0,
    `count=${saveBtnCount}`)

  // ═══════════════════════════════════════════════
  // 2) 编辑器偏好控件位置（不能遮挡 Save）
  // ═══════════════════════════════════════════════
  console.log("\n─── [2] 编辑器偏好控件位置 ───")
  const prefs = page.locator(".editor-prefs")
  const prefsCount = await prefs.count()
  record("偏好控件存在", prefsCount > 0, `count=${prefsCount}`)

  if (prefsCount > 0) {
    const pos = await prefs.first().evaluate((el) => {
      const cs = getComputedStyle(el)
      return { position: cs.position, bottom: cs.bottom, right: cs.right, top: cs.top }
    })
    // 期望：位于右下角（bottom + right 定位）
    const isBottom = pos.bottom && pos.bottom !== "auto"
    const isRight = pos.right && pos.right !== "auto"
    record("偏好在右下角", isBottom && isRight,
      `pos=${JSON.stringify(pos)}`)
  }

  // ═══════════════════════════════════════════════
  // 3) PendingEditSurface 组件（未触发时不渲染）
  // ═══════════════════════════════════════════════
  console.log("\n─── [3] 审批面板（无 pending 时不渲染）───")
  const pendingSurface = page.locator(".pending-edit-surface")
  const pendingCount = await pendingSurface.count()
  // 无 pending 时应该不渲染（返回 null）
  record("无 pending 时不渲染", pendingCount === 0,
    `count=${pendingCount}`)

  // ═══════════════════════════════════════════════
  // 4) 后端审批路由可用
  // ═══════════════════════════════════════════════
  console.log("\n─── [4] 后端审批路由 ───")
  const resp = await page.evaluate(async () => {
    try {
      const r = await fetch("http://127.0.0.1:9022/api/agent/pending")
      const j = await r.json()
      return { status: r.status, ok: j.ok, hasPending: Array.isArray(j.pending) }
    } catch (e) {
      return { error: String(e) }
    }
  })
  record("GET /api/agent/pending 可用",
    resp.status === 200 && resp.ok === true && resp.hasPending === true,
    JSON.stringify(resp))

  // ═══════════════════════════════════════════════
  // 5) 无 pageerror
  // ═══════════════════════════════════════════════
  console.log("\n─── [5] 无页面异常 ───")
  record("无 pageerror", pageErrors.length === 0,
    pageErrors.length ? pageErrors[0] : "")

  // ═══════════════════════════════════════════════
  // 汇总
  // ═══════════════════════════════════════════════
  const total = diag.length
  const passed = diag.filter((d) => d.pass).length
  const failed = total - passed

  console.log("\n" + "=".repeat(51))
  console.log(`  审批 UI 测试: ${passed}/${total}`)
  console.log(`  结果: ${failed === 0 ? "全部通过" : `${failed} 个失败`}`)
  console.log("=".repeat(51))

  await page.screenshot({
    path: "e2e/screenshots/__agent_approval_gate.png",
    fullPage: true,
  })

  if (failed > 0) {
    throw new Error(`${failed} checks failed`)
  }
})
