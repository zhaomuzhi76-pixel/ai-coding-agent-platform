import {
  useEffect,
  useMemo,
  useState,
} from "react"

import {
  ModelCatalog,
  type ModelProfile,
} from "../../../core/models/model_catalog"

import {
  BrowserModelCatalogStorage,
} from "../../../core/models/model_catalog_storage"

import {
  emptyModelForm,
  loadModelCatalog,
  persistModelCatalog,
  type ModelForm,
} from "./industrial_model_manager_support"

import { matchModelCatalog } from "./industrial_model_manager_sync"


export interface IndustrialModelManagerStateProps {
  current: {
    provider: string
    model: string
    base_url: string
  }
  onSelect: (profile: ModelProfile) => void
}


export function useIndustrialModelManagerState(
  props: IndustrialModelManagerStateProps,
) {
  const storage = useMemo(
    () =>
      new BrowserModelCatalogStorage(
        window.localStorage,
      ),
    [],
  )

  const [catalog,setCatalog] =
    useState<ModelCatalog>(
      () => loadModelCatalog(storage),
    )

  const [editingId,setEditingId] =
    useState<string | null>(null)

  const [form,setForm] =
    useState<ModelForm>(
      emptyModelForm,
    )

  const [error,setError] =
    useState<string | null>(null)


  useEffect(() => {
    const next =
      matchModelCatalog(
        catalog,
        props.current,
      )

    if (!next) return

    persistModelCatalog(
      storage,
      next,
    )

    setCatalog(next)
  }, [
    props.current.base_url,
    props.current.model,
    props.current.provider,
  ])


  function commit(
    next: ModelCatalog,
  ) {
    persistModelCatalog(
      storage,
      next,
    )
    setCatalog(next)
  }


  return {
    catalog,
    setCatalog,
    storage,
    editingId,
    setEditingId,
    form,
    setForm,
    error,
    setError,
    active: catalog.active(),
    commit,
  }
}
