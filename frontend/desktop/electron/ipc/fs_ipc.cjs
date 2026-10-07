const { dialog, ipcMain } = require("electron")
const fs = require("node:fs/promises")
const path = require("node:path")

const allowedRoots = new Set()

function assertAllowed(target) {
  const resolved = path.resolve(target)
  for (const root of allowedRoots) {
    if (resolved === root || resolved.startsWith(root + path.sep)) {
      return resolved
    }
  }
  throw new Error("path outside allowed workspace: " + resolved)
}

function allowRoot(root) {
  if (typeof root !== "string" || !root.trim()) return
  allowedRoots.add(path.resolve(root))
}

async function selectFolder() {
  const result = await dialog.showOpenDialog({
    properties: ["openDirectory"],
  })
  if (result.canceled || result.filePaths.length === 0) {
    return null
  }
  const folder = path.resolve(result.filePaths[0])
  allowedRoots.add(folder)
  return { name: path.basename(folder), path: folder }
}

async function listDir(dir) {
  const safe = assertAllowed(dir)
  const entries = await fs.readdir(safe, { withFileTypes: true })
  const out = []
  for (const entry of entries) {
    if (entry.name === "node_modules") continue
    if (entry.name === ".git") continue
    const full = path.join(safe, entry.name)
    let size = 0
    try {
      const st = await fs.stat(full)
      size = st.size
    } catch (e) {
      size = 0
    }
    out.push({
      name: entry.name,
      path: full,
      kind: entry.isDirectory() ? "directory" : "file",
      size: size,
    })
  }
  out.sort(function (a, b) {
    if (a.kind !== b.kind) return a.kind === "directory" ? -1 : 1
    return a.name.localeCompare(b.name)
  })
  return out
}

async function readFile(target) {
  const safe = assertAllowed(target)
  const st = await fs.stat(safe)
  if (st.size > 2 * 1024 * 1024) {
    throw new Error("file too large (>2MB)")
  }
  const content = await fs.readFile(safe, "utf8")
  return { path: safe, content: content, size: st.size }
}

async function writeFile(target, content) {
  const safe = assertAllowed(target)
  await fs.writeFile(safe, content, "utf8")
  return { path: safe, size: Buffer.byteLength(content, "utf8") }
}

function registerFsIpc() {
  ipcMain.handle("select-folder", function () { return selectFolder() })
  ipcMain.handle("fs:list-dir", function (_e, dir) { return listDir(dir) })
  ipcMain.handle("fs:read-file", function (_e, p) { return readFile(p) })
  ipcMain.handle("fs:write-file", function (_e, p, c) { return writeFile(p, c) })
  ipcMain.handle("fs:allow-root", function (_e, r) {
    allowRoot(r)
    return true
  })
}

module.exports = {
  allowRoot: allowRoot,
  listDir: listDir,
  readFile: readFile,
  selectFolder: selectFolder,
  writeFile: writeFile,
  registerFsIpc: registerFsIpc,
}
