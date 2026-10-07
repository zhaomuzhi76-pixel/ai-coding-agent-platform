const { app, BrowserWindow, Menu } = require("electron")
const path = require("node:path")
const fs = require("node:fs")

const fsIpc = require("./ipc/fs_ipc.cjs")
const persistIpc = require("./ipc/persist_ipc.cjs")

function buildMenu() {
  return Menu.buildFromTemplate([
    {
      label: "View",
      submenu: [
        { role: "reload", accelerator: "F5" },
        { role: "forceReload", accelerator: "Ctrl+Shift+R" },
        { role: "toggleDevTools", accelerator: "F12" },
        { type: "separator" },
        { role: "resetZoom" },
        { role: "zoomIn" },
        { role: "zoomOut" },
        { type: "separator" },
        { role: "togglefullscreen" },
      ],
    },
  ])
}
Menu.setApplicationMenu(buildMenu())

// 优先用 dev 模式（只要 4173 在跑 或 强制 env）
// 解决"改源码但 Electron 读旧 dist 白屏"的问题
const { net } = require("electron")
const hasVitePort = (() => {
  try {
    const req = net.request({ method: "HEAD", url: "http://localhost:4173/" })
    req.abort()
    return true
  } catch { return false }
})()
const isDev = !app.isPackaged
  || !!process.env.BIANCHENG_DEV_URL
  || !!process.env.VITE_DEV_URL
  || hasVitePort
const DEV_URL_OVERRIDE = process.env.BIANCHENG_DEV_URL
const DEV_URL = DEV_URL_OVERRIDE || process.env.VITE_DEV_URL || "http://localhost:4173"
const FORCE_DEV = !!DEV_URL_OVERRIDE

// 后端地址解析顺序（与 renderer 端一致，但这里只处理启动器注入的部分）
// 1. 命令行参数 --backend-url=xxx
// 2. 环境变量 BIANCHENG_BACKEND_URL
// 3. 打包同级目录的 config.json
function resolveInjectedBackendUrl() {
  // 1. CLI 参数
  const cliArg = process.argv.find(a => a.startsWith("--backend-url="))
  if (cliArg) {
    const v = cliArg.slice("--backend-url=".length).trim()
    if (v) return v
  }

  // 2. 环境变量
  if (process.env.BIANCHENG_BACKEND_URL) {
    const v = process.env.BIANCHENG_BACKEND_URL.trim()
    if (v) return v
  }

  // 3. 打包同级目录的 config.json（客户机房部署时放一个即可）
  try {
    const appDir = path.dirname(app.getPath("exe"))
    const cfgPath = path.join(appDir, "config.json")
    if (fs.existsSync(cfgPath)) {
      const raw = fs.readFileSync(cfgPath, "utf8")
      const cfg = JSON.parse(raw)
      if (cfg && typeof cfg.backendUrl === "string" && cfg.backendUrl.trim()) {
        return cfg.backendUrl.trim()
      }
    }
  } catch { /* ignore */ }

  return null
}

async function restoreAllowedRoots() {
  try {
    const saved = await persistIpc.persistGet("workspace.roots")
    if (Array.isArray(saved)) {
      for (const r of saved) {
        if (typeof r === "string") fsIpc.allowRoot(r)
      }
    }
  } catch { /* first boot */ }
}

// REMOTE_FIRST: 生产模式优先连后端 /app（前端热更新），失败回退本地 dist
async function loadRenderer(win) {
  const useDev = isDev || FORCE_DEV
  if (useDev) {
    try { await win.loadURL(DEV_URL) } catch (e) {
      if (!String(e).includes("ERR_ABORTED")) console.error("[load-error]", e)
    }
    win.webContents.openDevTools({ mode: "detach" })
    return
  }

  // 生产：尝试远程 /app（这样改前端只需更新后端 frontend/dist，无需重打包）
  const injected = resolveInjectedBackendUrl()
  const candidates = []
  if (injected) candidates.push(injected)
  // 用户可在 config.json 里额外配 frontendUrl
  candidates.push("http://127.0.0.1:9022")

  for (const base of candidates) {
    const url = base.replace(/\/+$/, "") + "/app/"
    try {
      const ok = await win.loadURL(url)
      console.log("[remote-first] loaded:", url)
      return
    } catch (e) {
      if (!String(e).includes("ERR_ABORTED")) {
        console.warn("[remote-first] failed:", url, e && e.message)
      }
    }
  }

  // 兜底：本地 dist
  const distIndex = path.join(__dirname, "..", "..", "dist", "index.html")
  if (!fs.existsSync(distIndex)) {
    console.error("[prod] dist/index.html missing:", distIndex)
  }
  console.log("[remote-first] fallback to local dist")
  await win.loadFile(distIndex)
}

async function createWindow() {
  const injectedUrl = resolveInjectedBackendUrl()
  if (injectedUrl) {
    console.log("[backend] injected via launcher:", injectedUrl)
  } else {
    console.log("[backend] no launcher override, renderer will use fallback chain")
  }

  const win = new BrowserWindow({
    width: 1600, height: 1000,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true, nodeIntegration: false, sandbox: false,
      devTools: true,
      additionalArguments: injectedUrl
        ? ["--backend-url=" + injectedUrl]
        : [],
    },
  })

  // 只处理 F12 / Ctrl+Shift+I —— 不做 preventDefault 影响 IME 之外的其他键
  win.webContents.on("before-input-event", (event, input) => {
    const key = (input.key || "").toLowerCase()
    const isF12 = input.key === "F12"
    const isCtrlShiftI =
      (input.control || input.meta) && input.shift && key === "i"
    if (!isF12 && !isCtrlShiftI) return
    event.preventDefault()
    if (win.webContents.isDevToolsOpened()) {
      win.webContents.closeDevTools()
    } else {
      win.webContents.openDevTools({ mode: "detach" })
    }
  })

  win.webContents.on("preload-error", (_e, p, err) =>
    console.error("[preload-error]", p, err))
  win.webContents.on("console-message", (ev) => {
    if (ev.level === "error" || ev.level === 3) console.log("[renderer]", ev.message)
  })
  // 不拦截键盘快捷键：交给 Menu role 处理，避免干扰 IME 中文输入
  win.setMenuBarVisibility(false)
  await loadRenderer(win)
}

app.whenReady().then(async () => {
  fsIpc.registerFsIpc()
  persistIpc.registerPersistIpc()
  await restoreAllowedRoots()
  await createWindow()
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) void createWindow()
  })
})

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit()
})
