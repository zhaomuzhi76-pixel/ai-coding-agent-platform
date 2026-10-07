"""L4 审核 UI 静态页面 —— 单文件内嵌 HTML/CSS/JS。"""
from __future__ import annotations

HTML = """<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8"><title>草稿审核 — L23</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#f4f5f7;color:#1f2937}
.header{background:#fff;padding:16px 24px;border-bottom:1px solid #e5e7eb;display:flex;
  justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10}
.header h1{font-size:18px;font-weight:600}
.meta{color:#6b7280;font-size:13px;margin-top:4px}
.actions button{padding:8px 16px;margin-left:8px;border-radius:6px;border:1px solid #d1d5db;
  background:#fff;cursor:pointer;font-size:14px}
.actions button.primary{background:#3b82f6;color:#fff;border-color:#3b82f6}
.actions button.danger{background:#fff;color:#dc2626;border-color:#fca5a5}
.wrap{padding:20px 24px;max-width:1200px;margin:0 auto}
.search{width:100%;padding:10px 14px;border:1px solid #d1d5db;border-radius:8px;
  font-size:14px;margin-bottom:16px}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:16px;
  margin-bottom:12px;transition:box-shadow .15s}
.card:hover{box-shadow:0 4px 12px rgba(0,0,0,.06)}
.card.miss{opacity:.55;border-style:dashed}
.card-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.card-id{font-family:monospace;color:#6b7280;font-size:12px}
.rank{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
.rank.hit{background:#dcfce7;color:#166534}
.rank.miss{background:#f3f4f6;color:#6b7280}
.content{font-size:14px;line-height:1.6;margin:8px 0;white-space:pre-wrap;
  max-height:180px;overflow-y:auto;padding:8px;background:#f9fafb;border-radius:6px}
.bars{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px}
.bar-label{font-size:11px;color:#6b7280;margin-bottom:4px;display:flex;
  justify-content:space-between}
.bar-track{height:8px;background:#e5e7eb;border-radius:4px;overflow:hidden}
.bar-fill{height:100%;transition:width .3s}
.bar-bm25{background:#60a5fa}
.bar-rerank{background:#a78bfa}
.card-actions{margin-top:12px;display:flex;gap:8px}
.card-actions button{padding:5px 12px;font-size:12px;border:1px solid #d1d5db;
  border-radius:5px;background:#fff;cursor:pointer}
.card-actions button.del{color:#dc2626;border-color:#fca5a5}
.empty{text-align:center;padding:60px 20px;color:#9ca3af}
.toast{position:fixed;bottom:24px;right:24px;background:#1f2937;color:#fff;
  padding:12px 20px;border-radius:8px;font-size:14px;opacity:0;transition:opacity .3s}
.toast.show{opacity:1}
</style></head><body>
<div class="header">
  <div><h1 id="title">草稿审核</h1><div class="meta" id="meta">加载中…</div></div>
  <div class="actions" id="actions"></div>
</div>
<div class="wrap">
  <input class="search" id="query" placeholder="输入查询词预览召回效果…">
  <div id="list"></div>
</div>
<div class="toast" id="toast"></div>
<script>
const API = '/api/rag/review/ui';
const state = {job_id: '', query: '', chunks: [], edits: {}};
const $ = id => document.getElementById(id);
const toast = msg => { const t = $('toast'); t.textContent = msg;
  t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 1800); };

function jobId() {
  return new URLSearchParams(location.search).get('job_id') || state.job_id;
}

async function load(jid, q) {
  const r = await fetch(`${API}/page?job_id=${encodeURIComponent(jid)}&query=${encodeURIComponent(q||'')}`);
  if (!r.ok) { $('list').innerHTML = `<div class="empty">加载失败：${r.status}</div>`; return; }
  const d = await r.json();
  state.job_id = d.job_id; state.query = d.query; state.chunks = d.chunks;
  $('title').textContent = `草稿审核 — ${d.job_id}`;
  $('meta').textContent = `共 ${d.total} 块 · 命中 ${d.hit_count} · 已选 ${d.selected_count}`;
  renderActions(d.actions); renderChunks(d.chunks);
}

function renderActions(actions) {
  $('actions').innerHTML = '';
  actions.forEach(a => {
    const b = document.createElement('button');
    b.textContent = a.label;
    if (a.style === 'primary') b.className = 'primary';
    if (a.style === 'danger') b.className = 'danger';
    b.onclick = () => submit(a.id);
    $('actions').appendChild(b);
  });
}

function renderChunks(chunks) {
  if (!chunks.length) { $('list').innerHTML = '<div class="empty">无草稿块</div>'; return; }
  $('list').innerHTML = chunks.map((c, i) => `
    <div class="card ${c.is_hit ? '' : 'miss'}" data-idx="${i}">
      <div class="card-head">
        <span class="card-id">${c.chunk_id} · 原始序 ${c.order}</span>
        <span class="rank ${c.is_hit ? 'hit' : 'miss'}">
          ${c.is_hit ? `召回 #${c.rank}` : '未召回'}</span>
      </div>
      <div class="content">${esc(c.content)}</div>
      <div class="bars">
        <div><div class="bar-label"><span>BM25</span><span>${c.bm25.toFixed(2)}</span></div>
          <div class="bar-track"><div class="bar-fill bar-bm25" style="width:${c.bm25_bar*100}%"></div></div></div>
        <div><div class="bar-label"><span>Reranker</span><span>${c.rerank.toFixed(4)}</span></div>
          <div class="bar-track"><div class="bar-fill bar-rerank" style="width:${c.rerank_bar*100}%"></div></div></div>
      </div>
      <div class="card-actions">
        <button onclick="toggleKeep(${i})">${c.selected ? '✓ 保留' : '○ 未选'}</button>
        <button onclick="editChunk(${i})">编辑</button>
        <button class="del" onclick="toggleDel(${i})">标记删除</button>
      </div>
    </div>`).join('');
}

function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

window.toggleKeep = i => { state.chunks[i].selected = !state.chunks[i].selected;
  state.chunks[i].action = state.chunks[i].selected ? 'keep' : 'delete'; renderChunks(state.chunks); };

window.toggleDel = i => { const c = state.chunks[i];
  c.selected = false; c.action = 'delete'; renderChunks(state.chunks); };

window.editChunk = i => { const c = state.chunks[i];
  const next = prompt('编辑内容：', c.content);
  if (next !== null && next !== c.content) {
    c.content = next; state.edits[c.chunk_id] = {chunk_id: c.chunk_id, content: next, order: c.order};
    renderChunks(state.chunks); toast('已编辑，保存时生效');
  }};

async function submit(action) {
  const approved = state.chunks.filter(c => c.selected).map(c => c.chunk_id);
  const edits = Object.values(state.edits);
  const body = {action, approved_chunk_ids: approved, edits};
  const url = action === 'reject' ? `${API}/reject` : `${API}/approve`;
  const r = await fetch(`${url}?job_id=${encodeURIComponent(state.job_id)}`,
    {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  if (r.ok) { const d = await r.json(); toast(`完成：${d.action || action}，写入 ${d.written ?? 0} 块`);
    setTimeout(() => location.reload(), 1200); }
  else { toast(`失败：${r.status}`); }
}

$('query').addEventListener('keydown', e => {
  if (e.key === 'Enter') { state.query = e.target.value; load(jobId(), state.query); }
});

load(jobId(), new URLSearchParams(location.search).get('query') || '');
</script></body></html>
"""


def html() -> str:
    return HTML
