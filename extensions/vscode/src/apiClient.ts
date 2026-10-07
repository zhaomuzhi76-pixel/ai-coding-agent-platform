import * as vscode from "vscode";

export interface ApiEnvelope<T> {
  ok: boolean;
  data?: T;
  error?: { code: string; message: string; detail?: string };
}

function baseUrl(): string {
  return vscode.workspace
    .getConfiguration("biancheng")
    .get<string>("apiBase", "http://localhost:8000/api/platform");
}

export function currentModel(): string {
  return vscode.workspace
    .getConfiguration("biancheng")
    .get<string>("model", "qwen-max");
}

export function currentLocale(): string {
  return vscode.workspace
    .getConfiguration("biancheng")
    .get<string>("locale", "zh-CN");
}

export function workspacePath(): string {
  return (
    vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? process.cwd()
  );
}

export async function callPlatform<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const url = `${baseUrl()}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
  const body = (await res.json()) as ApiEnvelope<T>;
  if (!body.ok || body.data === undefined) {
    const detail = body.error?.detail ?? "";
    const msg = body.error
      ? `${body.error.code}: ${body.error.message} ${detail}`
      : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return body.data;
}

export function post<T>(path: string, payload: unknown): Promise<T> {
  return callPlatform<T>(path, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function get<T>(path: string): Promise<T> {
  return callPlatform<T>(path, { method: "GET" });
}
