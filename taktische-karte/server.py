#!/usr/bin/env python3
"""Taktische Karte — Ein Server für alles: Karte, Admin, Tile-Download, OSINT."""
import http.server, socketserver, os, sys, json, urllib.request, math, time, threading, uuid, re, cgi, io

PORT = 8765
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
DATA_DIR = os.path.join(DIR, 'data')
TILES_DIR = os.path.join(DIR, 'tiles')
OSINT_DIR = os.path.join(DATA_DIR, 'osint')
os.makedirs(TILES_DIR, exist_ok=True)
os.makedirs(OSINT_DIR, exist_ok=True)
os.makedirs(os.path.join(OSINT_DIR, 'media'), exist_ok=True)

tile_state = {'running': False, 'paused': False, 'progress': 0, 'total': 0, 'current': '', 'errors': 0}
osint_state = {'running': False, 'progress': 0, 'step': '', 'result': None}


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def log_message(self, format, *args):
        pass

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _read_body(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            return json.loads(self.rfile.read(length)) if length else {}
        except:
            return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        # JSON data from data/ directory
        if self.path == '/blockaden-data.json' or self.path.startswith('/blockaden-data.json?'):
            src = os.path.join(DATA_DIR, 'blockaden-data.json')
            if not os.path.exists(src):
                empty = {"stand": "", "blockaden": [], "events": [], "strassen_abschnitte": [], "messe": {}}
                save_json(src, empty)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            with open(src, 'rb') as f:
                self.wfile.write(f.read())
            return

        if self.path == '/coordinates.json':
            src = os.path.join(DATA_DIR, 'coordinates.json')
            if os.path.exists(src):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self._cors()
                self.end_headers()
                with open(src, 'rb') as f:
                    self.wfile.write(f.read())
                return

        # OSINT data
        if self.path == '/osint/data':
            src = os.path.join(DATA_DIR, 'osint-data.json')
            data = load_json(src)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
            return

        # OSINT media
        if self.path.startswith('/osint/media/'):
            filename = self.path.split('/osint/media/', 1)[1]
            safe_path = os.path.normpath(os.path.join(OSINT_DIR, 'media', filename))
            if not safe_path.startswith(OSINT_DIR):
                self._json({'error': 'forbidden'}, 403)
                return
            if os.path.exists(safe_path):
                ct = 'image/jpeg' if safe_path.endswith('.jpg') else 'image/png'
                self.send_response(200)
                self.send_header('Content-Type', ct)
                self._cors()
                self.end_headers()
                with open(safe_path, 'rb') as f:
                    self.wfile.write(f.read())
                return

        # Tile download progress (SSE)
        if self.path == '/tile-progress':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self._cors()
            self.end_headers()
            last = ''
            while tile_state['running']:
                msg = json.dumps(tile_state)
                if msg != last:
                    self.wfile.write(f'data: {msg}\n\n'.encode())
                    self.wfile.flush()
                    last = msg
                time.sleep(0.5)
            self.wfile.write(f'data: {json.dumps(tile_state)}\n\n'.encode())
            return

        if self.path == '/tile-state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps(tile_state).encode())
            return

        # Redirect /admin to admin.html
        if self.path == '/admin' or self.path == '/admin/':
            self.send_response(301)
            self.send_header('Location', '/admin.html')
            self.end_headers()
            return

        return super().do_GET()

    def do_POST(self):
        # OSINT save
        if self.path == '/osint/save':
            body = self._read_body()
            src = os.path.join(DATA_DIR, 'osint-data.json')
            data = load_json(src)
            person = body.get('person', {})
            if not person.get('id'):
                person['id'] = str(uuid.uuid4())
            idx = next((i for i, p in enumerate(data.get('personen', [])) if p.get('id') == person['id']), -1)
            if idx >= 0:
                data['personen'][idx] = person
            else:
                data.setdefault('personen', []).append(person)
            data['stand'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            save_json(src, data)
            self._json({'status': 'ok', 'id': person['id']})
            return

        # OSINT delete
        if self.path == '/osint/delete':
            body = self._read_body()
            pid = body.get('id', '')
            src = os.path.join(DATA_DIR, 'osint-data.json')
            data = load_json(src)
            data['personen'] = [p for p in data.get('personen', []) if p.get('id') != pid]
            save_json(src, data)
            self._json({'status': 'ok'})
            return

        # OSINT start (KI agent)
        if self.path == '/osint/start':
            global osint_state
            body = self._read_body()
            osint_state = {'running': True, 'progress': 0, 'step': 'Starte...', 'result': None}
            urls = body.get('urls', [])
            ort = body.get('ort', 'Erfurt')
            threading.Thread(target=run_osint, args=(urls, ort), daemon=True).start()
            self._json({'status': 'started'})
            return

        # OSINT stop
        if self.path == '/osint/stop':
            osint_state['running'] = False
            self._json({'status': 'stopped'})
            return

        # Tile download
        if self.path == '/tile-download':
            body = self._read_body()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'started'}).encode())
            threading.Thread(target=run_download, args=(body,), daemon=True).start()
            return

        if self.path == '/tile-pause':
            tile_state['paused'] = not tile_state['paused']
            self.send_response(200)
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({'paused': tile_state['paused']}).encode())
            return

        if self.path == '/tile-stop':
            tile_state['running'] = False
            self.send_response(200)
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'stopping'}).encode())
            return


# ── OSINT Agent ──

def run_osint(urls, ort):
    global osint_state

    def update(step_text, pct):
        osint_state['step'] = step_text
        osint_state['progress'] = pct

    try:
        person = {'id': str(uuid.uuid4()), 'name': '', 'alias': [], 'profile_urls': [],
                  'posts': [], 'besuchte_orte': [], 'beziehungen': [], 'bewertung': {},
                  'notizen': '', 'medien': [], 'quellen': [], 'tags': [], 'priorität': 'mittel',
                  'recherche_modus': 'ki', 'recherche_stand': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}

        # Step 1: Extract profile info
        update('Analysiere Profil...', 10)
        for i, url in enumerate(urls):
            plattform = 'x' if 'x.com' in url else 'facebook' if 'facebook.com' in url else 'andere'
            person['profile_urls'].append({'plattform': plattform, 'url': url})
            person['quellen'].append({'typ': 'web_extract', 'url': url, 'datum': time.strftime('%Y-%m-%d')})
            # Try to extract name/handle
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as r:
                    html = r.read().decode('utf-8', errors='ignore')[:10000]
                    handles = re.findall(r'@(\w+)', html)
                    if handles:
                        person['alias'].append('@' + handles[0])
                    # Crude title extraction
                    title = re.search(r'<title>([^<]+)</title>', html)
                    if title and not person['name']:
                        person['name'] = title.group(1).split('|')[0].split('on X')[0].strip()
            except:
                pass
            update(f'Profil {i+1}/{len(urls)} analysiert', 20)

        if not person['name']:
            person['name'] = person['alias'][0] if person['alias'] else 'Unbekannt'

        # Step 2: Search for posts
        update('Suche Posts...', 35)
        search_name = person['name'] or ' '.join(person['alias'])
        try:
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(search_name)}+{urllib.parse.quote(ort)}"
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
                html = r.read().decode('utf-8', errors='ignore')
                snippets = re.findall(r'<span[^>]*>(.{30,200})</span>', html)[:5]
                for s in snippets:
                    clean = re.sub(r'<[^>]+>', '', s)
                    person['posts'].append({
                        'plattform': 'web', 'datum': time.strftime('%Y-%m-%d'),
                        'inhalt': clean[:200], 'url': ''
                    })
            person['quellen'].append({'typ': 'web_search', 'query': f"{search_name} {ort}", 'datum': time.strftime('%Y-%m-%d')})
        except:
            pass
        update(f'{len(person["posts"])} Posts gefunden', 50)

        # Step 3: Analyze content for locations and risk
        update('Analysiere Inhalte...', 70)
        text = ' '.join([p['inhalt'] for p in person['posts']] + [person['name']] + person['alias'])
        gewalt_kw = ['gewalt', 'waffe', 'kampf', 'angriff', 'militant']
        org_kw = ['orga', 'treffen', 'planung', 'gruppe', 'mobilisierung']
        g = sum(1 for kw in gewalt_kw if kw in text.lower())
        o = sum(1 for kw in org_kw if kw in text.lower())
        person['bewertung'] = {
            'stufe': min(5, max(1, (g + o + 1) // 2)),
            'kategorien': {'gewalttätigkeit': min(5, g+1), 'organisationsgrad': min(5, o+1),
                           'mobilität': 2, 'vernetzung': 2},
            'begründung': f'Automatisch erstellt aus {len(person["posts"])} Posts und Profilanalyse.'
        }

        # Step 4: Save
        update('Speichere Ergebnis...', 90)
        src = os.path.join(DATA_DIR, 'osint-data.json')
        data = load_json(src)
        data.setdefault('personen', []).append(person)
        data['stand'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        save_json(src, data)

        osint_state['result'] = person
        osint_state['progress'] = 100
        osint_state['step'] = f'✅ Fertig: {person["name"]}'
        osint_state['running'] = False

    except Exception as e:
        osint_state['step'] = f'❌ Fehler: {str(e)[:100]}'
        osint_state['running'] = False


# ── Tile Download ──

def tile_count(z1, z2, s, n, w, e):
    total = 0
    for z in range(z1, z2 + 1):
        nT = 2 ** z
        lat2t = lambda lat: int((1 - math.log(math.tan(lat * math.pi / 180) + 1 / math.cos(lat * math.pi / 180)) / math.pi) / 2 * nT)
        lon2t = lambda lon: int((lon + 180) / 360 * nT)
        tx1, tx2 = lon2t(w), lon2t(e)
        ty1, ty2 = lat2t(n), lat2t(s)
        total += max(0, tx2 - tx1 + 1) * max(0, ty2 - ty1 + 1)
    return total


def run_download(config):
    global tile_state
    tile_state = {'running': True, 'paused': False, 'progress': 0, 'total': 0, 'current': '', 'errors': 0}
    types = config.get('types', ['osm'])
    base_z1, base_z2 = config.get('base_zoom', [10, 16])
    base_bbox = config.get('base_bbox', [50.2, 51.6, 9.8, 12.6])
    hotspots = config.get('hotspots', [])
    total = tile_count(base_z1, base_z2, *base_bbox) * len(types)
    for h in hotspots:
        total += tile_count(h.get('z1', 17), h.get('z2', 19), *h['bbox']) * len(types)
    tile_state['total'] = total
    done = 0

    def dl_area(label, z1, z2, s, n, w, e):
        nonlocal done
        for z in range(z1, z2 + 1):
            nT = 2 ** z
            lat2t = lambda lat: int((1 - math.log(math.tan(lat * math.pi / 180) + 1 / math.cos(lat * math.pi / 180)) / math.pi) / 2 * nT)
            lon2t = lambda lon: int((lon + 180) / 360 * nT)
            tx1, tx2 = lon2t(w), lon2t(e)
            ty1, ty2 = lat2t(n), lat2t(s)
            for x in range(min(tx1, tx2), max(tx1, tx2) + 1):
                for y in range(min(ty1, ty2), max(ty1, ty2) + 1):
                    if not tile_state['running']:
                        return
                    while tile_state['paused']:
                        time.sleep(0.5)
                        if not tile_state['running']:
                            return
                    for t in types:
                        if t == 'osm':
                            url = f'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
                        else:
                            url = f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
                        path = os.path.join(TILES_DIR, t, str(z), str(x))
                        os.makedirs(path, exist_ok=True)
                        fname = os.path.join(path, f'{y}.png')
                        if not os.path.exists(fname):
                            try:
                                urllib.request.urlretrieve(url, fname)
                                time.sleep(0.05)
                            except:
                                tile_state['errors'] += 1
                        done += 1
                        tile_state['progress'] = min(99, int(done * 100 / tile_state['total']))
                        tile_state['current'] = f'{label} z{z} {t} {x}/{y}'

    dl_area('Basis', base_z1, base_z2, *base_bbox)
    for h in hotspots:
        dl_area(h['name'], h.get('z1', 17), h.get('z2', 19), *h['bbox'])
    tile_state['progress'] = 100
    tile_state['current'] = 'Fertig!'
    tile_state['running'] = False


if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════╗
║   TAKTISCHE KARTE               ║
╠══════════════════════════════════╣
║ 🌐 http://localhost:{PORT}         ║
║ 🗺  /              Live-Karte    ║
║ ✏️  /admin.html    Admin-Panel   ║
║ ⚙  /cron-config   Cronjob       ║
║ 🗺  /setup.html    Tile-Setup    ║
║ 🔍 /osint.html    OSINT         ║
╚══════════════════════════════════╝
""")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server läuft (Strg+C zum Beenden).")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer gestoppt.")
