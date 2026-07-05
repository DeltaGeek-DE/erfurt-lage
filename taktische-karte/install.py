#!/usr/bin/env python3
"""Taktische Karte — One-Click Installer.
Erstellt das komplette Setup: Ordnerstruktur, Abhängigkeiten, Start-Skript."""

import os, sys, json, shutil, subprocess, platform

INSTALL_DIR = os.path.join(os.path.expanduser("~"), "TaktischeKarte")
APP_DIR = os.path.dirname(os.path.abspath(__file__))

def header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def check_python():
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 11):
        print("❌ Python 3.11+ benötigt. Aktuell:", sys.version)
        sys.exit(1)
    print(f"✅ Python {v.major}.{v.minor}.{v.micro}")

def install_hermes():
    """Prüft und installiert Hermes Agent falls nötig."""
    try:
        result = subprocess.run(['hermes', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Hermes Agent gefunden: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    print("📦 Hermes Agent wird installiert...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'hermes-agent'], check=True)
        print("✅ Hermes Agent installiert")
        return True
    except Exception as e:
        print(f"⚠ Hermes-Installation übersprungen: {e}")
        print("  Manuelle Installation: pip install hermes-agent")
        return False

def setup_directories():
    """Erstellt die komplette Ordnerstruktur."""
    dirs = [
        'app', 'app/assets/leaflet', 'app/assets/markercluster',
        'app/data', 'app/scripts', 'app/tiles/osm', 'app/tiles/sat',
        'logs'
    ]
    for d in dirs:
        os.makedirs(os.path.join(INSTALL_DIR, d), exist_ok=True)
    print(f"✅ Ordnerstruktur: {INSTALL_DIR}")

def copy_app():
    """Kopiert alle App-Dateien."""
    files = [
        ('app/index.html', 'app/index.html'),
        ('app/admin.html', 'app/admin.html'),
        ('app/index-local.html', 'app/index-local.html'),
        ('app/assets/leaflet/leaflet.js', 'app/assets/leaflet/leaflet.js'),
        ('app/assets/leaflet/leaflet.css', 'app/assets/leaflet/leaflet.css'),
        ('app/assets/markercluster/leaflet.markercluster.js', 'app/assets/markercluster/leaflet.markercluster.js'),
        ('app/assets/markercluster/MarkerCluster.css', 'app/assets/markercluster/MarkerCluster.css'),
        ('app/assets/share-tech-mono.css', 'app/assets/share-tech-mono.css'),
        ('app/data/coordinates.json', 'app/data/coordinates.json'),
        ('app/scripts/fix_coords.py', 'app/scripts/fix_coords.py'),
        ('app/scripts/geocode.py', 'app/scripts/geocode.py'),
        ('server.py', 'server.py'),
        ('tile_server.py', 'tile_server.py'),
        ('KI-ANLEITUNG.md', 'KI-ANLEITUNG.md'),
        ('README.md', 'README.md'),
        ('setup.html', 'setup.html'),
    ]
    copied = 0
    for src, dst in files:
        src_path = os.path.join(APP_DIR, src)
        dst_path = os.path.join(INSTALL_DIR, dst)
        if os.path.exists(src_path):
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src_path, dst_path)
            copied += 1
        else:
            print(f"  ⚠ Fehlt: {src}")

    print(f"✅ {copied}/{len(files)} Dateien kopiert")
    return copied

def create_launcher():
    """Erstellt Start-Skript für Windows."""
    if platform.system() == 'Windows':
        # Batch-Datei
        bat = f'''@echo off
cd /d "{INSTALL_DIR}"
echo.
echo ╔══════════════════════════════════╗
echo ║   TAKTISCHE KARTE               ║
echo ╠══════════════════════════════════╣
echo ║ [1] Server starten              ║
echo ║ [2] Admin-Panel öffnen          ║
echo ║ [3] Setup (Tiles downloaden)    ║
echo ║ [4] Server + Admin starten      ║
echo ║ [5] Beenden                     ║
echo ╚══════════════════════════════════╝
echo.
set /p choice="Auswahl: "
if "%choice%"=="1" goto server
if "%choice%"=="2" goto admin
if "%choice%"=="3" goto setup
if "%choice%"=="4" goto both
if "%choice%"=="5" goto end

:server
start "Taktische Karte Server" python server.py
echo Server gestartet auf http://localhost:8765
pause
goto end

:admin
start http://localhost:8765/admin.html
goto end

:setup
start http://localhost:8765/setup.html
goto end

:both
start "Taktische Karte Server" python server.py
timeout /t 2 >nul
start http://localhost:8765/admin.html
goto end

:end
'''
        with open(os.path.join(INSTALL_DIR, 'start.bat'), 'w', encoding='utf-8') as f:
            f.write(bat)
        print("✅ start.bat erstellt")

    # Python-Launcher (plattformunabhängig)
    py = f'''#!/usr/bin/env python3
"""Taktische Karte Launcher."""
import subprocess, webbrowser, os, sys
os.chdir(r"{INSTALL_DIR}")
print("╔══════════════════════════════════╗")
print("║   Taktische Karte Launcher      ║")
print("╠══════════════════════════════════╣")
print("║ [1] Server + Admin starten      ║")
print("║ [2] Nur Admin öffnen            ║")
print("║ [3] Setup (Tiles)               ║")
print("╚══════════════════════════════════╝")
try:
    c = input("Auswahl: ").strip()
    if c == '1':
        subprocess.Popen([sys.executable, 'server.py'])
        webbrowser.open('http://localhost:8765/admin.html')
    elif c == '2':
        webbrowser.open('http://localhost:8765/admin.html')
    elif c == '3':
        webbrowser.open('http://localhost:8765/setup.html')
except KeyboardInterrupt:
    pass
'''
    with open(os.path.join(INSTALL_DIR, 'launcher.py'), 'w', encoding='utf-8') as f:
        f.write(py)
    print("✅ launcher.py erstellt")

def create_cronjob_template():
    """Erstellt einen Cronjob-Template-Prompt."""
    coords_path = os.path.join(INSTALL_DIR, 'app', 'data', 'coordinates.json')
    data_path = os.path.join(INSTALL_DIR, 'app', 'data', 'blockaden-data.json')
    fix_path = os.path.join(INSTALL_DIR, 'app', 'scripts', 'fix_coords.py')

    prompt = f'''PRÜFE ALLE EINTRÄGE. Alle 5 Minuten.

**REGELN**:
- KEINE KOORDINATEN ERFINDEN. Setze neue Einträge auf ZENTRUM_LAT/ZENTRUM_LON. fix_coords.py korrigiert.
- Nur mit expliziter Quellen-Bestätigung löschen/hinzufügen.
- NIEMALS Zukunfts-Daten eintragen.

**WEBSEARCH** (6 Queries):
1. "Polizei ORT Blockaden aktuell DATUM"
2. "site:x.com HASHTAG OR ORT"
3. "site:x.com @POLIZEI_ACCOUNT OR @REPORTER"
4. "EREIGNIS Proteste Blockaden aufgelöst DATUM"
5. "site:presseportal.de POLIZEI ORT DATUM"
6. "site:de.indymedia.org ORT"

**DATENQUELLE**: {data_path}
**KOORDINATEN**: {coords_path}

**TERMINAL**: python {fix_path}
'''
    with open(os.path.join(INSTALL_DIR, 'cronjob-prompt.txt'), 'w', encoding='utf-8') as f:
        f.write(prompt)
    print("✅ cronjob-prompt.txt erstellt")

# ── MAIN ──
if __name__ == '__main__':
    header("TAKTISCHE KARTE — Installation")
    check_python()
    install_hermes()
    setup_directories()
    copy_app()
    create_launcher()
    create_cronjob_template()

    header("✅ INSTALLATION ABGESCHLOSSEN")
    print(f"""
  Ordner: {INSTALL_DIR}

  Starten:
    Windows: Doppelklick auf start.bat
    Alle OS: python launcher.py

  Server manuell:
    python server.py
    → http://localhost:8765

  Setup (Tiles downloaden):
    → http://localhost:8765/setup.html

  KI-Cronjob einrichten:
    Hermes-App öffnen → /cron → Prompt aus cronjob-prompt.txt einfügen
""")
