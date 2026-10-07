import type {
    PersistedWorkspace,
  } from "./workspace_persistence_contract"

function record(
  value: unknown,
): Record<string, unknown> | null {
  if (
    typeof value !== "object" ||
    value === null ||
    Array.isArray(value)
  ) {
    return null
  }

  return value as Record<string, unknown>
}

export function parseWorkspace(
  value: unknown,
): PersistedWorkspace | null {
  const item =
    record(value)

  if (
    !item ||
    !item.boundary ||
    typeof item.name !== "string" ||
    !(
      item.kind === "directory" ||
      item.kind === "file"
    ) ||    !Array.isArray(item.expanded)
  ) {
    return null
  }
  return {
    version:
      typeof item.version === "number"
        ? item.version
        : 1,
    boundary:
      item.boundary as
        PersistedWorkspace["boundary"],
    name: item.name,
    kind: item.kind,
    activeFile:
      typeof item.activeFile ===
        "string"
        ? item.activeFile
        : null,
    expanded:
      item.expanded.filter(
        value =>
          typeof value ===
          "string",
      )
  }
}
