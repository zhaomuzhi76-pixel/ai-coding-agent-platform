import { getConfig, setConfig, CONFIG_KEYS } from "../storage/app_config_repository"

export interface BackendStatus {
  reachable: boolean
  url: string
  source: BackendUrlSource
  latencyMs: number
  error: string | null
  version: string | null
}

export type BackendUrlSource =
  | "runtime-override"   // Electron 启动时注入（企业部署最优先）
  | "user-config"        // 用户手动设置（持久化到 IndexedDB）
  | "build-default"      // 构建时 VITE_DEFAULT_BACKEND_URL
  | "env-default"        // 运行时 window.__BACKEND_URL__
  | "hardcoded"          // 兜底：本地开发默认

const HARDCODED_FALLBACK = "http://127.0.0.1:9022"

function normalize(url: string): string {
  return url.replace(/\/+$/, "")
}

function readBuildDefault(): string | null {
  // vite 会在构建时静态替换 import.meta.env.VITE_*
  const v = import.meta.env.VITE_DEFAULT_BACKEND_URL as string | undefined
  return v && v.trim() ? normalize(v.trim()) : null
}

function readRuntimeOverride(): string | null {
  if (typeof window === "undefined") return null
  const v = (window as unknown as { __BACKEND_URL__?: string }).__BACKEND_URL__
  return v && typeof v === "string" && v.trim() ? normalize(v.trim()) : null
}

export interface ResolvedBackendUrl {
  url: string
  source: BackendUrlSource
}

export async function resolveBackendUrl(): Promise<ResolvedBackendUrl> {
  // 1. 运行时注入（企业启动器/env 变量 → preload 注入）
  const runtime = readRuntimeOverride()
  if (runtime) return { url: runtime, source: "runtime-override" }

  // 2. 用户配置（第一次手动设置后持久化，之后无感）
  const userSet = await getConfig<string>(CONFIG_KEYS.backendUrl)
  if (userSet && userSet.trim()) {
    return { url: normalize(userSet.trim()), source: "user-config" }
  }

  // 3. 构建时注入的默认值（打包时 npm run build 带 VITE_DEFAULT_BACKEND_URL）
  const buildDefault = readBuildDefault()
  if (buildDefault) return { url: buildDefault, source: "build-default" }

  // 4. 兜底
  return { url: HARDCODED_FALLBACK, source: "hardcoded" }
}

let cachedResolved: ResolvedBackendUrl | null = null

export async function getBackendUrl(): Promise<string> {
  if (cachedResolved) return cachedResolved.url
  cachedResolved = await resolveBackendUrl()
  return cachedResolved.url
}

export async function getBackendUrlSource(): Promise<BackendUrlSource> {
  if (cachedResolved) return cachedResolved.source
  cachedResolved = await resolveBackendUrl()
  return cachedResolved.source
}

export async function setBackendUrl(url: string): Promise<void> {
  const normalized = normalize(url)
  cachedResolved = { url: normalized, source: "user-config" }
  await setConfig(CONFIG_KEYS.backendUrl, normalized)
}

export async function clearBackendUrlOverride(): Promise<void> {
  cachedResolved = null
  await setConfig(CONFIG_KEYS.backendUrl, "")
}

export async function probeBackend(url?: string): Promise<BackendStatus> {
  const resolved = url
    ? { url: normalize(url), source: "user-config" as BackendUrlSource }
    : cachedResolved ?? (cachedResolved = await resolveBackendUrl())

  const started = Date.now()
  try {
    const res = await fetch(resolved.url + "/health", {
      method: "GET",
      signal: AbortSignal.timeout(3000),
    })
    const latencyMs = Date.now() - started
    if (!res.ok) {
      return {
        reachable: false, url: resolved.url, source: resolved.source,
        latencyMs, error: "HTTP " + res.status, version: null,
      }
    }
    let version: string | null = null
    try {
      const body = (await res.json()) as { version?: string }
      version = body.version ?? null
    } catch { /* ignore */ }
    return {
      reachable: true, url: resolved.url, source: resolved.source,
      latencyMs, error: null, version,
    }
  } catch (err) {
    return {
      reachable: false, url: resolved.url, source: resolved.source,
      latencyMs: Date.now() - started,
      error: err instanceof Error ? err.message : String(err),
      version: null,
    }
  }
}

export interface AgentRequest {
  sessionId: string
  prompt: string
  workspaceRoot: string | null
  activeFile: string | null
}

export async function postAgent(
  request: AgentRequest,
): Promise<{ ok: boolean; error: string | null }> {
  const base = await getBackendUrl()
  try {
    const res = await fetch(base + "/api/agent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: AbortSignal.timeout(30000),
    })
    if (!res.ok) return { ok: false, error: "HTTP " + res.status }
    return { ok: true, error: null }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}

export function sourceLabel(source: BackendUrlSource): string {
  switch (source) {
    case "runtime-override": return "启动器注入"
    case "user-config": return "手动配置"
    case "build-default": return "构建内置"
    case "env-default": return "环境变量"
    case "hardcoded": return "本地默认"
  }
}
