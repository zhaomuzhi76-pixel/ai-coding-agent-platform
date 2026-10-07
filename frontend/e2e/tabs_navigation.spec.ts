import { test, expect, type Page } from "@playwright/test"
import { resetLocalStorageOnce } from "./support/reset"

async function mockPlatformApi(page: Page) {
  await page.route("**/api/platform/models", (route) =>
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        ok: true, data: { models: [
          { model: "qwen-max", provider: "dashscope",
            display_name: "通义千问-Max", context_window: 32000,
            supports_tool_call: true, supports_stream: true,
            supports_embedding: false,
            cost_input_per_1k: 0.02, cost_output_per_1k: 0.06,
            strengths: ["reasoning"] },
        ] },
      }),
    }),
  )
  await page.route("**/api/platform/domains", (route) =>
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        ok: true, data: { domains: [
          { name: "agriculture", entity_types: ["crop"], terms: 2 },
        ] },
      }),
    }),
  )
  await page.route("**/api/observability/**", (route) => {
    const url = route.request().url()
    if (url.includes("/summary")) {
      return route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({
          ok: true, data: {
            overall: { count: 0, p50: 0, p95: 0, p99: 0, max: 0 },
            spans: 0, errors: 0, alerts: 0,
          },
        }),
      })
    }
    if (url.includes("/spans")) {
      return route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({ ok: true, data: { total: 0, spans: [] } }),
      })
    }
    return route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ ok: true, data: { events: [] } }),
    })
  })
  await page.route("**/api/security/**", (route) =>
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        ok: true, data: route.request().url().includes("summary")
          ? { roles: 2, permissions: 16, tenants: 0,
              audit_entries: 0, denials: 0 }
          : { roles: [], count: 0 },
      }),
    }),
  )
  await page.route("**/api/mcp/**", (route) =>
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        ok: true, data: route.request().url().includes("summary")
          ? { local_tools: 3, remote_servers: 0, domains: 2 }
          : { tools: [], servers: [], domains: [], count: 0 },
      }),
    }),
  )
  await page.route("**/api/finetune/**", (route) =>
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        ok: true, data: route.request().url().includes("summary")
          ? { recipes: 4, runs: 0, statuses: {} }
          : { recipes: [], runs: [], count: 0 },
      }),
    }),
  )
}

test.describe("Tab navigation", () => {
  test.beforeEach(async ({ page }) => {
    await resetLocalStorageOnce(page)
    await mockPlatformApi(page)
  })

  test("7 tabs render correctly", async ({ page }) => {
    await page.goto("/#/platform")
    const nav = page.locator(".global-nav")
    await expect(nav).toBeVisible({ timeout: 8000 })

    const labels = ["编码", "平台", "模型", "微调", "工具", "安全", "监控"]
    for (const label of labels) {
      await expect(
        nav.getByRole("button", { name: label, exact: true }),
      ).toBeVisible()
    }
    console.log(`  [tabs] all 7 tabs present`)
  })

  test("platform tab shows workbench", async ({ page }) => {
    await page.goto("/#/platform")
    await expect(page.locator(".platform-workbench")).toBeVisible({
      timeout: 8000,
    })
    console.log(`  [platform] workbench rendered`)
  })

  test("models tab shows catalog", async ({ page }) => {
    await page.goto("/#/models")
    await expect(page.locator(".models-view")).toBeVisible({
      timeout: 8000,
    })
    console.log(`  [models] catalog rendered`)
  })

  test("monitor tab shows KPI", async ({ page }) => {
    await page.goto("/#/monitor")
    await expect(page.locator(".ind-kpi-row")).toBeVisible({
      timeout: 8000,
    })
    console.log(`  [monitor] KPI rendered`)
  })

  test("security tab shows page", async ({ page }) => {
    await page.goto("/#/security")
    await expect(page.locator(".ind-page__title")).toBeVisible({
      timeout: 8000,
    })
    console.log(`  [security] rendered`)
  })

  test("mcp tab shows market", async ({ page }) => {
    await page.goto("/#/mcp")
    await expect(page.locator(".ind-page__title")).toBeVisible({
      timeout: 8000,
    })
    console.log(`  [mcp] rendered`)
  })

  test("finetune tab shows recipes", async ({ page }) => {
    await page.goto("/#/finetune")
    await expect(page.locator(".ind-page__title")).toBeVisible({
      timeout: 8000,
    })
    console.log(`  [finetune] rendered`)
  })
})
