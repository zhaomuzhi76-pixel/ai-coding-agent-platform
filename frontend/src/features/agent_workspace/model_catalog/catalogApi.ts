export interface ModelDescriptor {
  id: string;
  provider: string;
  displayName: string;
  contextWindow: number;
  isDefault: boolean;
}

export interface CatalogSnapshot {
  defaultModelId: string;
  models: ModelDescriptor[];
}

export async function fetchCatalog(
  signal?: AbortSignal,
): Promise<CatalogSnapshot> {
  const res = await fetch("/api/providers/catalog", { signal });
  if (!res.ok) throw new Error(`catalog ${res.status}`);
  return (await res.json()) as CatalogSnapshot;
}
