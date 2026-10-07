export interface RecentProject {
  project_id: string
  name: string
  root_path: string
  workspace_id: string | null
}

const STORAGE_KEY = "biancheng.ai.recent-projects"
const LIMIT = 12

function normalize(
  project: Partial<RecentProject>,
): RecentProject | null {
  if (
    typeof project.project_id !== "string"
    || !project.project_id.trim()
    || typeof project.name !== "string"
    || !project.name.trim()
    || typeof project.root_path !== "string"
    || !project.root_path.trim()
  ) {
    return null
  }

  return {
    project_id: project.project_id.trim(),
    name: project.name.trim(),
    root_path: project.root_path.trim(),
    workspace_id:
      typeof project.workspace_id === "string"
        ? project.workspace_id
        : null,
  }
}

export function readRecentProjects(): RecentProject[] {
  try {
    const raw =
      window.localStorage.getItem(STORAGE_KEY)

    if (!raw) return []

    const parsed = JSON.parse(raw)

    if (!Array.isArray(parsed)) return []

    return parsed
      .map(item =>
        normalize(
          item as Partial<RecentProject>,
        ),
      )
      .filter(
        (
          item,
        ): item is RecentProject =>
          item !== null,
      )
  } catch {
    return []
  }
}

export function rememberProject(
  project: RecentProject,
): RecentProject[] {
  const normalized = normalize(project)

  if (!normalized) {
    return readRecentProjects()
  }

  const next = [
    normalized,
    ...readRecentProjects().filter(
      item =>
        item.project_id !==
        normalized.project_id,
    ),
  ].slice(0, LIMIT)

  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(next),
  )

  return next
}

export function forgetProject(
  projectId: string,
): RecentProject[] {
  const next =
    readRecentProjects().filter(
      item =>
        item.project_id !== projectId,
    )

  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(next),
  )

  return next
}
