import {
  createContext,
  useContext,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from "react"

import {
  createControlPlaneCapability,
  type ControlPlaneCapability,
} from "../composition/control_plane_composition"


interface ControlPlaneContextValue
  extends ControlPlaneCapability {
}


const ControlPlaneContext =
  createContext<ControlPlaneContextValue | null>(
    null,
  )


export function ControlPlaneProvider(
  props: {
    children: ReactNode
  },
) {

  const value =
    useMemo(
      () =>
        createControlPlaneCapability(),
      [],
    )


  return (
    <ControlPlaneContext.Provider
      value={value}
    >
      {props.children}
    </ControlPlaneContext.Provider>
  )
}


export function useControlPlaneContext() {

  const value =
    useContext(ControlPlaneContext)

  if (!value) {
    throw new Error(
      "control plane context required",
    )
  }

  return value
}


export function useProjectSessionState() {

  const {
    projectSession,
  } =
    useControlPlaneContext()


  return useSyncExternalStore(
    projectSession.store.subscribe.bind(
      projectSession.store,
    ),
    projectSession.store.getSnapshot.bind(
      projectSession.store,
    ),
  )
}


export function useAgentWorkspaceState() {

  const {
    agentWorkspaceStore,
  } =
    useControlPlaneContext()


  return useSyncExternalStore(
    agentWorkspaceStore.subscribe.bind(
      agentWorkspaceStore,
    ),
    agentWorkspaceStore.getSnapshot.bind(
      agentWorkspaceStore,
    ),
  )
}
