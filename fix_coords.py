"""fix_coords.py — Geokodiert ALLE Blockaden-Koordinaten via OSM Nominatim.
Toleranz: 500m. Alles darüber wird korrigiert. Läuft nach jedem Cronjob-Update."""
import json, urllib.request, urllib.parse, time, sys

# Nur als Fallback, wenn Nominatim nichts findet
FALLBACK = {
    'gothaer platz': (50.97135, 11.01139),
    'blumenstraße': (50.98432, 11.00614),
    'blumenstr': (50.98432, 11.00614),
    'clara-zetkin': (50.97242, 11.04254),
    'clara zetkin': (50.97242, 11.04254),
    'frienstedt': (50.95608, 10.90877),
    'gispersleben': (51.01889, 10.99087),
    'geratalstraße': (50.94820, 10.99577),
    'geratalstr': (50.94820, 10.99577),
    'bischleben': (50.94820, 10.99577),
    'winzerstraße': (50.95890, 11.00043),
    'winzerstr': (50.95890, 11.00043),
    'bindersleben': (50.97452, 10.94897),
    'hauptfriedhof': (50.97294, 10.99332),
    'friedhof': (50.97294, 10.99332),
    'schmira': (50.95361, 10.97081),
    'brühler herrenberg': (50.97272, 11.00602),
    'brühler': (50.97272, 11.00602),
    'wartburgstraße': (50.96143, 11.00288),
    'wartburgstr': (50.96143, 11.00288),
    'cyriakstraße': (50.96534, 11.01026),
    'cyriakstr': (50.96534, 11.01026),
    'eisenacher': (50.95613, 10.97656),
    'messe': (50.95932, 10.98967),
    'erfurter kreuz': (50.92000, 10.96400),
    'k14': (50.97452, 10.94897),
    'gottstedter': (50.96919, 10.91043),
    'alach': (50.96919, 10.91043),
    'gottstedt': (50.96919, 10.91043),
    'stotternheim': (51.056, 11.043),
    'mittelhausen': (51.035, 11.002),
    'hohenwinden': (51.017, 11.038),
}

def geocode(query):
    """Geocode via Nominatim, return (lat, lon) or None."""
    try:
        q = urllib.parse.quote(f"{query}, Erfurt, Thüringen")
        url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'ErfurtLagekarte/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"  Nominatim error: {e}", file=sys.stderr)
    return None

def dist_m(a, b):
    """Rough distance in meters between two (lat,lon) points."""
    return ((a[0]-b[0])*111000)**2 + ((a[1]-b[1])*71000)**2  # squared meters

PATH = r'C:\Users\tomri\Desktop\ISATIS\blockaden-data.json'

with open(PATH, 'r', encoding='utf-8') as f:
    js = json.load(f)

fixed = 0

for b in js.get('blockaden', []):
    current = (b['lat'], b['lon'])
    name = b['name']
    
    # Try fallback table first (fast, no API call)
    nl = name.lower()
    best = None
    for key, coord in FALLBACK.items():
        if key in nl:
            best = coord
            break
    
    # If no fallback, or fallback is far from current, try geocoding
    if best and dist_m(current, best) < 600**2:
        continue  # within 600m — good enough
    
    # Try Nominatim
    result = geocode(name)
    if result:
        if dist_m(current, result) > 500**2:
            old = current
            b['lat'], b['lon'] = result
            print(f"FIX (geo)  {name}: {old} -> {result}")
            fixed += 1
    elif best:
        if dist_m(current, best) > 500**2:
            old = current
            b['lat'], b['lon'] = best
            print(f"FIX (table) {name}: {old} -> {best}")
            fixed += 1
    time.sleep(1.2)  # Nominatim rate limit

# Also fix events
for ev in js.get('events', []):
    current = (ev['lat'], ev['lon'])
    nl = ev['name'].lower()
    for key, coord in FALLBACK.items():
        if key in nl and dist_m(current, coord) > 500**2:
            ev['lat'], ev['lon'] = coord
            print(f"FIX (event) {ev['name']}: {current} -> {coord}")
            fixed += 1
            break

if fixed > 0:
    js['stand'] = time.strftime('2026-07-04T%H:%M:%S+02:00')
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(js, f, ensure_ascii=False, indent=2)
    print(f"\n{fixed} Koordinaten korrigiert.")
else:
    print("Alle Koordinaten korrekt — keine Korrekturen nötig.")
