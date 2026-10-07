import { useEffect, useRef, useState } from "react"
import { Terminal } from "@xterm/xterm"
import { FitAddon } from "@xterm/addon-fit"
import { WebLinksAddon } from "@xterm/addon-web-links"
import "@xterm/xterm/css/xterm.css"
import { openTerminalSocket, type TerminalSocketApi } from "./terminal_socket"
import { runtimeConfig } from "../config/runtime"

export function TerminalView() {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const termRef = useRef<Terminal | null>(null)
  const fitRef = useRef<FitAddon | null>(null)
  const sockRef = useRef<TerminalSocketApi | null>(null)
  const [status, setStatus] = useState<"connecting" | "ready" | "closed">("connecting")

  useEffect(() => {
    if (!hostRef.current) return
    const term = new Terminal({
      fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
      fontSize: 12,
      lineHeight: 1.4,
      cursorBlink: true,
      convertEol: true,
      theme: {
        background: "#0b111b",
        foreground: "#d9e2ec",
        cursor: "#7aa2f7",
        selectionBackground: "#26456e",
      },
    })
    const fit = new FitAddon()
    term.loadAddon(fit)
    term.loadAddon(new WebLinksAddon())
    term.open(hostRef.current)
    fit.fit()

    termRef.current = term
    fitRef.current = fit

    const sock = openTerminalSocket(runtimeConfig.apiBaseUrl, {
      onData: (d) => term.write(d),
      onClose: () => {
        setStatus("closed")
        term.write("\r\n\x1b[33m[session closed]\x1b[0m\r\n")
      },
      onError: () => setStatus("closed"),
    })
    sockRef.current = sock
    setStatus("ready")
    sock.resize(term.cols, term.rows)

    const dispose = term.onData((d) => sock.send(d))

    const ro = new ResizeObserver(() => {
      try {
        fit.fit()
        sock.resize(term.cols, term.rows)
      } catch {
        /* ignore */
      }
    })
    ro.observe(hostRef.current)

    return () => {
      ro.disconnect()
      dispose.dispose()
      sock.close()
      term.dispose()
    }
  }, [])

  return (
    <div className="terminal-view" data-status={status}>
      <div ref={hostRef} className="terminal-view__host" />
    </div>
  )
}
