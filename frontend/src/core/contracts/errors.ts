export type ErrorKind =
  | "transport"
  | "protocol"
  | "execution"
  | "session"
  | "validation"
  | "unknown"

export class FrontendError extends Error {
  readonly kind: ErrorKind
  readonly status?: number

  constructor(
    message: string,
    kind: ErrorKind,
    status?: number,
  ) {
    super(message)
    this.name = "FrontendError"
    this.kind = kind
    this.status = status
  }
}

export function errorMessage(
  error: unknown,
): string {
  return error instanceof Error
    ? error.message
    : "frontend operation failed"
}
