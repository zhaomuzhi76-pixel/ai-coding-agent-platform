import type { IndustrialNav } from "./industrial_sidebar"

export function industrialPageTitle(
 nav: IndustrialNav,
): string {
 return nav === "projects"
  ? "AI Coding Command Center"
  : "Industrial Codex Workspace"
}

export function emptyNavigate(
 _value: IndustrialNav,
): void {
 return
}

export function emptyBoundaryChange(
): void {
 return
}
