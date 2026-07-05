#!/usr/bin/env python3
"""Taktische Karte — Ein Server für alles: Karte, Admin, Tile-Download."""
import http.server, socketserver, os, sys, json, urllib.request, math, time, threading

PORT = 8765
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
DATA_DIR = os.path.join(DIR, 'data')
TILES_DIR = os.path.join(DIR, 'tiles')
os.makedirs(TILES_DIR, exist_ok=True)

tile_state = {'running': False, 'paused': False, 'progress': 0, 'total': 0, 'current': '', 'errors': 0}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def log_message(self, format, *args):
        pass

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        # JSON data from data/ directory
        if self.path == '/blockaden-data.json' or self.path.startswith('/blockaden-data.json?'):
            src = os.path.join(DATA_DIR, 'blockaden-data.json')
            if not os.path.exists(src):
                empty = {"stand": "", "blockaden": [], "events": [], "strassen_abschnitte": [], "messe": {}}
                with open(src, 'w', encoding='utf-8') as f:
                    json.dump(empty, f)
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
        if self.path == '/tile-download':
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))
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
║ ⚙  /cron-config.html  Cronjob   ║
║ 🗺  /setup.html    Tile-Setup    ║
║ 📥 /tile-download Tile-Download ║
╚══════════════════════════════════╝
""")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server läuft (Strg+C zum Beenden).")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer gestoppt.")
