#!/usr/bin/env python3
"""Taktische Karte — Lokaler Server (offline-fähig, KI-bereit)."""
import http.server, socketserver, os, sys, json, shutil

PORT = 8765
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
DATA_DIR = os.path.join(DIR, 'data')

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self):
        # Serve blockaden-data.json from data/ directory
        if self.path == '/blockaden-data.json' or self.path.startswith('/blockaden-data.json?'):
            src = os.path.join(DATA_DIR, 'blockaden-data.json')
            if not os.path.exists(src):
                # Create empty if missing
                empty = {"stand": "", "blockaden": [], "events": [], "strassen_abschnitte": [], "messe": {}}
                with open(src, 'w', encoding='utf-8') as f:
                    json.dump(empty, f, ensure_ascii=False, indent=2)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
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
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(src, 'rb') as f:
                    self.wfile.write(f.read())
                return

        return super().do_GET()

    def log_message(self, format, *args):
        print(f"  {args[0]}")

if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════╗
║   TAKTISCHE KARTE — Offline      ║
╠══════════════════════════════════╣
║ 🌐 http://localhost:{PORT}         ║
║ 🗺  /index.html    Live-Karte     ║
║ ✏️  /admin.html    Admin-Panel    ║
║ 📁 {DIR}
╚══════════════════════════════════╝
""")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server läuft auf Port {PORT}. Strg+C zum Beenden.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer gestoppt.")
