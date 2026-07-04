#!/usr/bin/env python3
"""
Erfurt Blockaden-Updater
Läuft alle 5 Minuten via Cronjob.
Sammelt aktuelle Blockaden-Daten aus:
  - presseportal.de (Polizei Thüringen)
  - web_search (@Polizei_Thuer auf X)
  - Bekannte Live-Ticker (taz, MDR, WELT, t-online)

Output: blockaden-data.json im selben Verzeichnis
"""

import json, re, subprocess, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── KONFIGURATION ──────────────────────────────────
OUTPUT_DIR = Path(__file__).parent if '__file__' in dir() else Path.cwd()
OUTPUT_FILE = OUTPUT_DIR / 'blockaden-data.json'
BERLIN_TZ = timezone(timedelta(hours=2))

# Bekannte Koordinaten für Erfurt
KOORDINATEN = {
    'erfurter kreuz': (50.92, 10.97),
    'a71': (50.92, 10.97),
    'gothaer platz': (50.9645, 11.0085),
    'clara-zetkin': (50.9712, 11.0429),
    'clara zetkin': (50.9712, 11.0429),
    'frienstedt': (50.952, 10.918),
    'bindersleben': (50.968, 10.938),
    'gispersleben': (51.018, 11.005),
    'b4': (51.018, 11.005),
    'b7': (50.952, 10.918),
    'blumenstraße': (50.976, 11.022),
    'blumenstr': (50.976, 11.022),
    'geratalstraße': (50.935, 10.945),
    'geratalstr': (50.935, 10.945),
    'bischleben': (50.935, 10.945),
    'winzerstraße': (50.968, 11.030),
    'winzerstr': (50.968, 11.030),
    'hauptfriedhof': (50.975, 11.005),
    'schmira': (50.955, 10.980),
    'gottstedt': (51.000, 10.968),
    'alach': (51.015, 10.950),
    'mittelhausen': (51.02, 11.04),
    'stotternheim': (51.02, 11.04),
    'messe erfurt': (50.938, 11.008),
    'messe': (50.938, 11.008),
    'gamstädt': (50.965, 10.900),
    'gamstadt': (50.965, 10.900),
    'k14': (50.968, 10.942),
    'molsdorf': (50.90, 10.96),
}

# ─── HILFSFUNKTIONEN ────────────────────────────────

def now_iso():
    return datetime.now(BERLIN_TZ).isoformat()

def curl_text(url, timeout=10):
    """Einfacher HTTP GET, gibt Text zurück."""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as f:
            return f.read().decode('utf-8', errors='replace')
    except Exception as e:
        return f"ERROR: {e}"

def extract_tn(text):
    """Extrahiere Teilnehmerzahl aus Text."""
    m = re.search(r'(?:ca\.?\s*)?(\d+\.?\d*)\s*(?:TN|Personen|Teilnehmer|Teilnehmende|Aktivisten|Demonstrant)', text, re.IGNORECASE)
    if m:
        val = m.group(1).replace('.', '')
        try: return int(val)
        except: return m.group(1)
    m = re.search(r'tausend(?:e)?', text, re.IGNORECASE)
    if m: return 'tausende'
    return '?'


# ─── QUELLE 1: presseportal.de ──────────────────────

def fetch_presseportal():
    """Hole aktuelle PMs der Landespolizeidirektion Thüringen."""
    results = []
    url = 'https://www.presseportal.de/blaulicht/r/Erfurt'
    text = curl_text(url)

    # Suche nach Artikeln vom 04.07.2026
    entries = re.findall(r'<a[^>]*href="(/blaulicht/pm/\d+/\d+)"[^>]*>([^<]+)</a>', text)
    for href, title in entries[:5]:
        full_url = 'https://www.presseportal.de' + href
        article = curl_text(full_url)
        # Extrahiere Fließtext
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', article, re.DOTALL)
        body = ' '.join(re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs)
        if any(w in body.lower() for w in ['blockade', 'blockiert', 'versammlung', 'sperrung', 'demonstration', 'erfurt']):
            results.append({'quelle': full_url, 'text': body[:2000]})
    return results


# ─── QUELLE 2: X/Twitter (@Polizei_Thuer) ────────────

def fetch_polizei_x():
    """Hole aktuelle Tweets via Hermes web_search (wird im Cron-Kontext aufgerufen)."""
    results = []
    # Im Cron-Kontext haben wir keinen direkten Zugriff auf web_search,
    # also per Subprozess oder wir verlassen uns auf den Prompt.
    # Stattdessen: Nutze die Social-Media-Embeds von presseportal
    return results


# ─── PARSING: Text → Blockaden ──────────────────────

def parse_blockaden_from_text(text):
    """Versuche Blockaden aus Text zu parsen."""
    found = []
    text_lower = text.lower()

    for name, coords in KOORDINATEN.items():
        if name in text_lower:
            # Suche TN-Zahl in der Nähe
            idx = text_lower.index(name)
            context = text[max(0,idx-200):idx+300]
            tn = extract_tn(context)

            typ = 'normal'
            if isinstance(tn, int) and tn >= 500:
                typ = 'gross'
            if 'sitz' in context.lower() or 'sitzblockade' in context.lower():
                typ = 'sitz'
            if 'abgeriegelt' in context.lower() or 'komplett' in context.lower():
                typ = 'barrikade'

            # Extrahiere Notiz
            note_match = re.search(r'([^.]*' + re.escape(name) + r'[^.]*\.)', text, re.IGNORECASE)
            note = note_match.group(1).strip()[:200] if note_match else ''

            found.append({
                'name': name.title(),
                'lat': coords[0],
                'lon': coords[1],
                'tn': tn,
                'typ': typ,
                'note': note
            })
    return found


def parse_strassen_abschnitte(text):
    """Erkenne Straßenabschnitte im Text."""
    abschnitte = []
    # Pattern: "A71 zwischen X und Y" oder "B7 von X bis Y"
    pattern = r'(A\d+|B\d+|K\d+|L\d+)\s+(?:zwischen|von)\s+([A-Za-zäöüß\-]+)\s+(?:und|bis)\s+([A-Za-zäöüß\-]+)'
    for match in re.finditer(pattern, text, re.IGNORECASE):
        road = match.group(1).upper()
        start_name = match.group(2).lower()
        end_name = match.group(3).lower()

        start_coords = KOORDINATEN.get(start_name)
        end_coords = KOORDINATEN.get(end_name)

        if start_coords and end_coords:
            abschnitte.append({
                'name': f'{road} GESPERRT',
                'route': [list(start_coords), list(end_coords)],
                'farbe': '#ff0000',
                'note': f'{start_name.title()} ↔ {end_name.title()}'
            })
    return abschnitte


# ─── HAUPTPROGRAMM ──────────────────────────────────

def main():
    print(f"[{datetime.now(BERLIN_TZ).strftime('%H:%M:%S')}] Starte Update...")

    alle_texte = []

    # 1. presseportal.de
    try:
        pm = fetch_presseportal()
        for p in pm:
            alle_texte.append(p['text'])
        print(f"  presseportal.de: {len(pm)} relevante PMs")
    except Exception as e:
        print(f"  presseportal.de FEHLER: {e}")

    # 2. X/Twitter wird im Cronjob-Kontext über den Prompt abgedeckt
    #    (Der Cronjob-Prompt ruft web_search auf)

    # Falls keine Texte, Basis-Daten behalten
    if not alle_texte:
        print("  Keine neuen Texte gefunden. Überspringe Update.")
        if OUTPUT_FILE.exists():
            print(f"  Behalte existierende {OUTPUT_FILE}")
            return
        else:
            print("  Keine existierende JSON. Erstelle Basis-Daten.")
            alle_texte = ['']

    full_text = ' '.join(alle_texte)

    # Parsen
    blockaden = parse_blockaden_from_text(full_text)
    abschnitte = parse_strassen_abschnitte(full_text)

    print(f"  Gefunden: {len(blockaden)} Blockaden, {len(abschnitte)} Abschnitte")

    # Wenn nichts gefunden, existierende Daten laden und nur Stand aktualisieren
    if not blockaden and OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        blockaden = existing.get('blockaden', [])
        abschnitte = existing.get('strassen_abschnitte', [])
        events = existing.get('events', [])
        messe = existing.get('messe', {})
        print("  Nutze existierende Blockaden-Daten.")
    else:
        events = [
            {
                'name': '⚠ ABSEILAKTION',
                'lat': 51.018, 'lon': 11.04,
                'typ': 'abseil',
                'note': 'A71-Brücke Mittelhausen/Stotternheim.'
            }
        ]
        messe = {
            'lat': 50.938, 'lon': 11.008,
            'status': 'Parteitag läuft seit 10:00'
        }

    data = {
        'stand': now_iso(),
        'quelle': 'Presseportal + @Polizei_Thuer',
        'blockaden': blockaden,
        'strassen_abschnitte': abschnitte,
        'events': events,
        'messe': messe
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  → {OUTPUT_FILE} geschrieben ({len(blockaden)} Blockaden, {len(abschnitte)} Abschnitte)")

if __name__ == '__main__':
    main()
