const base = "http://127.0.0.1:4173"

async function httpGate() {
  const response = await fetch(`${base}/api/health`)

  console.log("FRONTEND_PROXY_HTTP_STATUS=", response.status)

  if (response.status !== 200) {
    throw new Error(
      `frontend preview /api/health returned ${response.status}`,
    )
  }

  const body = await response.text()

  console.log("FRONTEND_PROXY_HTTP_BYTES=", body.length)

  if (!body) {
    throw new Error("frontend preview health response is empty")
  }

  console.log("FRONTEND_PROXY_HTTP=PASS")
}

async function websocketGate() {
  const socket = new WebSocket(
    "ws://127.0.0.1:4173/ws/agent",
  )

  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      socket.close()
      reject(new Error("frontend preview websocket timeout"))
    }, 5000)

    socket.addEventListener("open", () => {
      clearTimeout(timer)
      console.log("FRONTEND_PROXY_WS=PASS")
      socket.close()
      resolve()
    })

    socket.addEventListener("error", () => {
      clearTimeout(timer)
      reject(new Error("frontend preview websocket failed"))
    })
  })
}

async function main() {
  console.log("===== FRONTEND -> BACKEND REAL PROXY GATE =====")
  await httpGate()
  await websocketGate()
  console.log("FRONTEND_BACKEND_PROXY_GATE=PASS")
}

main().catch(error => {
  console.error("FRONTEND_BACKEND_PROXY_GATE=FAIL")
  console.error(error)
  process.exitCode = 1
})
