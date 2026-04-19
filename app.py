from flask import Flask, render_template_string, request, jsonify, send_from_directory
import requests, re, urllib3, os
from bs4 import BeautifulSoup

# Отключаем предупреждения о небезопасном SSL-соединении
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# --- CONFIG ---
SERVERS = [{"id": f"s1", "name": f"Server 1", "url": f"https://server1.example.com"},
           {"id": f"s2", "name": f"Server 2", "url": f"https://server2.example.com"},
           {"id": f"s3", "name": f"Server 3", "url": f"https://server3.example.com"},]
LOGIN, PASSWORD, TIMEOUT = "aa", "aabb", 300

HTML = r"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>SysDiag Monitor</title>
    <link rel="icon" href="/favicon.ico" type="image/x-icon">
    <style>
      :root {
        --bg: #0b0d12; --surface: #10131a; --border: #1e2535;
        --accent: #00e5ff; --ok: #00d97e; --danger: #ef4444; --muted: #718096;
        --font: system-ui, -apple-system, sans-serif;
        --mono: ui-monospace, monospace;
      }
      body { background: var(--bg); color: #e2e8f0; font-family: var(--font); margin: 0; display: flex; flex-direction: column; height: 100vh; }
      header { padding: 12px 24px; display: flex; align-items: center; border-bottom: 1px solid var(--border); background: var(--surface); }
      .logo { font-weight: 800; font-size: 18px; }
      .logo span { color: var(--accent); }
      
      .main { display: flex; flex: 1; overflow: hidden; }
      aside { width: 240px; border-right: 1px solid var(--border); display: flex; flex-direction: column; background: var(--surface); }
      .scroll { flex: 1; overflow-y: auto; padding: 15px; }
      .label { font-size: 10px; color: var(--muted); text-transform: uppercase; margin-bottom: 8px; border-bottom: 1px solid var(--border); }

      .srv-item { display: flex; align-items: center; gap: 8px; padding: 6px; cursor: pointer; border-radius: 4px; }
      .srv-item:hover { background: #161b26; }
      .srv-item input { display: none; }
      
      .box { width: 14px; height: 14px; border: 1.5px solid var(--muted); border-radius: 3px; position: relative; flex-shrink: 0; }
      input:checked + .box { background: var(--accent); border-color: var(--accent); }
      input:checked + .box::after { content: '✓'; position: absolute; color: #000; font-size: 10px; top: -1px; left: 2px; font-weight: 900; }

      .srv-info { display: flex; flex-direction: column; font-size: 12px; }
      .srv-ip { font-family: var(--mono); font-size: 10px; color: var(--muted); }

      .actions { padding: 15px; border-top: 1px solid var(--border); display: grid; gap: 6px; }
      button { padding: 8px; border: none; border-radius: 4px; font-weight: 700; font-size: 10px; cursor: pointer; text-transform: uppercase; }
      .content { flex: 1; padding: 20px; overflow-y: auto; }
      .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 15px; }

      .card { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 10px; }
      .card-h { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; font-weight: 800; font-size: 12px; }
      .v-info { color: var(--muted); font-family: var(--mono); font-size: 10px; font-weight: 400; }
      
      .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--muted); }
      .dot.ok { background: var(--ok); box-shadow: 0 0 5px var(--ok); }
      .dot.danger { background: var(--danger); box-shadow: 0 0 5px var(--danger); }
      .dot.loading { opacity: 0.5; animation: p 1s infinite; }

      .row { padding: 4px 8px; font-size: 11px; font-family: var(--mono); border-left: 2px solid transparent; background: #161b26; margin-bottom: 3px; font-weight: 800; }
      .row.ok { border-left-color: var(--ok); }
      .row.danger { border-left-color: var(--danger); }
      .sec-t { font-size: 10px; color: var(--muted); text-transform: uppercase; margin: 8px 0 4px; font-weight: 800; }
      .v-badge { font-weight: 400; }
      @keyframes p { 50% { opacity: 0.2; } }
    </style>
</head>
<body>
<header><div class="logo">INDEX/VERSION<span> MONITOR</span></div><div id="stat" style="margin-left:auto; font-size:12px; color:var(--muted); font-weight:800">Ready</div></header>
<div class="main">
  <aside>
    <div class="scroll" id="srvList"></div>
    <div class="actions">
      <button style="background:#00b4d8" onclick="run('index')">index</button>
      <button style="background:#7c3aed; color:#fff" onclick="run('version')">Versions</button>
      <button style="background:var(--ok)" onclick="run('both')">Check All</button>
      <button style="background:none; border:1px solid var(--border); color:var(--muted)" onclick="toggle()">Invert</button>
    </div>
  </aside>
  <main class="content"><div class="grid" id="grid"></div></main>
</div>
<script>
let servers = [];
async function init() {
  servers = await (await fetch('/api/servers')).json();
  document.getElementById('srvList').innerHTML = '<div class="label">Servers</div>' + servers.map(s => `
    <label class="srv-item">
      <input type="checkbox" name="srv" value="${s.id}" checked><div class="box"></div>
      <div class="srv-info"><b>${s.name}</b><span class="srv-ip">${s.url.split('//')[1]}</span></div>
    </label>`).join('');
}
function toggle() { document.querySelectorAll('input[name="srv"]').forEach(b => b.checked = !b.checked); }

async function run(mode) {
  const ids = [...document.querySelectorAll('input[name="srv"]:checked')].map(b => b.value);
  if(!ids.length) return;
  const grid = document.getElementById('grid'); grid.innerHTML = '';
  document.getElementById('stat').textContent = 'Running...';
  
  ids.forEach(id => {
    const s = servers.find(x => x.id === id);
    const ip = s.url.split('//')[1];
    grid.insertAdjacentHTML('beforeend', `
      <div class="card">
        <div class="card-h">
          <div class="dot loading" id="d-${id}"></div>
          <span>${s.name} <span class="v-info">[${ip}]</span></span>
        </div>
        <div id="b-${id}" style="font-size:11px">Loading...</div>
      </div>`);
  });

  await Promise.all(ids.map(async id => {
    try {
      const res = await (await fetch('/api/check', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({server_id:id, mode})})).json();
      render(id, res);
    } catch { document.getElementById(`b-${id}`).innerHTML = '<div class="row danger">Error</div>'; }
  }));
  document.getElementById('stat').textContent = 'Last: ' + new Date().toLocaleTimeString();
}

function render(id, data) {
  const b = document.getElementById(`b-${id}`), d = document.getElementById(`d-${id}`);
  if (data.error) { b.innerHTML = `<div class="row danger">${data.error}</div>`; d.className = 'dot danger'; return; }
  let h = '', ok = true;

  if (data.index?.services?.length) {
    h += `<div class="sec-t">INDEX</div>`;
    data.index.services.forEach(i => {
      const res = i.status === 'alert-success';
      if(!res) ok = false;
      h += `<div class="row ${res?'ok':'danger'}">${i.name}: ${i.detail}</div>`;
    });
  }

  if (data.version?.services?.length) {
    const curV = data.version.footer_version || '?';
    h += `<div class="sec-t">Vers <span class="v-badge">(${curV})</span></div>`;
    data.version.services.forEach(i => {
      const res = i.version === data.version.footer_version;
      if(!res) ok = false;
      h += `<div class="row ${res?'ok':'danger'}">${i.name}: ${i.version}</div>`;
    });
  }

  b.innerHTML = h || '<div class="row muted">No data</div>'; 
  d.className = 'dot ' + (ok ? 'ok' : 'danger');
}
init();
</script>
</body>
</html>
"""

def parse(soup):
    res = []
    mp = soup.find(id="mainPanel")
    if not mp: return res
    for div in mp.find_all("div", class_="exception-panel"):
        al = div.find("div", class_="alert")
        if not al: continue
        name = al.find("strong").get_text(strip=True) if al.find("strong") else "???"
        res.append({
            "name": name, 
            "detail": al.get_text(separator=" ", strip=True).replace(name, "").strip(" -–"), 
            "status": "alert-success" if "alert-success" in al.get("class", []) else "alert-danger"
        })
    return res

def get_session(url):
    s = requests.Session()
    s.verify = False
    r = s.get(f"{url}/signin", timeout=10)
    tk = BeautifulSoup(r.text, "html.parser").find("input", {"name": "__secretToken"})["value"]
    s.post(f"{url}/signin", data={"__secretToken": tk, "login": LOGIN, "password": PASSWORD}, timeout=10)
    return s

# --- ROUTES ---

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route('/favicon.ico')
def favicon():
    # Отдает файл favicon.ico напрямую из корня проекта
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/api/servers")
def api_srv():
    return jsonify(SERVERS)

@app.route("/api/check", methods=["POST"])
def api_check():
    d = request.json
    srv = next(s for s in SERVERS if s["id"] == d['server_id'])
    try:
        ss = get_session(srv["url"])
        res = {}
        if d['mode'] in ('index', 'both'):
            res['index'] = {"services": parse(BeautifulSoup(ss.get(f"{srv['url']}/index", timeout=TIMEOUT).text, "html.parser"))}
        if d['mode'] in ('version', 'both'):
            soup = BeautifulSoup(ss.get(f"{srv['url']}/version", timeout=TIMEOUT).text, "html.parser")
            f_ver = soup.find(id="footer").find("a").text if (soup.find(id="footer") and soup.find(id="footer").find("a")) else "?"
            res['version'] = {
                "footer_version": f_ver, 
                "services": [
                    {"name": i['name'], "version": (re.search(r"([\d.]+)", i['detail']).group(1) if re.search(r"([\d.]+)", i['detail']) else "?")} 
                    for i in parse(soup)
                ]
            }
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True, port=5000)