export function lineCount(
  content: string,
): number {
  return Math.max(
    1,
    content.split("\n").length,
  )
}

export function statusLabel(
  loading: boolean,
  saving: boolean,
  loadError: string | null,
  saveError: string | null,
  dirty: boolean,
): string {
  if (loadError) return "Load error"
  if (saveError) return "Save error"
  if (loading) return "Loading"
  if (saving) return "Saving"
  return dirty ? "Modified" : "Saved"
}

export function editorText(
  element: HTMLElement,
): string {
  return element.innerText
    .replace(/\r\n/g, "\n")
}
