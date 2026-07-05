#!/usr/bin/env python3
"""Taktische Karte — Lokaler Server (offline-fähig)."""
import http.server
import socketserver
import os
import sys

PORT = 8765
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)
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
