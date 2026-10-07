import type {
  FileNode,
} from "./file_tree_store"

import type {
  WorkspaceResourceEntry,
} from "./resource_contract"

function mapLazyChildren(
  loader:
    (() =>
      Promise<WorkspaceResourceEntry[]>) |
    undefined,
) {
  return loader
    ? async () =>
        mapResourceFiles(
          await loader(),
        )
    : undefined
}

export function mapResourceFiles(
  files: WorkspaceResourceEntry[],
): FileNode[] {
  const roots: FileNode[] = []

  for (const file of files) {
    const parts =
      file.name
        .split("/")
        .filter(Boolean)

    let current =
      roots

    parts.forEach(
      (part, index) => {
        const last =
          index === parts.length - 1

        let node =
          current.find(
            item =>
              item.name === part,
          )

        if (!node) {
          node = {
            name: part,
            type:
              last
                ? file.type
                : "directory",
            ...(last
              ? {
                  ...(file.source
                    ? {
                        source:
                          file.source,
                      }
                    : {}),
                  ...(file.loadChildren
                    ? {
                        loaded: false,
                        loadChildren:
                          mapLazyChildren(
                            file.loadChildren,
                          ),
                      }
                    : {}),
                }
              : {
                  children: [],
                  loaded: true,
                }),
          }

          current.push(node)
        }

        if (!last) {
          if (!node.children) {
            node.children = []
          }

          current =
            node.children
        }
      },
    )
  }

  return sortNodes(roots)
}

function sortNodes(
  nodes: FileNode[],
): FileNode[] {
  return nodes
    .map(
      node => ({
        ...node,
        ...(node.children
          ? {
              children:
                sortNodes(
                  node.children,
                ),
            }
          : {}),
      }),
    )
    .sort(
      (a, b) =>
        a.type === b.type
          ? a.name.localeCompare(
              b.name,
            )
          : a.type === "directory"
            ? -1
            : 1,
    )
}
