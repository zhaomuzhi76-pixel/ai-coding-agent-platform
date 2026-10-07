const { MongoClient, ObjectId } = require("mongodb")
const crypto = require("node:crypto")
const fs = require("node:fs/promises")
const path = require("node:path")

const MONGO_URL = process.env.MONGO_URL || "mongodb://127.0.0.1:27017"
const DB_NAME = "biancheng_ai_agent"
const SKIP = new Set(["node_modules", ".git", "dist", "build", ".cache"])

let client = null, db = null, available = false
function sha1(buf) { return crypto.createHash("sha1").update(buf).digest("hex") }
function toRel(root, p) { return path.relative(root, p).replace(/\\/g, "/") || "." }

async function ensureIndexes() {
  await db.collection("file_nodes").createIndex({ workspaceId: 1, path: 1 }, { unique: true })
  await db.collection("file_nodes").createIndex({ workspaceId: 1, parentPath: 1 })
  await db.collection("file_nodes").createIndex({ workspaceId: 1, isExpanded: 1 })
  await db.collection("workspaces").createIndex({ rootPath: 1 }, { unique: true })
  await db.collection("agent_events").createIndex({ sessionId: 1, ts: 1 })
  await db.collection("agent_patches").createIndex({ sessionId: 1, createdAt: 1 })
  await db.collection("file_history").createIndex({ sessionId: 1, filePath: 1 })
}

async function connect() {
  if (available) return true
  try {
    client = new MongoClient(MONGO_URL, { serverSelectionTimeoutMS: 2500 })
    await client.connect()
    db = client.db(DB_NAME)
    await db.command({ ping: 1 })
    await ensureIndexes()
    available = true
    console.log("[mongo] connected", MONGO_URL, "/", DB_NAME)
    return true
  } catch (e) {
    console.warn("[mongo] fallback to JSON:", e.message)
    available = false
    return false
  }
}
function isAvailable() { return available }
async function close() { if (client) await client.close() }

async function saveWorkspace(rootPath, rootName) {
  if (!available) return null
  const now = new Date()
  const doc = await db.collection("workspaces").findOneAndUpdate(
    { rootPath },
    { $set: { rootName, lastOpenedAt: now }, $setOnInsert: { createdAt: now } },
    { upsert: true, returnDocument: "after" }
  )
  return { id: doc._id.toString(), rootPath: doc.rootPath, rootName: doc.rootName }
}

async function loadWorkspace(rootPath) {
  if (!available) return null
  const doc = await db.collection("workspaces").findOne({ rootPath })
  if (!doc) return null
  return { id: doc._id.toString(), rootPath: doc.rootPath, rootName: doc.rootName }
}

async function listChildren(workspaceId, parentPath) {
  if (!available) return []
  return db.collection("file_nodes")
    .find({ workspaceId, parentPath })
    .sort({ kind: 1, name: 1 })
    .toArray()
}

async function setExpanded(workspaceId, nodePath, isExpanded) {
  if (!available) return false
  await db.collection("file_nodes").updateOne(
    { workspaceId, path: nodePath },
    { $set: { isExpanded: !!isExpanded, updatedAt: new Date() } }
  )
  return true
}

async function listExpanded(workspaceId) {
  if (!available) return []
  const docs = await db.collection("file_nodes")
    .find({ workspaceId, isExpanded: true, kind: "directory" }, { projection: { path: 1 } })
    .sort({ path: 1 })
    .toArray()
  return docs.map(d => d.path)
}

// Merkle + mtime 增量扫描
async function incrementalScan(workspaceId, rootPath, dirPath) {
  if (!available) return 0
  let entries
  try { entries = await fs.readdir(dirPath, { withFileTypes: true }) } catch { return 0 }

  const parentRel = dirPath === rootPath ? "." : toRel(rootPath, dirPath)
  const diskPaths = new Set()
  const ops = []

  for (const entry of entries) {
    if (SKIP.has(entry.name)) continue
    const full = path.join(dirPath, entry.name)
    const rel = toRel(rootPath, full)
    diskPaths.add(rel)

    let stat
    try { stat = await fs.stat(full) } catch { continue }
    const kind = entry.isDirectory() ? "directory" : "file"
    let contentHash = null

    if (kind === "file") {
      const prev = await db.collection("file_nodes").findOne(
        { workspaceId, path: rel },
        { projection: { mtime: 1, contentHash: 1 } }
      )
      const mtimeMs = stat.mtimeMs
      const prevMs = prev?.mtime ? new Date(prev.mtime).getTime() : 0
      if (prev?.contentHash && Math.abs(mtimeMs - prevMs) < 1000) {
        contentHash = prev.contentHash // mtime 未变，跳过 hash 计算
      } else {
        try { contentHash = sha1(await fs.readFile(full)) } catch { contentHash = null }
      }
    }

    ops.push({
      updateOne: {
        filter: { workspaceId, path: rel },
        update: {
          $set: {
            workspaceId, path: rel, parentPath: parentRel,
            name: entry.name, kind, size: stat.size,
            mtime: stat.mtime, contentHash, updatedAt: new Date(),
          },
          $setOnInsert: { createdAt: new Date(), isExpanded: false },
        },
        upsert: true,
      },
    })
  }

  const existing = await db.collection("file_nodes")
    .find({ workspaceId, parentPath: parentRel }, { projection: { path: 1 } })
    .toArray()
  const stale = existing.filter(c => !diskPaths.has(c.path)).map(c => c.path)
  if (stale.length > 0) {
    ops.push({ deleteMany: { filter: { workspaceId, path: { $in: stale } } } })
  }

  if (ops.length === 0) return 0
  const r = await db.collection("file_nodes").bulkWrite(ops)
  return r.upsertedCount + r.modifiedCount + r.deletedCount
}

// ============ Agent 执行结果 ============
async function upsertSession(sessionId, payload) {
  if (!available) return false
  const now = new Date()
  await db.collection("sessions").updateOne(
    { sessionId },
    { $set: { ...payload, updatedAt: now }, $setOnInsert: { createdAt: now } },
    { upsert: true }
  )
  return true
}

async function appendAgentEvent(sessionId, event) {
  if (!available) return false
  await db.collection("agent_events").insertOne({
    sessionId, ts: new Date(), event,
  })
  return true
}

async function listAgentEvents(sessionId, limit = 1000) {
  if (!available) return []
  const docs = await db.collection("agent_events")
    .find({ sessionId }).sort({ ts: 1 }).limit(limit).toArray()
  return docs.map(d => ({ _id: d._id.toString(), ts: d.ts, event: d.event }))
}

async function savePatch(patch) {
  if (!available) return null
  const now = new Date()
  const r = await db.collection("agent_patches").insertOne({
    ...patch, status: patch.status || "pending",
    createdAt: now, updatedAt: now,
  })
  return r.insertedId.toString()
}

async function updatePatchStatus(patchId, status) {
  if (!available) return false
  await db.collection("agent_patches").updateOne(
    { _id: new ObjectId(patchId) },
    { $set: { status, updatedAt: new Date() } }
  )
  return true
}

async function listPatches(sessionId) {
  if (!available) return []
  const docs = await db.collection("agent_patches")
    .find({ sessionId }).sort({ createdAt: 1 }).toArray()
  return docs.map(d => ({ ...d, _id: d._id.toString() }))
}

function registerMongoIpc(ipcMain) {
  ipcMain.handle("mongo:is-available", () => isAvailable())
  ipcMain.handle("mongo:save-workspace", (_e, p, n) => saveWorkspace(p, n))
  ipcMain.handle("mongo:load-workspace", (_e, p) => loadWorkspace(p))
  ipcMain.handle("mongo:list-children", (_e, w, p) => listChildren(w, p))
  ipcMain.handle("mongo:set-expanded", (_e, w, p, x) => setExpanded(w, p, x))
  ipcMain.handle("mongo:list-expanded", (_e, w) => listExpanded(w))
  ipcMain.handle("mongo:incremental-scan", (_e, w, r, d) => incrementalScan(w, r, d))
  ipcMain.handle("mongo:session-upsert", (_e, s, p) => upsertSession(s, p))
  ipcMain.handle("mongo:agent-event-append", (_e, s, ev) => appendAgentEvent(s, ev))
  ipcMain.handle("mongo:agent-event-list", (_e, s, l) => listAgentEvents(s, l))
  ipcMain.handle("mongo:patch-save", (_e, p) => savePatch(p))
  ipcMain.handle("mongo:patch-status", (_e, id, st) => updatePatchStatus(id, st))
  ipcMain.handle("mongo:patch-list", (_e, s) => listPatches(s))
}

module.exports = {
  connect, isAvailable, close, registerMongoIpc,
  saveWorkspace, loadWorkspace, listChildren, setExpanded, listExpanded, incrementalScan,
  upsertSession, appendAgentEvent, listAgentEvents,
  savePatch, updatePatchStatus, listPatches,
}
