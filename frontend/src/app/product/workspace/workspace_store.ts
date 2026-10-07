import type {
  AgentResourceBoundary,
} from "../../../core/resources/resource_boundary"

import type {
  FileNodeSource,
} from "./explorer/file_node_source"

import type {
  WorkspaceSnapshot,
} from "./workspace_contract"

export class WorkspaceStore {
  private listeners: Array<() => void> = []

  private state: WorkspaceSnapshot = {
    project: null,
    activeFile: null,
    activeFileSource: null,
    resourceName: null,
    resourceBoundary: null,
    capabilities: [],
    fileVersion: 0,
  }

  getSnapshot() {
    return this.state
  }

  subscribe(listener: () => void) {
    this.listeners.push(listener)

    return () => {
      this.listeners =
        this.listeners.filter(
          item => item !== listener,
        )
    }
  }

  setProject(project: string) {
    this.state = {
      ...this.state,
      project,
      activeFile: null,
      activeFileSource: null,
      resourceName: null,
      resourceBoundary: null,
    }

    this.notify()
  }

  setResource(
    boundary: AgentResourceBoundary,
    name: string,
    activeFile: string | null,
    activeFileSource: FileNodeSource | null = null,
  ) {
    this.state = {
      ...this.state,
      project:
        boundary.projectId
        ?? boundary.workspace,
      activeFile,
      activeFileSource,
      resourceName: name,
      resourceBoundary: boundary,
    }

    this.notify()
  }

  setBoundary(
    boundary: AgentResourceBoundary,
  ) {
    this.state = {
      ...this.state,
      resourceBoundary: boundary,
    }

    this.notify()
  }

  selectFile(
    file: string,
    source: FileNodeSource | null,
  ) {
    this.state = {
      ...this.state,
      activeFile: file,
      activeFileSource: source,
    }

    this.notify()
  }

  setActiveFileSource(
    source: FileNodeSource | null,
  ) {
    this.state = {
      ...this.state,
      activeFileSource: source,
    }

    this.notify()
  }

  bumpFileVersion() {
    this.state = {
      ...this.state,
      fileVersion: (this.state.fileVersion ?? 0) + 1,
    }
    this.notify()
  }

  private notify() {
    this.listeners.forEach(
      listener => listener(),
    )
  }
}
