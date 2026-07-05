#!/usr/bin/env python3
"""ISATIS — Taktische Live-Lagekarte Generator.
Eingabe: Anlass, Ort, Thema → Ausgabe: komplettes Dashboard auf GitHub Pages."""

import json, os, sys, subprocess, urllib.request, urllib.parse, time

TEMPLATE_HTML = r'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="300">
<title>{{TITEL}}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0c0f;font-family:'Share Tech Mono',monospace;overflow:hidden;height:100vh;width:100vw}
#map{width:100%;height:100%;z-index:1}
.hud{position:fixed;top:0;left:0;right:clamp(220px,20vw,300px);z-index:1001;pointer-events:none}
.hud-top{display:flex;justify-content:space-between;align-items:center;padding:4px 10px;background:rgba(10,12,15,0.94)}
.hud-title{font-size:12px;font-weight:700;color:#ff4444;letter-spacing:2px;text-shadow:0 0 6px rgba(0,0,0,0.8)}
.hud-title .sub{font-size:8px;color:#ff8888;margin-left:6px}
.hud-badge{font-size:9px;color:#ffaa00;display:flex;gap:10px;text-shadow:0 0 4px rgba(0,0,0,0.8)}
.hud-badge span{font-size:13px;font-weight:700;color:#ff4444;margin-left:2px}
.sidebar{position:fixed!important;top:clamp(28px,3vh,36px)!important;right:0!important;left:auto!important;bottom:0!important;width:clamp(220px,20vw,300px)!important;height:auto!important;z-index:1000;background:rgba(10,12,15,0.94);border-left:1px solid rgba(255,68,68,0.2);overflow:hidden;padding:clamp(8px,1vw,12px);font-size:clamp(11px,1.2vw,15px);color:#bbb;display:flex;flex-direction:column;transform:none!important;will-change:auto;pointer-events:auto}
.sidebar h3{font-size:clamp(11px,1.3vw,15px);color:#ff4444;letter-spacing:1px;text-transform:uppercase;margin:clamp(5px,0.6vw,10px) 0 clamp(3px,0.4vw,5px);padding-bottom:clamp(2px,0.2vw,4px);border-bottom:1px solid rgba(255,68,68,0.15);flex-shrink:0}
.sidebar h3:first-child{margin-top:0}
.sidebar label{display:flex;align-items:center;gap:clamp(5px,0.6vw,10px);padding:clamp(2px,0.3vw,4px) 0;cursor:pointer;color:#bbb;font-size:clamp(11px,1.2vw,15px);flex-shrink:0}
.sidebar label:hover{color:#fff}
.sidebar .layer-btn{display:inline-block;padding:clamp(4px,0.5vw,7px) clamp(8px,1vw,14px);margin:clamp(1px,0.15vw,3px);background:rgba(255,68,68,0.08);border:1px solid rgba(255,68,68,0.2);border-radius:3px;color:#bbb;font:clamp(10px,1.1vw,14px) 'Share Tech Mono',monospace;cursor:pointer;letter-spacing:1px}
.sidebar .layer-btn.active{background:rgba(255,68,68,0.2);border-color:#ff4444;color:#ff4444}
.sidebar .layer-btn:hover{background:rgba(255,68,68,0.15);color:#fff}
.sidebar button{display:block;width:100%;margin:clamp(2px,0.2vw,3px) 0;padding:clamp(4px,0.5vw,7px) clamp(8px,1vw,14px);background:rgba(255,68,68,0.08);border:1px solid rgba(255,68,68,0.2);border-radius:3px;color:#ff8888;font:clamp(10px,1.1vw,14px) 'Share Tech Mono',monospace;cursor:pointer;letter-spacing:1px;text-align:left;flex-shrink:0}
.sidebar button:hover{background:rgba(255,68,68,0.2);color:#fff}
.sidebar .leg-row{display:flex;align-items:center;gap:clamp(4px,0.5vw,8px);margin:clamp(1px,0.2vw,3px) 0;font-size:clamp(10px,1.1vw,14px);color:#bbb;flex-shrink:0}
.sidebar .tac-sym{font-size:clamp(12px,1.4vw,18px);flex-shrink:0;width:clamp(14px,1.6vw,20px);text-align:center}
.marker-cluster{background-clip:padding-box;border-radius:50%}
.marker-cluster-small{background-color:rgba(10,12,15,0.9)}
.marker-cluster-medium{background-color:rgba(10,12,15,0.92)}
.marker-cluster-large{background-color:rgba(10,12,15,0.94)}
.leaflet-cluster-spider-leg{stroke:#ff4444!important;stroke-opacity:0.6!important}
.leaflet-popup-content-wrapper{background:rgba(10,12,15,0.96)!important;border:1px solid rgba(255,68,68,0.3)!important;border-radius:2px!important;color:#fff!important;font-family:'Share Tech Mono',monospace!important}
.leaflet-popup-content{margin:6px 10px!important;line-height:1.4!important}
.leaflet-popup-tip{background:rgba(10,12,15,0.96)!important}
.leaflet-popup-close-button{color:#f44!important;font-size:16px!important}
.pup-title{font-size:clamp(12px,1.3vw,16px);font-weight:700;color:#ff4444;letter-spacing:1px;margin-bottom:3px}
.pup-note{font-size:clamp(10px,1.1vw,14px);color:#ccc;line-height:1.4}
.pup-tn{display:inline-block;background:rgba(255,68,68,0.15);border:1px solid rgba(255,68,68,0.3);color:#ff4444;padding:1px 6px;border-radius:2px;font-size:clamp(10px,1.1vw,14px);font-weight:700;margin-top:3px}
.fs-btn{position:fixed;bottom:6px;left:6px;z-index:1000;background:rgba(10,12,15,0.85);border:1px solid rgba(255,68,68,0.2);color:#ff4444;padding:3px 6px;font:8px 'Share Tech Mono',monospace;cursor:pointer;border-radius:2px}
.fs-btn:hover{background:rgba(255,68,68,0.15)}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(255,68,68,0.3);border-radius:2px}
</style>
</head>
<body>
<div class="hud"><div class="hud-top">
<div class="hud-title">{{TITEL}}<span class="sub">{{HASHTAG}} ▪ <span id="zeit">—</span></span></div>
<div class="hud-badge">BLOCKADEN <span id="n-block">—</span> | EVENTS <span id="n-events">—</span></div>
</div></div>
<div id="map"></div>
<button class="fs-btn" onclick="document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen()">⛶</button>
<div class="sidebar">
<h3>🗺 KARTE</h3>
<div style="display:flex;gap:2px">
<span class="layer-btn active" onclick="switchLayer('topo',this)">Topo</span>
<span class="layer-btn" onclick="switchLayer('sat',this)">Sat</span>
<span class="layer-btn" onclick="switchLayer('hybrid',this)">Hybrid</span>
</div>
<h3>👁 OVERLAYS</h3>
<label><input type="checkbox" checked onchange="toggleOverlay('blockaden',this.checked)"> ◆ Blockaden</label>
<label><input type="checkbox" checked onchange="toggleOverlay('events',this.checked)"> ▲ Events</label>
<label><input type="checkbox" checked onchange="toggleOverlay('abschnitte',this.checked)"> ━ Sperrungen</label>
<h3>🎨 LEGENDE</h3>
<div class="leg-row"><span class="tac-sym" style="color:#ff6644">◆</span> Blockade ≥500</div>
<div class="leg-row"><span class="tac-sym" style="color:#ff4444">●</span> Blockade &lt;500</div>
<div class="leg-row"><span class="tac-sym" style="color:#ffaa00">■</span> Sitzblockade</div>
<div class="leg-row"><span class="tac-sym" style="color:#ff0000">▲</span> Abseilaktion</div>
<div class="leg-row"><span class="tac-sym" style="color:#f44">⊘</span> Abgeriegelt</div>
<div class="leg-row"><div class="leg-line" style="width:16px;height:3px;background:#1a1a2e;border-radius:1px"></div> Strasse gesperrt</div>
<div class="leg-row"><div class="leg-line" style="width:16px;height:3px;background:#00cc44;border-radius:1px"></div> Strasse frei</div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const map = L.map('map', { center:{{CENTER}}, zoom:13, zoomControl:false, attributionControl:false });
const topoLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19});
const satLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19});
const hybridLabels = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,opacity:0.45});
topoLayer.addTo(map);
L.control.zoom({position:'bottomright'}).addTo(map);
for(let la={{BOUNDS_S}};la<={{BOUNDS_N}};la+=0.02) L.polyline([[la,{{BOUNDS_W}}],[la,{{BOUNDS_E}}]],{color:'#fff',weight:.5,opacity:.02}).addTo(map);
for(let lo={{BOUNDS_W}};lo<={{BOUNDS_E}};lo+=0.02) L.polyline([[{{BOUNDS_S}},lo],[{{BOUNDS_N}},lo]],{color:'#fff',weight:.5,opacity:.02}).addTo(map);
function switchLayer(v,btn){
  map.removeLayer(topoLayer);map.removeLayer(satLayer);map.removeLayer(hybridLabels);
  if(v==='topo')topoLayer.addTo(map);
  else if(v==='sat')satLayer.addTo(map);
  else{satLayer.addTo(map);hybridLabels.addTo(map);}
  document.querySelectorAll('.layer-btn').forEach(b=>b.classList.remove('active'));
  if(btn)btn.classList.add('active');
}
function makeIcons(z){const s=Math.max(0.4,1+(z-13)*0.12),px=v=>Math.round(v*s);return{
 gross:L.divIcon({html:'<div style="width:'+px(20)+'px;height:'+px(20)+'px;background:#ff6644;border-radius:50%;box-shadow:0 0 '+px(14)+'px #ff6644,0 0 '+px(28)+'px #ff664433;border:'+px(2)+'px solid #ff664488;animation:pulse 2s infinite"></div><style>@keyframes pulse{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.3);opacity:0.7}}</style>',iconSize:[px(20),px(20)],iconAnchor:[px(10),px(10)]}),
 normal:L.divIcon({html:'<div style="width:'+px(14)+'px;height:'+px(14)+'px;background:#ff4444;border-radius:50%;box-shadow:0 0 '+px(8)+'px #ff4444,0 0 '+px(16)+'px #ff444422;border:'+px(2)+'px solid #ff444488"></div>',iconSize:[px(14),px(14)],iconAnchor:[px(7),px(7)]}),
 sitz:L.divIcon({html:'<div style="width:'+px(16)+'px;height:'+px(16)+'px;background:#ffaa00;border-radius:3px;transform:rotate(45deg);box-shadow:0 0 '+px(10)+'px #ffaa00,0 0 '+px(20)+'px #ffaa0033;border:'+px(2)+'px solid #ffaa0088"></div>',iconSize:[px(16),px(16)],iconAnchor:[px(8),px(8)]}),
 barrikade:L.divIcon({html:'<div style="width:'+px(14)+'px;height:'+px(14)+'px;background:rgba(255,68,68,.15);border:'+px(2)+'px solid red;box-shadow:0 0 '+px(8)+'px rgba(255,0,0,.4);display:flex;align-items:center;justify-content:center;font-size:'+px(10)+'px;color:red;font-weight:bold">⊘</div>',iconSize:[px(14),px(14)],iconAnchor:[px(7),px(7)]}),
 abseil:L.divIcon({html:'<div style="width:0;height:0;border-left:'+px(8)+'px solid transparent;border-right:'+px(8)+'px solid transparent;border-bottom:'+px(14)+'px solid red;filter:drop-shadow(0 0 '+px(8)+'px red);animation:ab 1s infinite"></div><style>@keyframes ab{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}</style>',iconSize:[px(16),px(16)],iconAnchor:[px(8),px(10)]}),
};}
let ico=makeIcons(13);
let clusterGroup=L.markerClusterGroup({chunkedLoading:true,maxClusterRadius:30,spiderfyOnMaxZoom:true,showCoverageOnHover:false,zoomToBoundsOnClick:true,disableClusteringAtZoom:14,
 iconCreateFunction:function(c){const n=c.getChildCount();let cl='marker-cluster-small',bg='#00ff88',tc='#0a0c0f';if(n>=10){cl='marker-cluster-large';bg='#ff4444';tc='#fff'}else if(n>=5){cl='marker-cluster-medium';bg='#ff6644';tc='#0a0c0f'}
 const z=map.getZoom(),s=Math.max(0.4,1+(z-13)*0.1),sz=Math.round(20*s),isz=Math.round(14*s),fs=Math.round(7*s);
 return L.divIcon({html:'<div style="width:'+isz+'px;height:'+isz+'px;margin:'+Math.round(2*s)+'px;font:700 '+fs+'px Share Tech Mono;background:'+bg+';color:'+tc+';border-radius:2px;display:flex;align-items:center;justify-content:center"><span>'+n+'</span></div>',className:cl,iconSize:L.point(sz,sz)});}
});
map.addLayer(clusterGroup);
let abschnittGroup=L.layerGroup().addTo(map);
let eventGroup=L.layerGroup().addTo(map);
function toggleOverlay(type,on){
 if(type==='blockaden')on?map.addLayer(clusterGroup):map.removeLayer(clusterGroup);
 if(type==='events')on?map.addLayer(eventGroup):map.removeLayer(eventGroup);
 if(type==='abschnitte')on?map.addLayer(abschnittGroup):map.removeLayer(abschnittGroup);
}
function render(d){
 const t=new Date(d.stand);const ts=t.toLocaleTimeString('de-DE',{hour:'2-digit',minute:'2-digit'});
 document.getElementById('zeit').textContent=t.toLocaleDateString('de-DE')+' '+ts;
 document.getElementById('n-block').textContent=d.blockaden.length;
 document.getElementById('n-events').textContent=(d.events||[]).length;
 eventGroup.clearLayers();
 (d.events||[]).forEach(ev=>{
  if(ev.typ==='abseil'){
   L.marker([ev.lat,ev.lon],{icon:ico.abseil}).bindPopup('<div class="pup-title">'+ev.name+'</div><div class="pup-note">'+ev.note+'</div><span class="pup-tn" style="background:rgba(255,0,0,.2);border-color:rgba(255,0,0,.5);color:#f00">KRITISCH</span>').addTo(eventGroup);
   L.circle([ev.lat,ev.lon],{radius:1200,color:'#f00',weight:1.5,opacity:.35,fillOpacity:.03,dashArray:'6 4'}).addTo(eventGroup);
  }else{
   L.circleMarker([ev.lat,ev.lon],{radius:6,color:'#ff6644',fillColor:'#ff6644',fillOpacity:.5,weight:1.5}).bindPopup('<div class="pup-title">'+ev.name+'</div><div class="pup-note">'+ev.note+'</div>').addTo(eventGroup);
  }
 });
 abschnittGroup.clearLayers();
 d.strassen_abschnitte.forEach(sa=>{
  L.polyline(sa.route,{color:sa.farbe||'#000',weight:8,opacity:0.85}).bindPopup('<div class="pup-title">'+sa.name+'</div><div class="pup-note">'+sa.note+'</div>').addTo(abschnittGroup);
 });
 clusterGroup.clearLayers();
 d.blockaden.forEach(b=>{
  const tn=typeof b.tn==='number'?b.tn.toLocaleString('de-DE'):b.tn;
  let tags='';
  if(b.typ==='sitz')tags+='<span class="pup-tag" style="background:rgba(255,170,0,.15);border:1px solid rgba(255,170,0,.4);color:#fa0">SITZ</span>';
  L.marker([b.lat,b.lon],{icon:ico[b.typ]||ico.normal}).bindPopup('<div class="pup-title">'+b.name+'</div><div class="pup-note">'+b.note+'</div><span class="pup-tn">▲ '+tn+' TN</span>'+tags).addTo(clusterGroup);
 });
}
let currentData=null;
async function load(){
 try{
  const resp=await fetch('{{DATA_URL}}?t='+Date.now());
  if(!resp.ok)throw new Error('HTTP '+resp.status);
  currentData=await resp.json();render(currentData);
 }catch(e){console.error(e)}
}
load();setInterval(load,300000);
map.on('zoomend',()=>{ico=makeIcons(map.getZoom());if(currentData)render(currentData);});
</script>
</body>
</html>'''


def geocode(place, delay=1.2):
    """Geocode a place via OSM Nominatim."""
    try:
        time.sleep(delay)
        q = urllib.parse.quote(place)
        url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'ISATIS/1.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        if data:
            return round(float(data[0]['lat']), 5), round(float(data[0]['lon']), 5)
    except Exception as e:
        print(f"  ⚠ Geocoding failed for '{place}': {e}")
    return None


def generate(event, location, hashtag, github_org, repo_name):
    """
    Generate a complete live map dashboard.

    Args:
        event: Event name, e.g. "AfD-Bundesparteitag Erfurt"
        location: City/region, e.g. "Erfurt, Thüringen"
        hashtag: e.g. "#EF0407"
        github_org: GitHub org/user, e.g. "DeltaGeek-DE"
        repo_name: e.g. "erfurt-lage"
    """
    print(f"🗺 ISATIS — Live-Lagekarte Generator")
    print(f"   Event: {event}")
    print(f"   Ort: {location}")
    print(f"   Hashtag: {hashtag}")
    print()

    # 1. Geocode location
    print("📍 Geokodiere Zentrum...")
    center = geocode(location)
    if not center:
        print("❌ Konnte Ort nicht geokodieren.")
        return 1
    lat, lon = center
    print(f"   → {lat}, {lon}")

    # 2. Create project directory
    proj_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), repo_name)
    if not os.path.exists(proj_dir):
        os.makedirs(proj_dir)
    print(f"📁 Projektverzeichnis: {proj_dir}")

    # 3. Generate coordinates.json
    coords = {
        location.split(',')[0].strip().lower(): [lat, lon],
        "messegelände": [lat, lon],
        "innenstadt": [lat, lon],
        "zentrum": [lat, lon],
    }
    with open(os.path.join(proj_dir, 'coordinates.json'), 'w', encoding='utf-8') as f:
        json.dump(coords, f, ensure_ascii=False, indent=2)
    print(f"📍 coordinates.json: {len(coords)} Orte")

    # 4. Generate blockaden-data.json
    data = {
        "stand": time.strftime("%Y-%m-%dT%H:%M:%S+02:00"),
        "blockaden": [],
        "strassen_abschnitte": [],
        "events": [],
        "lage_gesamt": f"Lagekarte initialisiert. Warte auf erste Meldungen.",
        "messe": {"lat": lat, "lon": lon, "status": "Noch keine Daten."}
    }
    with open(os.path.join(proj_dir, 'blockaden-data.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"📊 blockaden-data.json initialisiert")

    # 5. Generate HTML
    bounds_s = round(lat - 0.08, 2)
    bounds_n = round(lat + 0.07, 2)
    bounds_w = round(lon - 0.12, 2)
    bounds_e = round(lon + 0.12, 2)
    data_url = f"https://{github_org.lower()}.github.io/{repo_name}/blockaden-data.json"

    html = TEMPLATE_HTML.replace('{{TITEL}}', f"LAGE {location.upper().split(',')[0]}").replace(
        '{{HASHTAG}}', hashtag).replace(
        '{{CENTER}}', f"[{lat},{lon}]").replace(
        '{{DATA_URL}}', data_url).replace(
        '{{BOUNDS_S}}', str(bounds_s)).replace(
        '{{BOUNDS_N}}', str(bounds_n)).replace(
        '{{BOUNDS_W}}', str(bounds_w)).replace(
        '{{BOUNDS_E}}', str(bounds_e))

    with open(os.path.join(proj_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"🌐 index.html generiert ({bounds_s}-{bounds_n}, {bounds_w}-{bounds_e})")

    # 6. Generate fix_coords.py
    fix_py = '''"""fix_coords.py — Erzwingt Koordinaten aus coordinates.json."""
import json
COORDS_FILE = 'coordinates.json'
DATA_FILE = 'blockaden-data.json'
with open(COORDS_FILE, 'r', encoding='utf-8') as f:
    TRUTH = json.load(f)
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    js = json.load(f)
fixed = 0

def force(item):
    global fixed
    name = item.get('name', '').lower()
    for key, coord in TRUTH.items():
        for word in key.lower().replace(', '+location.split(',')[0].strip().lower(), '').replace(' '+location.split(',')[0].strip().lower(), '').split():
            if word in name and [item['lat'], item['lon']] != coord:
                item['lat'], item['lon'] = coord[0], coord[1]
                fixed += 1
                return

for name in ['blockaden', 'events']:
    for item in js.get(name, []):
        force(item)

if fixed:
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(js, f, ensure_ascii=False, indent=2)
    print(f"{fixed} Koordinaten korrigiert.")
else:
    print("Alle Koordinaten OK.")
'''
    with open(os.path.join(proj_dir, 'fix_coords.py'), 'w', encoding='utf-8') as f:
        f.write(fix_py)
    print("🩺 fix_coords.py generiert")

    # 7. Generate GitHub Actions workflow
    actions_dir = os.path.join(proj_dir, '.github', 'workflows')
    os.makedirs(actions_dir, exist_ok=True)
    workflow = f'''name: Deploy to Pages
on:
  push:
    branches: [master]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: true
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{{{ steps.deploy.outputs.page_url }}}}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: .
      - id: deploy
        uses: actions/deploy-pages@v4
'''
    with open(os.path.join(actions_dir, 'pages.yml'), 'w') as f:
        f.write(workflow)
    print("⚙ GitHub Actions Workflow generiert")

    # 8. Init git, create repo, push
    print("\n🚀 Erstelle GitHub Repository...")
    subprocess.run(['git', 'init'], cwd=proj_dir, check=False)
    subprocess.run(['git', 'add', '.'], cwd=proj_dir, check=False)
    subprocess.run(['git', 'commit', '-m', f'ISATIS: {event} — initial'], cwd=proj_dir, check=False)

    result = subprocess.run(
        ['gh', 'repo', 'create', f'{github_org}/{repo_name}', '--public',
         '--description', f'Live-Lagekarte {event} {hashtag}',
         '--source', '.', '--remote', 'origin', '--push'],
        cwd=proj_dir, capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        print("⚠ Repo might already exist. Try pushing manually.")

    # 9. Enable GitHub Pages
    print("🌐 Aktiviere GitHub Pages...")
    subprocess.run([
        'gh', 'api', f'repos/{github_org}/{repo_name}/pages',
        '--method', 'PUT', '-F', 'build_type=workflow',
    ], capture_output=True)

    public_url = f"https://{github_org.lower()}.github.io/{repo_name}/"
    data_url = public_url + 'blockaden-data.json'

    print(f"""
╔══════════════════════════════════════════╗
║ ✅ ISATIS Dashboard bereit!              ║
╠══════════════════════════════════════════╣
║ 🗺 Karte: {public_url}
║ 📊 Daten: {data_url}
║ 📁 Projekt: {proj_dir}
╠══════════════════════════════════════════╣
║ Nächste Schritte:                        ║
║ 1. Warte auf Pages-Deploy (~60s)         ║
║ 2. Erstelle Cronjob mit Hermes:          ║
║    cronjob create */5 * * * *            ║
║ 3. Geokodiere weitere Orte:              ║
║    python geocode_all.py                 ║
╚══════════════════════════════════════════╝
    """)

    return 0


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("ISATIS — Live-Lagekarte Generator")
        print(f"Usage: python {sys.argv[0]} <EVENT> <ORT> <HASHTAG> [GITHUB_ORG] [REPO_NAME]")
        print(f"Example: python {sys.argv[0]} 'AfD-Parteitag' 'Erfurt' '#EF0407' DeltaGeek-DE erfurt-lage")
        sys.exit(1)

    event = sys.argv[1]
    location = sys.argv[2]
    hashtag = sys.argv[3]
    github_org = sys.argv[4] if len(sys.argv) > 4 else 'DeltaGeek-DE'
    repo_name = sys.argv[5] if len(sys.argv) > 5 else hashtag.replace('#', '').lower() + '-lage'

    sys.exit(generate(event, location, hashtag, github_org, repo_name))
