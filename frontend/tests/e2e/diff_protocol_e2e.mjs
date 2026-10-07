/**
 * diff 协议级 E2E（无浏览器）。
 *
 * 关键修复：pending 查询加时间戳过滤
 *   · 记录 task_start_ts（秒，小数）
 *   · SQL: WHERE status='pending' AND created_at > task_start_ts
 *   · 避免误拿历史僵尸 pending
 *
 * 双路径：HTTP /api/agent/pending → SQLite 兜底
 */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execFileSync } from "node:child_process";

const WS_URL = process.env.E2E_WS_URL || "ws://127.0.0.1:9022/ws/agent";
const HTTP = process.env.E2E_HTTP || "http://127.0.0.1:9022";
const WS_ROOT = process.env.E2E_WORKSPACE || "/dev/shm/prog_full_ws";
const MODEL = process.env.E2E_MODEL || "qwen2.5-coder:7b";
const TARGET = path.join(WS_ROOT, "e2e_target.py");
const DB = `${process.env.HOME || "/root"}/.biancheng/metrics.db`;

let fails = 0;
const ok = (n, m) => console.log(`  ${n.padEnd(28)} OK   ${m}`);
const ng = (n, m) => { console.log(`  ${n.padEnd(28)} FAIL ${m}`); fails++; };

function sha(p) {
  try { return crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex"); }
  catch { return ""; }
}

function wsConnect() {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(WS_URL);
    const t = setTimeout(() => { try { ws.close(); } catch {} reject(new Error("ws timeout")); }, 5000);
    ws.addEventListener("open", () => { clearTimeout(t); resolve(ws); });
    ws.addEventListener("error", (e) => { clearTimeout(t); reject(e); });
  });
}

async function runTask(prompt) {
  const ws = await wsConnect();
  const execSid = `e2e-${Math.random().toString(36).slice(2, 12)}`;
  const events = [];
  const done = new Promise((resolve) => {
    ws.addEventListener("message", (ev) => {
      try {
        const m = JSON.parse(ev.data);
        events.push(m);
        if (m.type === "end" || m.type === "error") resolve();
      } catch {}
    });
    ws.addEventListener("close", resolve);
  });
  ws.send(JSON.stringify({
    session_id: execSid, message: prompt, provider: "ollama", model: MODEL,
    workspace: WS_ROOT, base_url: "", api_key: "", domains: [], stream: true,
  }));
  await Promise.race([done, new Promise(r => setTimeout(r, 120000))]);
  try { ws.close(); } catch {}
  return events;
}

/** 时间戳过滤：只返回本次任务创建的 pending（取第一条，FIFO 与 LLM 步序一致）。 */
function fetchNewPendingFromDb(startTs) {
  try {
    const sql = `SELECT edit_id FROM pending_edits WHERE status='pending' AND created_at > ${startTs} ORDER BY created_at ASC LIMIT 1;`;
    const out = execFileSync("sqlite3", [DB, sql], { encoding: "utf8" }).trim();
    return out || null;
  } catch {
    // 无 sqlite3 CLI → python3
    try {
      const py = `
import sqlite3
c=sqlite3.connect("${DB}")
r=c.execute("SELECT edit_id FROM pending_edits WHERE status='pending' AND created_at > ${startTs} ORDER BY created_at ASC LIMIT 1").fetchone()
print(r[0] if r else "")
`;
      const out = execFileSync("python3", ["-c", py], { encoding: "utf8" }).trim();
      return out || null;
    } catch { return null; }
  }
}

async function approve(editId) {
  const r = await fetch(`${HTTP}/api/agent/approve/${editId}`, { method: "POST" });
  return r.status;
}

async function reject(editId) {
  const r = await fetch(`${HTTP}/api/agent/reject/${editId}`, { method: "POST" });
  return r.status;
}

async function scenario(name, prompt, decision, expectChange) {
  console.log(`\n  ── [${name}] ${decision} ──`);
  fs.writeFileSync(TARGET, "value = 1\n");
  const before = sha(TARGET);
  console.log(`    before sha=${before.slice(0, 12)}`);

  const startTs = (Date.now() / 1000) - 0.5;  // 半秒容差
  const task = runTask(prompt);

  // 轮询等 pending（时间戳过滤）
  let editId = null;
  for (let i = 0; i < 90; i++) {
    await new Promise(r => setTimeout(r, 1000));
    editId = fetchNewPendingFromDb(startTs);
    if (editId) break;
  }
  if (!editId) { ng(`${name} 捕获 pending`, "90s 无 pending（时间戳过滤后）"); await task; return; }
  ok(`${name} 捕获 pending`, `${editId} (created > ${startTs.toFixed(1)})`);

  const st = decision === "approve" ? await approve(editId) : await reject(editId);
  ok(`${name} ${decision}`, `HTTP ${st}`);

  // 等 WS 结束
  await task;

  const after = sha(TARGET);
  const content = fs.readFileSync(TARGET, "utf8");
  const changed = before !== after;
  if (expectChange) {
    if (changed && content.includes("42")) ok(`${name} 文件真改`, `after=${after.slice(0, 12)}`);
    else ng(`${name} 文件真改`, `after=${after.slice(0, 12)} content=${JSON.stringify(content)}`);
  } else {
    if (!changed) ok(`${name} 文件未改`, "OK");
    else ng(`${name} 文件未改`, `after=${after.slice(0, 12)}`);
  }
}

async function main() {
  console.log(`  WS=${WS_URL}  WS_ROOT=${WS_ROOT}`);
  await scenario("A 批准", "把 e2e_target.py 里的 value = 1 改成 value = 42", "approve", true);
  await scenario("B 拒绝", "把 e2e_target.py 里的 value = 1 改成 value = 99", "reject", false);
  console.log();
  console.log(`  ══ diff 协议级 E2E: ${fails === 0 ? "ALL PASS ✅" : fails + " 项失败 ❌"} ══`);
  process.exit(fails === 0 ? 0 : 1);
}

main().catch(e => { console.log("  ❌", e.message); process.exit(1); });
