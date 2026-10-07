export type ResourceTargetKind =
  | "directory"
  | "file"

export interface AgentResourceBoundary {
  projectId: string | null
  workspace: string
  targetPath: string
  targetKind: ResourceTargetKind
}

export function createResourceBoundary(
  input: AgentResourceBoundary,
): AgentResourceBoundary {
  if (
    typeof input.workspace !== "string"
    || !input.workspace.trim()
  ) {
    throw new Error(
      "resource workspace required",
    )
  }

  if (
    input.projectId !== null
    && (
      typeof input.projectId !== "string"
      || !input.projectId.trim()
    )
  ) {
    throw new Error(
      "resource project id invalid",
    )
  }

  if (
    input.targetKind !== "directory"
    && input.targetKind !== "file"
  ) {
    throw new Error(
      "resource target kind invalid",
    )
  }

  return {
    projectId:
      input.projectId?.trim() ?? null,
    workspace: input.workspace.trim(),
    targetPath: normalizeTargetPath(
      input.targetPath,
    ),
    targetKind: input.targetKind,
  }
}

export function normalizeTargetPath(
  value: string,
): string {
  if (
    typeof value !== "string"
  ) {
    throw new Error(
      "resource target path required",
    )
  }

  const normalized =
    value.trim().replaceAll("\\", "/")

  if (
    !normalized
    || normalized === "."
  ) {
    return "."
  }

  if (
    normalized.startsWith("/")
    || /^[A-Za-z]:\//.test(normalized)
  ) {
    throw new Error(
      "resource target path must be relative",
    )
  }

  const parts = normalized.split("/")
  const clean: string[] = []

  for (const part of parts) {
    if (!part || part === ".") {
      continue
    }

    if (part === "..") {
      throw new Error(
        "resource target path escapes workspace",
      )
    }

    clean.push(part)
  }

  return clean.join("/") || "."
}

export function resourcePath(
  boundary: AgentResourceBoundary,
): string {
  return boundary.targetPath === "."
    ? boundary.workspace
    : `${boundary.workspace}/${boundary.targetPath}`
}
