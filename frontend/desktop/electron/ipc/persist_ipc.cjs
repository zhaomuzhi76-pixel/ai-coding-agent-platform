const { app, ipcMain } = require("electron")
const fs = require("node:fs/promises")
const path = require("node:path")

let cache = null
let filePath = ""

function resolvePath() {
  if (!filePath) {
    filePath = path.join(
      app.getPath("userData"),
      "workspace_persist.json",
    )
  }
  return filePath
}

async function load() {
  if (cache) return cache
  try {
    const raw = await fs.readFile(resolvePath(), "utf8")
    const parsed = JSON.parse(raw)
    cache = parsed && typeof parsed === "object" ? parsed : {}
  } catch (e) {
    cache = {}
  }
  return cache
}

async function save() {
  if (!cache) return
  const target = resolvePath()
  await fs.mkdir(path.dirname(target), { recursive: true })
  await fs.writeFile(
    target,
    JSON.stringify(cache, null, 2),
    "utf8",
  )
}

async function persistGet(key) {
  const data = await load()
  return data[key] !== undefined ? data[key] : null
}

async function persistSet(key, value) {
  const data = await load()
  data[key] = value
  await save()
  return true
}

function registerPersistIpc() {
  ipcMain.handle("persist:get", function (_e, k) { return persistGet(k) })
  ipcMain.handle("persist:set", function (_e, k, v) { return persistSet(k, v) })
}

module.exports = {
  persistGet: persistGet,
  persistSet: persistSet,
  registerPersistIpc: registerPersistIpc,
}
