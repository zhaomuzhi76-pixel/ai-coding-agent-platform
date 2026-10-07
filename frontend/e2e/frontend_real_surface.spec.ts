import { test, expect } from "@playwright/test"

const BASE_URL = "http://127.0.0.1:4173"
type Page = import("@playwright/test").Page

async function openActions(page: Page) {
  await page.locator(
    ".industrial-sidebar .industrial-nav button",
  ).first().click()
  await expect(page.getByRole("button", {
    name: "打开文件夹",
    exact: true,
  })).toBeVisible()
}

async function installDirectory(page: Page) {
  await page.addInitScript(() => {
    let saved = "print('hello')\n"
    const file = (name: string) => ({
      kind: "file",
      name,
      async getFile() {
        return new File([saved], name)
      },
      async createWritable() {
        return {
          async write(value: unknown) {
            saved = String(value)
            document.documentElement.dataset.saved = saved
          },
          async close() {},
        }
      },
    })
    const directory = {
      kind: "directory",
      name: "demo-project",
      async *values() {
        yield {
          kind: "directory",
          name: "src",
          async *values() {
            yield file("main.py")
          },
        }
        yield file("README.md")
      },
    }
    Object.defineProperty(window, "showDirectoryPicker", {
      configurable: true,
      value: async () => directory,
    })
  })
}

async function installFilePicker(page: Page) {
  await page.addInitScript(() => {
    let saved = "print('standalone')\n"
    const file = {
      kind: "file",
      name: "standalone.py",
      async getFile() {
        return new File([saved], "standalone.py")
      },
      async createWritable() {
        return {
          async write(value: unknown) {
            saved = String(value)
          },
          async close() {},
        }
      },
    }
    Object.defineProperty(window, "showOpenFilePicker", {
      configurable: true,
      value: async () => [file],
    })
  })
}

async function openMainFile(page: Page) {
  await page.getByRole("button", {
    name: "demo-project",
    exact: true,
  }).click()
  await page.getByRole("button", {
    name: "src",
    exact: true,
  }).click()
  await expect(page.getByRole("button", {
    name: "main.py",
    exact: true,
  })).toBeVisible()
  await page.getByRole("button", {
    name: "main.py",
    exact: true,
  }).click()

  await expect(
    page.getByTestId(
      "workspace-editor",
    ),
  ).toContainText(
    "main.py",
  )

  await expect.poll(() =>
    page.evaluate(() =>
      JSON.parse(
        localStorage.getItem(
          "biancheng.ai.workspace.current",
        ) ?? "null",
      )?.activeFile ?? null,
    ),
  ).toBe(
    "demo-project/src/main.py",
  )
}

test("frontend real browser surface", async ({ page }) => {
  await page.goto(BASE_URL)
  await expect(page.locator("#root")).toBeVisible()
})

test("frontend asset loading", async ({ page }) => {
  const failures: string[] = []
  page.on("requestfailed", request => failures.push(request.url()))
  await page.goto(BASE_URL)
  expect(failures).toEqual([])
})

test("folder opens real content and saves", async ({ page }) => {
  await installDirectory(page)
  await page.goto(BASE_URL)
  await openActions(page)
  await page.getByRole("button", {
    name: "打开文件夹",
    exact: true,
  }).click()
  await openMainFile(page)

  const editor = page.getByTestId("workspace-editor")
  const editorContent =
    page.getByTestId("workspace-editor-content")
  await expect(
    editor,
  ).toContainText("demo-project/src/main.py")
  await expect(
    editorContent,
  ).toHaveText("print('hello')")

  await editorContent.fill("print('saved')")
  await page.getByRole("button", {
    name: "Save",
    exact: true,
  }).click()
  await expect.poll(() =>
    page.evaluate(
      () => document.documentElement.dataset.saved,
    ),
  ).toBe("print('saved')\n")

  await page.reload()

  await expect(
    page.getByRole("button", {
      name: "demo-project",
      exact: true,
    }),
  ).toBeVisible()

  await expect(
    page.getByRole("button", {
      name: "src",
      exact: true,
    }),
  ).toBeVisible()

  await expect(
    page.getByRole("button", {
      name: "main.py",
      exact: true,
    }),
  ).toBeVisible()

  await expect(
    page.getByTestId(
      "workspace-editor",
    ),
  ).toContainText(
    "demo-project/src/main.py",
  )
})

test("workspace persists left state across reload", async ({ page }) => {
  await installDirectory(page)
  await page.goto(BASE_URL)
  await openActions(page)
  await page.getByRole("button", {
    name: "打开文件夹",
    exact: true,
  }).click()
  await openMainFile(page)

  await expect(
    page.getByRole("button", {
      name: "main.py",
      exact: true,
    }),
  ).toBeVisible()

  await page.reload()

  await expect(
    page.getByRole("button", {
      name: "demo-project",
      exact: true,
    }),
  ).toBeVisible()

  await expect(
    page.getByRole("button", {
      name: "src",
      exact: true,
    }),
  ).toBeVisible()

  await expect(
    page.getByRole("button", {
      name: "main.py",
      exact: true,
    }),
  ).toBeVisible()

  await expect(
    page.getByTestId(
      "workspace-editor",
    ),
  ).toContainText(
    "main.py",
  )
})

test("repeated folder selection stays unique", async ({ page }) => {
  await installDirectory(page)
  await page.goto(BASE_URL)

  await openActions(page)
  await page.getByRole("button", {
    name: "打开文件夹",
    exact: true,
  }).click()
  await openMainFile(page)
  await expect(page.getByRole("button", {
    name: "main.py",
    exact: true,
  })).toHaveCount(1)

  await openActions(page)
  await page.getByRole("button", {
    name: "打开文件夹",
    exact: true,
  }).click()
  await openMainFile(page)
  await expect(page.getByRole("button", {
    name: "main.py",
    exact: true,
  })).toHaveCount(1)
})

test("standalone file uses the same editor", async ({ page }) => {
  await installFilePicker(page)
  await page.goto(BASE_URL)
  await openActions(page)

  await page.getByRole("button", {
    name: "打开文件",
    exact: true,
  }).click()
  await expect(page.getByRole("button", {
    name: "standalone.py",
    exact: true,
  })).toBeVisible()
  await page.getByRole("button", {
    name: "standalone.py",
    exact: true,
  }).click()

  const editor = page.getByTestId("workspace-editor")
  await expect(editor).toContainText("standalone.py")
  await expect(
    page.getByTestId(
      "workspace-editor-content",
    ),
  ).toHaveText("print('standalone')")
})

test("cancelled folder selection leaves workspace clean", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "showDirectoryPicker", {
      configurable: true,
      value: async () => {
        throw new DOMException("cancelled", "AbortError")
      },
    })
  })
  await page.goto(BASE_URL)
  await openActions(page)
  await page.getByRole("button", {
    name: "打开文件夹",
    exact: true,
  }).click()
  await expect(page.getByTestId(
    "workspace-file-tree-empty",
  )).toBeVisible()
  await expect(page.getByRole("alert")).not.toBeVisible()
})
