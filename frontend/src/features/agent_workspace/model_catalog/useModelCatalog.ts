import { useEffect, useMemo, useState } from "react";
import { fetchCatalog, type ModelDescriptor } from "./catalogApi";

type Status = "loading" | "ready" | "error";

export interface ModelCatalogState {
  status: Status;
  models: ModelDescriptor[];
  defaultId: string | null;
  selected: string | null;
  select: (id: string) => void;
}

export function useModelCatalog(): ModelCatalogState {
  const [status, setStatus] = useState<Status>("loading");
  const [models, setModels] = useState<ModelDescriptor[]>([]);
  const [defaultId, setDefaultId] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    const ac = new AbortController();
    fetchCatalog(ac.signal)
      .then((snap) => {
        setModels(snap.models);
        setDefaultId(snap.defaultModelId);
        setSelected(snap.defaultModelId);
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if ((err as { name?: string }).name !== "AbortError") {
          setStatus("error");
        }
      });
    return () => ac.abort();
  }, []);

  return useMemo(
    () => ({ status, models, defaultId, selected, select: setSelected }),
    [status, models, defaultId, selected],
  );
}
