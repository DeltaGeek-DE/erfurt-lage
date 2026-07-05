#!/usr/bin/env python3
"""Build: Erstellt ein komplettes Release-Paket der Taktischen Karte."""

import zipfile, os, shutil, sys, json

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, 'dist')
VERSION = '1.0.0'

# Clean dist
if os.path.exists(DIST):
    shutil.rmtree(DIST)
os.makedirs(DIST)

RELEASE_NAME = f'taktische-karte-v{VERSION}'
release_dir = os.path.join(DIST, RELEASE_NAME)
os.makedirs(release_dir)

# Alles kopieren (außer dist, .git, __pycache__)
exclude = {'dist', '.git', '__pycache__', 'node_modules', '.venv', 'venv',
           'tiles', 'example-blockaden.json', 'example-coordinates.json'}

def copy_tree(src, dst):
    for item in os.listdir(src):
        if item in exclude:
            continue
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=lambda _, c: [x for x in c if x in exclude])
        else:
            shutil.copy2(s, d)

copy_tree(ROOT, release_dir)

# Erstelle leere tiles-Verzeichnisse
os.makedirs(os.path.join(release_dir, 'app', 'tiles', 'osm'), exist_ok=True)
os.makedirs(os.path.join(release_dir, 'app', 'tiles', 'sat'), exist_ok=True)

# Entferne example-Daten, erstelle frische leere
data_dir = os.path.join(release_dir, 'app', 'data')
for old in ['blockaden-data.json', 'example-blockaden.json', 'example-coordinates.json']:
    p = os.path.join(data_dir, old)
    if os.path.exists(p):
        os.remove(p)

# Frische leere Daten
with open(os.path.join(data_dir, 'blockaden-data.json'), 'w', encoding='utf-8') as f:
    json.dump({"stand":"","blockaden":[],"events":[],"strassen_abschnitte":[],"lage_gesamt":""}, f, ensure_ascii=False, indent=2)

with open(os.path.join(data_dir, 'coordinates.json'), 'w', encoding='utf-8') as f:
    json.dump({}, f, ensure_ascii=False, indent=2)

# ZIP erstellen
zip_path = os.path.join(DIST, f'{RELEASE_NAME}.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(release_dir):
        for file in files:
            full = os.path.join(root, file)
            arc = os.path.relpath(full, DIST)
            zf.write(full, arc)

size = os.path.getsize(zip_path)

# Saubermachen
shutil.rmtree(release_dir)

print(f"""
╔══════════════════════════════════════╗
║ ✅ Release v{VERSION} erstellt            ║
╠══════════════════════════════════════╣
║ 📦 {zip_path}
║ 📏 {size/1024:.0f} KB ({size/1024/1024:.1f} MB)
╠══════════════════════════════════════╣
║ Installation beim Anwender:          ║
║ 1. ZIP entpacken                     ║
║ 2. python server.py                  ║
║ 3. http://localhost:8765             ║
╚══════════════════════════════════════╝
""")
