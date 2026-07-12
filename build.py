#!/usr/bin/env python3
"""
build.py — Genera index.html con datos embebidos de Instagram + Supabase sync.

Uso:
  python build.py [--supabase-url URL] [--supabase-key KEY]

  Si no pasás --supabase-url ni --supabase-key, el HTML se genera
  con placeholders que podés editar a mano después.

Requiere:
  - Python 3.7+
  - docs/json/following.json (export de Instagram)
  - docs/json/followers_1.json (export de seguidores, opcional)
"""

import json
import os
import argparse
import html as html_mod
from datetime import datetime, timezone

# ─── Config ───────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(SCRIPT_DIR, "docs", "json")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "index.html")

# ─── Leer exports ─────────────────────────────────────────────────────

def read_following():
    path = os.path.join(JSON_DIR, "following.json")
    if not os.path.exists(path):
        print(f"[WARN] No se encuentra: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    users = []
    for entry in data.get("relationships_following", []):
        username = entry.get("title", "")
        if not username:
            continue
        sd = entry.get("string_list_data", [])
        if not sd:
            continue
        users.append({
            "u": username,
            "h": sd[0].get("href", ""),
            "t": sd[0].get("timestamp", 0),
        })
    return users


def read_followers():
    path = os.path.join(JSON_DIR, "followers_1.json")
    if not os.path.exists(path):
        print(f"[WARN] No se encuentra: {path}")
        return set()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    followers = set()
    for entry in data:
        sd = entry.get("string_list_data", [])
        if sd:
            username = sd[0].get("value", "")
            if username:
                followers.add(username.lower())
    return followers


# ─── Build HTML ───────────────────────────────────────────────────────

def build_html(users, followers, supabase_url="", supabase_anon_key=""):
    # Serializar users como JSON compacto
    users_json = json.dumps(users, separators=(",", ":"))

    # Serializar followers set como Set literal (más rápido en JS)
    followers_json = json.dumps(sorted(followers))

    # Stats para el banner
    total = len(users)
    followers_count = len(followers)

    # Años disponibles
    years = sorted(set(
        datetime.fromtimestamp(u["t"], tz=timezone.utc).year
        for u in users if u["t"]
    ), reverse=True)
    years_json = json.dumps(years)

    supabase_code = ""
    if supabase_url and supabase_anon_key:
        supabase_code = f"""
  const SUPABASE_URL = {json.dumps(supabase_url)};
  const SUPABASE_ANON_KEY = {json.dumps(supabase_anon_key)};
"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Instagram Unfollow Tool</title>
<script src="https://unpkg.com/@supabase/supabase-js@2"></script>
<style>
  :root {{
    --bg: #0f0f0f;
    --surface: #1a1a1a;
    --surface2: #242424;
    --border: #2e2e2e;
    --text: #e8e8e8;
    --text2: #999;
    --accent: #5b8def;
    --green: #2ecc71;
    --red: #e74c3c;
    --orange: #f39c12;
    --purple: #9b59b6;
    --gray: #666;
    --radius: 8px;
    --shadow: 0 2px 8px rgba(0,0,0,.3);
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 16px;
    min-height: 100vh;
  }}
  .header {{
    max-width: 1200px; margin: 0 auto 16px;
    display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
    justify-content: space-between;
  }}
  .header h1 {{ font-size: 20px; font-weight: 700; }}
  .stats {{ display: flex; gap: 12px; flex-wrap: wrap; font-size: 13px; }}
  .stat {{ background: var(--surface); padding: 6px 12px; border-radius: var(--radius); }}
  .stat b {{ color: var(--accent); }}
  .sync-badge {{
    font-size: 12px; padding: 4px 10px; border-radius: 12px;
    background: var(--surface2); border: 1px solid var(--border);
    display: inline-flex; align-items: center; gap: 4px;
  }}
  .sync-badge.ok {{ border-color: var(--green); color: var(--green); }}
  .sync-badge.err {{ border-color: var(--red); color: var(--red); }}
  .sync-badge.syncing {{ border-color: var(--orange); color: var(--orange); }}

  .controls {{
    max-width: 1200px; margin: 0 auto 16px;
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
  }}
  .controls button,
  .controls .btn {{
    background: var(--surface); color: var(--text); border: 1px solid var(--border);
    padding: 6px 14px; border-radius: var(--radius); cursor: pointer;
    font-size: 13px; transition: all .15s;
  }}
  .controls button:hover {{ background: var(--surface2); }}
  .controls button.active {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
  .controls button.keep.active {{ background: var(--green); border-color: var(--green); }}
  .controls button.unfollow.active {{ background: var(--red); border-color: var(--red); }}
  .controls button.deleted.active {{ background: var(--gray); border-color: var(--gray); }}
  .controls button.private.active {{ background: var(--purple); border-color: var(--purple); }}
  .controls button.pending.active {{ background: var(--orange); border-color: var(--orange); }}

  .year-chips {{
    display: flex; flex-wrap: wrap; gap: 4px; margin: 8px 0;
  }}
  .year-chips button {{
    background: var(--surface); border: 1px solid var(--border);
    color: var(--text2); padding: 2px 10px; border-radius: 12px;
    cursor: pointer; font-size: 12px; transition: all .15s;
  }}
  .year-chips button.active {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
  .year-chips button:hover {{ background: var(--surface2); }}

  .session-bar {{
    max-width: 1200px; margin: 0 auto 16px;
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
    font-size: 13px; color: var(--text2);
  }}
  .session-bar input {{
    width: 70px; background: var(--surface); border: 1px solid var(--border);
    color: var(--text); padding: 4px 8px; border-radius: var(--radius); font-size: 13px;
  }}

  .grid {{
    max-width: 1200px; margin: 0 auto;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 8px;
  }}
  .card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 12px;
    display: flex; flex-direction: column; gap: 6px;
    transition: all .3s ease; position: relative;
    opacity: 1; transform: scale(1);
  }}
  .card.dismissing {{
    opacity: 0; transform: scale(.8) translateY(-10px);
    pointer-events: none;
  }}
  .card.hidden {{ display: none; }}
  .card .avatar {{
    width: 40px; height: 40px; border-radius: 50%;
    background: var(--surface2); display: flex; align-items: center; justify-content: center;
    font-size: 18px; font-weight: 600; color: var(--accent);
    overflow: hidden; flex-shrink: 0;
  }}
  .card .avatar img {{ width: 100%; height: 100%; object-fit: cover; }}
  .card .uname {{
    font-size: 13px; font-weight: 600; color: var(--text);
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }}
  .card .uname a {{ color: inherit; text-decoration: none; }}
  .card .uname a:hover {{ text-decoration: underline; }}
  .card .meta {{ font-size: 11px; color: var(--text2); }}
  .card .actions {{ display: flex; gap: 4px; flex-wrap: wrap; }}
  .card .actions button {{
    flex: 1; min-width: 36px; padding: 4px 6px; border-radius: 4px;
    border: 1px solid var(--border); background: var(--surface2);
    color: var(--text2); cursor: pointer; font-size: 11px;
    transition: all .15s; text-align: center;
  }}
  .card .actions button:hover {{ background: var(--border); }}
  .card .actions button.s-keep {{ border-color: var(--green); }}
  .card .actions button.s-keep.active {{ background: var(--green); color: #fff; }}
  .card .actions button.s-unfollow {{ border-color: var(--red); }}
  .card .actions button.s-unfollow.active {{ background: var(--red); color: #fff; }}
  .card .actions button.s-deleted {{ border-color: var(--gray); }}
  .card .actions button.s-deleted.active {{ background: var(--gray); color: #fff; }}
  .card .actions button.s-private {{ border-color: var(--purple); }}
  .card .actions button.s-private.active {{ background: var(--purple); color: #fff; }}
  .card .actions button.s-pending {{ border-color: var(--orange); }}
  .card .actions button.s-pending.active {{ background: var(--orange); color: #fff; }}
  .card .badge {{
    font-size: 10px; padding: 1px 6px; border-radius: 10px;
    background: var(--surface2); color: var(--text2);
    align-self: flex-start;
  }}
  .card .badge.nfb {{ background: #2c1810; color: #e67e22; }}

  .toast {{
    position: fixed; bottom: 20px; right: 20px;
    background: var(--surface2); border: 1px solid var(--border);
    padding: 10px 16px; border-radius: var(--radius);
    font-size: 13px; z-index: 999;
    opacity: 0; transform: translateY(10px);
    transition: all .3s ease; pointer-events: none;
  }}
  .toast.show {{ opacity: 1; transform: translateY(0); }}
  .toast.ok {{ border-color: var(--green); }}
  .toast.err {{ border-color: var(--red); }}

  @media (max-width: 600px) {{
    .grid {{ grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }}
    .header {{ flex-direction: column; align-items: stretch; }}
    .stats {{ font-size: 12px; }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>📸 Unfollow Tool</h1>
  <div class="stats">
    <span class="stat">Total <b id="stat-total">{total}</b></span>
    <span class="stat">Keep <b id="stat-keep">0</b></span>
    <span class="stat">Unfollow <b id="stat-unfollow">0</b></span>
    <span class="stat">Deleted <b id="stat-deleted">0</b></span>
    <span class="stat">Private <b id="stat-private">0</b></span>
    <span class="stat">Pending <b id="stat-pending">0</b></span>
    <span class="stat">Sin revisar <b id="stat-unseen">0</b></span>
  </div>
  <span class="sync-badge" id="sync-badge">⏳ Iniciando...</span>
</div>

<div class="controls">
  <button class="active" data-filter="all" onclick="setFilter('all')">Todos</button>
  <button class="keep" data-filter="keep" onclick="setFilter('keep')">Mantener</button>
  <button class="unfollow" data-filter="unfollow" onclick="setFilter('unfollow')">Unfollow</button>
  <button class="deleted" data-filter="deleted" onclick="setFilter('deleted')">Eliminado</button>
  <button class="private" data-filter="private" onclick="setFilter('private')">Privado</button>
  <button class="pending" data-filter="pending" onclick="setFilter('pending')">Pending</button>
  <span style="flex:1"></span>
  <button onclick="exportTxt()">📥 Export .txt</button>
  <button onclick="resetStates()">🔄 Reset local</button>
</div>

<div class="year-chips" id="year-chips"></div>

<div class="session-bar">
  <span>Modo sesión:</span>
  <input type="number" id="session-count" value="50" min="1" max="200">
  <button onclick="loadSession()">Cargar siguientes sin revisar</button>
  <span id="session-info" style="margin-left:auto"></span>
</div>

<div class="grid" id="grid"></div>

<div class="toast" id="toast"></div>

<script>
// ─── Datos embebidos ──────────────────────────────────────────────
const USERS = {users_json};
const FOLLOWERS = new Set({followers_json});
const YEARS = {years_json};

// ─── Config Supabase ──────────────────────────────────────────────{supabase_code}
const STORAGE_KEY = 'igc_v2_states';
let supabase = null;
if (typeof SUPABASE_URL !== 'undefined') {{
  supabase = supabaseJs.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
}}

// ─── Estado ────────────────────────────────────────────────────────
let states = {{}};
let filterState = 'all';
let filterYear = null;
let currentFiltered = [];

// ─── Toast ─────────────────────────────────────────────────────────
let toastTimer = null;
function showToast(msg, type='ok') {{
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast ' + type + ' show';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2500);
}}

// ─── Sync badge ────────────────────────────────────────────────────
function setSyncBadge(state, text) {{
  const el = document.getElementById('sync-badge');
  el.className = 'sync-badge ' + state;
  el.textContent = text;
}}

// ─── Cargar estados (localStorage + Supabase) ─────────────────────
async function loadStates() {{
  // 1. Local primero (instántaneo)
  try {{
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) states = JSON.parse(raw);
  }} catch(e) {{}}

  // 2. Supabase remoto
  if (!supabase) {{
    setSyncBadge('err', '🔴 Sin Supabase');
    render();
    updateStats();
    return;
  }}

  setSyncBadge('syncing', '🔄 Sincronizando...');
  try {{
    const {{ data, error }} = await supabase
      .from('states')
      .select('username, state, updated_at');

    if (error) throw error;

    // Merge: si tenemos updated_at, el más reciente gana
    let merged = {{ ...states }};
    const now = Date.now();
    for (const row of data) {{
      const remoteTs = row.updated_at ? new Date(row.updated_at).getTime() : 0;
      const localState = merged[row.username];
      // Buscar timestamp local (si no existe, local pierde)
      const localTs = (localState && states['__ts__']?.[row.username]) || 0;

      if (remoteTs >= localTs) {{
        merged[row.username] = row.state;
      }}
    }}

    states = merged;
    // Persistir merge en localStorage
    localStorage.setItem(STORAGE_KEY, JSON.stringify(states));
    setSyncBadge('ok', '🟢 Sincronizado');
  }} catch (e) {{
    console.warn('Supabase sync error:', e);
    setSyncBadge('err', '🔴 Error de sync (usando local)');
  }}

  render();
  updateStats();
}}

// ─── Guardar estado ────────────────────────────────────────────────
async function saveState(username, newState) {{
  // Local inmediato
  states[username] = newState;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(states));
  updateStats();
  render();

  // Supabase async
  if (!supabase) return;
  try {{
    const {{ error }} = await supabase
      .from('states')
      .upsert({{
        username,
        state: newState,
        updated_at: new Date().toISOString(),
      }}, {{ onConflict: 'username' }});

    if (error) throw error;
  }} catch (e) {{
    console.warn('Supabase save error:', e);
    showToast('Error al guardar en la nube', 'err');
  }}
}}

// ─── Render ────────────────────────────────────────────────────────
function render() {{
  const grid = document.getElementById('grid');
  grid.innerHTML = '';

  let list = USERS;

  // Filtro por año
  if (filterYear) {{
    list = list.filter(u => {{
      const d = new Date(u.t * 1000);
      return d.getUTCFullYear() === filterYear;
    }});
  }}

  // Filtro por estado
  if (filterState !== 'all') {{
    list = list.filter(u => states[u.u] === filterState);
  }}

  currentFiltered = list;

  // Session mode: si estamos en filtro "all" y hay session activa
  // se maneja aparte (ver loadSession)

  let htmlFragments = [];
  for (const u of list) {{
    const state = states[u.u] || '';
    const isNfb = !FOLLOWERS.has(u.u.toLowerCase());
    const date = new Date(u.t * 1000);
    const dateStr = date.toLocaleDateString('es-AR', {{ year:'numeric', month:'short', day:'numeric' }});
    const year = date.getUTCFullYear();
    const initial = u.u.charAt(0).toUpperCase();

    htmlFragments.push(`<div class="card" data-user="${{u.u}}">
      <div style="display:flex;align-items:center;gap:8px">
        <div class="avatar">${{initial}}</div>
        <div style="flex:1;min-width:0">
          <div class="uname"><a href="${{htmlEncode(u.h)}}" target="_blank">@${{htmlEncode(u.u)}}</a></div>
          <div class="meta">${{dateStr}} · ${{year}}</div>
        </div>
      </div>
      ${{isNfb ? '<div class="badge nfb">No te sigue</div>' : ''}}
      <div class="actions">
        <button class="s-keep ${{state === 'keep' ? 'active' : ''}}" onclick="saveState('${{escapeJs(u.u)}}','keep')">K</button>
        <button class="s-unfollow ${{state === 'unfollow' ? 'active' : ''}}" onclick="saveState('${{escapeJs(u.u)}}','unfollow')">U</button>
        <button class="s-deleted ${{state === 'deleted' ? 'active' : ''}}" onclick="saveState('${{escapeJs(u.u)}}','deleted')">D</button>
        <button class="s-private ${{state === 'private' ? 'active' : ''}}" onclick="saveState('${{escapeJs(u.u)}}','private')">P</button>
        <button class="s-pending ${{state === 'pending' ? 'active' : ''}}" onclick="saveState('${{escapeJs(u.u)}}','pending')">?</button>
      </div>
    </div>`);
  }}

  grid.innerHTML = htmlFragments.join('');
}}

function htmlEncode(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

function escapeJs(s) {{
  return String(s).replace(/\\\\/g,'\\\\\\\\').replace(/'/g,"\\\\'").replace(/"/g,'\\\\"');
}}

// ─── Filtros ───────────────────────────────────────────────────────
function setFilter(state) {{
  filterState = state;
  document.querySelectorAll('.controls button[data-filter]').forEach(b => {{
    b.classList.toggle('active', b.dataset.filter === state);
  }});
  render();
  updateStats();
}}

function setYear(year) {{
  filterYear = filterYear === year ? null : year;
  document.querySelectorAll('.year-chips button').forEach(b => {{
    b.classList.toggle('active', parseInt(b.dataset.year) === filterYear);
  }});
  render();
  updateStats();
}}

// ─── Años chips ────────────────────────────────────────────────────
function renderYearChips() {{
  const container = document.getElementById('year-chips');
  container.innerHTML = YEARS.map(y =>
    `<button data-year="${{y}}" onclick="setYear(${{y}})" class="${{filterYear === y ? 'active' : ''}}">${{y}}</button>`
  ).join('');
}}

// ─── Stats ─────────────────────────────────────────────────────────
function updateStats() {{
  const counts = {{ keep:0, unfollow:0, deleted:0, private:0, pending:0 }};
  for (const s of Object.values(states)) {{
    if (counts[s] !== undefined) counts[s]++;
  }}
  const unseen = USERS.length - Object.keys(states).length;
  document.getElementById('stat-keep').textContent = counts.keep;
  document.getElementById('stat-unfollow').textContent = counts.unfollow;
  document.getElementById('stat-deleted').textContent = counts.deleted;
  document.getElementById('stat-private').textContent = counts.private;
  document.getElementById('stat-pending').textContent = counts.pending;
  document.getElementById('stat-unseen').textContent = unseen;
}}

// ─── Modo sesión ───────────────────────────────────────────────────
function loadSession() {{
  const count = parseInt(document.getElementById('session-count').value) || 50;
  // Encontrar los N usuarios más antiguos sin revisar
  const unseen = USERS
    .filter(u => !states[u.u])
    .sort((a, b) => a.t - b.t)
    .slice(0, count);

  // Resetear filtros
  setFilter('all');
  filterYear = null;
  document.querySelectorAll('.year-chips button').forEach(b => b.classList.remove('active'));

  // Mostrar solo estos
  currentFiltered = unseen;
  const grid = document.getElementById('grid');
  let htmlFragments = [];
  for (const u of unseen) {{
    const isNfb = !FOLLOWERS.has(u.u.toLowerCase());
    const date = new Date(u.t * 1000);
    const dateStr = date.toLocaleDateString('es-AR', {{ year:'numeric', month:'short', day:'numeric' }});
    const year = date.getUTCFullYear();
    const initial = u.u.charAt(0).toUpperCase();
    const state = states[u.u] || '';

    htmlFragments.push(`<div class="card" data-user="${{u.u}}">
      <div style="display:flex;align-items:center;gap:8px">
        <div class="avatar">${{initial}}</div>
        <div style="flex:1;min-width:0">
          <div class="uname"><a href="${{htmlEncode(u.h)}}" target="_blank">@${{htmlEncode(u.u)}}</a></div>
          <div class="meta">${{dateStr}} · ${{year}}</div>
        </div>
      </div>
      ${{isNfb ? '<div class="badge nfb">No te sigue</div>' : ''}}
      <div class="actions">
        <button class="s-keep ${{state === 'keep' ? 'active' : ''}}" onclick="saveState('${{escapeJs(u.u)}}','keep')">K</button>
        <button class="s-unfollow ${{state === 'unfollow' ? 'active' : ''}}" onclick="saveState('${{escapeJs(u.u)}}','unfollow')">U</button>
        <button class="s-deleted ${{state === 'deleted' ? 'active' : ''}}" onclick="saveState('${{escapeJs(u.u)}}','deleted')">D</button>
        <button class="s-private ${{state === 'private' ? 'active' : ''}}" onclick="saveState('${{escapeJs(u.u)}}','private')">P</button>
        <button class="s-pending ${{state === 'pending' ? 'active' : ''}}" onclick="saveState('${{escapeJs(u.u)}}','pending')">?</button>
      </div>
    </div>`);
  }}

  grid.innerHTML = htmlFragments.join('');
  document.getElementById('session-info').textContent =
    `Mostrando ${{unseen.length}} cuentas sin revisar (más antiguas)`;
  updateStats();
}}

// ─── Export ────────────────────────────────────────────────────────
function exportTxt() {{
  const categories = ['unfollow', 'keep', 'deleted', 'private', 'pending'];
  for (const cat of categories) {{
    const list = USERS.filter(u => states[u.u] === cat).map(u => u.u);
    if (list.length === 0) continue;
    const blob = new Blob([list.join('\\n')], {{ type: 'text/plain' }});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${{cat}}_${{list.length}}.txt`;
    a.click();
  }}
  showToast(`Exportados ${{categories.length}} archivos`);
}}

// ─── Reset local ───────────────────────────────────────────────────
function resetStates() {{
  if (!confirm('¿Resetear TODOS los estados locales? (no afecta Supabase)')) return;
  states = {{}};
  localStorage.removeItem(STORAGE_KEY);
  render();
  updateStats();
  showToast('Estados locales reseteados');
}}

// ─── Init ──────────────────────────────────────────────────────────
renderYearChips();
updateStats();
loadStates();
</script>
</body>
</html>"""

    return html


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Genera index.html para Instagram Unfollow Tool")
    parser.add_argument("--supabase-url", help="Supabase Project URL")
    parser.add_argument("--supabase-key", help="Supabase anon public key")
    args = parser.parse_args()

    print("📖 Leyendo following.json...")
    users = read_following()
    print(f"   → {len(users)} usuarios seguidos")

    print("📖 Leyendo followers_1.json...")
    followers = read_followers()
    print(f"   → {len(followers)} seguidores")

    print("🏗️  Generando index.html...")
    html = build_html(users, followers, args.supabase_url or "", args.supabase_key or "")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    file_size = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"✅ index.html generado ({file_size:.0f} KB)")

    if not args.supabase_url:
        print()
        print("⚠️  No configuraste Supabase. El HTML funciona con localStorage local.")
        print("   Para activar sync multi-equipo:")
        print("   1. Creá un proyecto en https://supabase.com")
        print("   2. Ejecutá el SQL de setup (está en el README o en el análisis)")
        print("   3. Corré: python build.py --supabase-url 'https://tuproyecto.supabase.co' --supabase-key 'tu-anon-key'")
        print()
        print("   También podés editar SUPABASE_URL y SUPABASE_ANON_KEY directamente en index.html.")

    print("🎯 Abrí index.html en tu navegador y listo.")


if __name__ == "__main__":
    main()
