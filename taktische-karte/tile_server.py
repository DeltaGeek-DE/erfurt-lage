#!/usr/bin/env python3
"""Tile-Download-Server für die Taktische Karte.
Läuft auf Port 8766, akzeptiert POST /download mit JSON-Konfiguration,
sendet Fortschritt per SSE an GET /progress."""

import http.server, json, urllib.request, os, math, time, sys, threading

TILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'tiles')
os.makedirs(TILES_DIR, exist_ok=True)

download_state = {'running': False, 'paused': False, 'progress': 0, 'total': 0, 'current': '', 'errors': 0}


class SSERequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silent

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/progress':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            last = ''
            while download_state['running']:
                msg = json.dumps(download_state)
                if msg != last:
                    self.wfile.write(f'data: {msg}\n\n'.encode())
                    self.wfile.flush()
                    last = msg
                time.sleep(0.5)
            self.wfile.write(f'data: {json.dumps(download_state)}\n\n'.encode())
            return

        if self.path == '/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(download_state).encode())
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == '/download':
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'started'}).encode())

            # Start download in background thread
            threading.Thread(target=run_download, args=(body,), daemon=True).start()
            return

        if self.path == '/pause':
            download_state['paused'] = not download_state['paused']
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'paused': download_state['paused']}).encode())
            return

        if self.path == '/stop':
            download_state['running'] = False
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'stopping'}).encode())
            return

        self.send_response(404)
        self.end_headers()


def tile_count(z1, z2, s, n, w, e):
    total = 0
    for z in range(z1, z2+1):
        nT = 2**z
        lat2tile = lambda lat: int((1 - math.log(math.tan(lat*math.pi/180) + 1/math.cos(lat*math.pi/180))/math.pi) / 2 * nT)
        lon2tile = lambda lon: int((lon + 180) / 360 * nT)
        tx1, tx2 = lon2tile(w), lon2tile(e)
        ty1, ty2 = lat2tile(n), lat2tile(s)
        total += max(0, tx2-tx1+1) * max(0, ty2-ty1+1)
    return total


def run_download(config):
    global download_state
    download_state = {'running': True, 'paused': False, 'progress': 0, 'total': 0, 'current': '', 'errors': 0}

    types = config.get('types', ['osm'])
    base_z1, base_z2 = config.get('base_zoom', [10, 16])
    base_bbox = config.get('base_bbox', [50.2, 51.6, 9.8, 12.6])  # s,n,w,e
    hotspots = config.get('hotspots', [])

    # Count total tiles
    total = tile_count(base_z1, base_z2, *base_bbox) * len(types)
    for h in hotspots:
        total += tile_count(h.get('z1', 17), h.get('z2', 19), *h['bbox']) * len(types)
    download_state['total'] = total

    done = 0

    def download_area(label, z1, z2, s, n, w, e):
        nonlocal done
        for z in range(z1, z2+1):
            nT = 2**z
            lat2tile = lambda lat: int((1 - math.log(math.tan(lat*math.pi/180) + 1/math.cos(lat*math.pi/180))/math.pi) / 2 * nT)
            lon2tile = lambda lon: int((lon + 180) / 360 * nT)
            tx1, tx2 = lon2tile(w), lon2tile(e)
            ty1, ty2 = lat2tile(n), lat2tile(s)

            for x in range(min(tx1, tx2), max(tx1, tx2)+1):
                for y in range(min(ty1, ty2), max(ty1, ty2)+1):
                    if not download_state['running']:
                        return
                    while download_state['paused']:
                        time.sleep(0.5)
                        if not download_state['running']:
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
                            except Exception as e:
                                download_state['errors'] += 1

                        done += 1
                        download_state['progress'] = min(99, int(done * 100 / download_state['total']))
                        download_state['current'] = f'{label} z{z} {t} {x}/{y}'

    # Base
    download_area('Basis', base_z1, base_z2, *base_bbox)

    # Hotspots
    for h in hotspots:
        download_area(h['name'], h.get('z1', 17), h.get('z2', 19), *h['bbox'])

    download_state['progress'] = 100
    download_state['current'] = 'Fertig!'
    download_state['running'] = False


def main():
    port = 8766
    print(f"""
╔══════════════════════════════════╗
║   Tile Download Server           ║
╠══════════════════════════════════╣
║ Port: {port}                        ║
║ Tiles: {TILES_DIR}
║ POST /download → Start           ║
║ GET  /progress → SSE-Stream      ║
║ POST /pause    → Pause/Resume   ║
║ POST /stop     → Abbrechen      ║
╚══════════════════════════════════╝
""")
    server = http.server.HTTPServer(('', port), SSERequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer gestoppt.')


if __name__ == '__main__':
    main()
