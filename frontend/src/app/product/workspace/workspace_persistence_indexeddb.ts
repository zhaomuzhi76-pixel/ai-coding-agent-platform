import type {
  PersistedWorkspace,
} from "./workspace_persistence_contract"

import {
  parseWorkspace,
} from "./workspace_persistence_codec"

const DB_NAME =
  "biancheng.ai.workspace"

const STORE_NAME =
  "workspace"

const DB_VERSION = 1

const DB_KEY =
  "current"

function openDatabase():
  Promise<IDBDatabase> {
  return new Promise(
    (resolve, reject) => {
      if (
        typeof indexedDB ===
        "undefined"
      ) {
        reject(
          new Error(
            "workspace persistence unavailable",
          ),
        )
        return
      }

      const request =
        indexedDB.open(
          DB_NAME,
          DB_VERSION,
        )

      request.onupgradeneeded =
        () => {
          const database =
            request.result

          if (
            !database.objectStoreNames.contains(
              STORE_NAME,
            )
          ) {
            database.createObjectStore(
              STORE_NAME,
            )
          }
        }

      request.onsuccess = () =>
        resolve(
          request.result,
        )

      request.onerror = () =>
        reject(
          request.error ??
            new Error(
              "workspace persistence open failed",
            ),
        )
    },
  )
}

export async function writeIndexedWorkspace(
  workspace: PersistedWorkspace,
): Promise<void> {
  const database =
    await openDatabase()

  await new Promise<void>(
    (resolve, reject) => {
      const transaction =
        database.transaction(
          STORE_NAME,
          "readwrite",
        )

      transaction.oncomplete = () => {
        database.close()
        resolve()
      }

      transaction.onerror = () => {
        database.close()
        reject(
          transaction.error ??
            new Error(
              "workspace persistence write failed",
            ),
        )
      }

      transaction.onabort = () => {
        database.close()
        reject(
          transaction.error ??
            new Error(
              "workspace persistence write aborted",
            ),
        )
      }

      transaction
        .objectStore(
          STORE_NAME,
        )
        .put(
          workspace,
          DB_KEY,
        )
    },
  )
}

export async function readIndexedWorkspace():
  Promise<PersistedWorkspace | null> {
  const database =
    await openDatabase()

  return new Promise(
    (resolve, reject) => {
      const transaction =
        database.transaction(
          STORE_NAME,
          "readonly",
        )

      const request =
        transaction
          .objectStore(
            STORE_NAME,
          )
          .get(DB_KEY)

      request.onsuccess =
        () => {
          database.close()
          resolve(
            parseWorkspace(
              request.result,
            ),
          )
        }

      request.onerror =
        () => {
          database.close()
          reject(
            request.error ??
              new Error(
                "workspace persistence read failed",
              ),
          )
        }
    },
  )
}
