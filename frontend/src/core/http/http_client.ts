import { runtimeConfig } from "../config/runtime"

export interface HttpErrorPayload {
  error?: string
  [key: string]: unknown
}

export class HttpError extends Error {
  readonly status: number
  readonly payload: HttpErrorPayload

  constructor(
    status: number,
    payload: HttpErrorPayload,
  ) {
    super(
      typeof payload.error === "string"
        ? payload.error
        : `HTTP ${status}`,
    )
    this.name = "HttpError"
    this.status = status
    this.payload = payload
  }
}

export async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(
    `${runtimeConfig.apiBaseUrl}${path}`,
    {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init.headers ?? {}),
      },
    },
  )

  const payload = (await response.json()) as unknown

  if (!response.ok) {
    throw new HttpError(
      response.status,
      isObject(payload) ? payload : {},
    )
  }

  return payload as T
}

function isObject(
  value: unknown,
): value is HttpErrorPayload {
  return (
    typeof value === "object"
    && value !== null
  )
}
