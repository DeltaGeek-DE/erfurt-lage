#!/usr/bin/env python3
"""Build a release ZIP of Taktische Karte."""
import zipfile, os, shutil, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, 'dist')
ZIP_NAME = 'taktische-karte.zip'

# Clean dist
if os.path.exists(DIST):
    shutil.rmtree(DIST)
os.makedirs(DIST)

# Files to include
include = [
    'README.md', 'server.py', 'requirements.txt',
    'app/index.html', 'app/admin.html',
    'app/assets/leaflet/leaflet.js', 'app/assets/leaflet/leaflet.css',
    'app/assets/markercluster/leaflet.markercluster.js', 'app/assets/markercluster/MarkerCluster.css',
    'app/scripts/fix_coords.py', 'app/scripts/geocode.py',
    'app/data/example-coordinates.json', 'app/data/example-blockaden.json',
]

zip_path = os.path.join(DIST, ZIP_NAME)
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in include:
        src = os.path.join(ROOT, f)
        if os.path.exists(src):
            zf.write(src, f)
            print(f'  + {f}')
        else:
            print(f'  ⚠ {f} nicht gefunden — übersprungen')

size = os.path.getsize(zip_path)
print(f'\n✅ Release: {zip_path} ({size/1024:.0f} KB)')
