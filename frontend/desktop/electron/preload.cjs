const { contextBridge, ipcRenderer } = require("electron")

// 从命令行参数读取启动器注入的后端地址
function readInjectedBackendUrl() {
  const args = process.argv || []
  for (const a of args) {
    if (typeof a === "string" && a.startsWith("--backend-url=")) {
      const v = a.slice("--backend-url=".length).trim()
      if (v) return v
    }
  }
  return null
}

const injectedBackendUrl = readInjectedBackendUrl()
if (injectedBackendUrl) {
  // 暴露到 window，供 renderer 优先读取
  contextBridge.exposeInMainWorld("__BACKEND_URL__", injectedBackendUrl)
}

contextBridge.exposeInMainWorld("desktopRuntime", {
  selectFolder: () => ipcRenderer.invoke("select-folder"),
  allowRoot: (r) => ipcRenderer.invoke("fs:allow-root", r),
  listDir: (d) => ipcRenderer.invoke("fs:list-dir", d),
  readFile: (p) => ipcRenderer.invoke("fs:read-file", p),
  writeFile: (p, c) => ipcRenderer.invoke("fs:write-file", p, c),
  persistGet: (k) => ipcRenderer.invoke("persist:get", k),
  persistSet: (k, v) => ipcRenderer.invoke("persist:set", k, v),
})
