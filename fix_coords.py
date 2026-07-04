"""fix_coords.py — coordinates.json als Wahrheit, Nominatim als Fallback für neue Orte."""
import json, math, urllib.request, urllib.parse, time

COORDS_FILE = r'C:\Users\tomri\Desktop\ISATIS\coordinates.json'
DATA_FILE = r'C:\Users\tomri\Desktop\ISATIS\blockaden-data.json'

with open(COORDS_FILE, 'r', encoding='utf-8') as f:
    TRUTH = json.load(f)

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    js = json.load(f)

def dist(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2) * 111000

def geocode(name):
    try:
        q = urllib.parse.quote(name + ", Erfurt, Thüringen")
        url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'ErfurtFixer/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data:
            return [round(float(data[0]['lat']), 5), round(float(data[0]['lon']), 5)]
    except Exception as e:
        print(f"  Nominatim error: {e}")
    return None

def find_best(name):
    nl = name.lower()
    for key, coord in TRUTH.items():
        kl = key.lower().replace(', erfurt', '').replace(' erfurt', '')
        words = kl.split()
        if sum(1 for w in words if w in nl) >= 1:
            return coord
    return None

fixed = 0

# Fix messe object
if js.get('messe'):
    t = TRUTH.get('Messe Erfurt')
    if t and dist([js['messe']['lat'], js['messe']['lon']], t) > 500:
        js['messe']['lat'], js['messe']['lon'] = t[0], t[1]; fixed += 1

# Fix old Messe coordinates
OLD_MESSE = [50.938, 11.008]
NEW_MESSE = TRUTH.get('Messe Erfurt', [50.95932, 10.98967])
for ev in js.get('events', []):
    c = [ev['lat'], ev['lon']]
    if dist(c, OLD_MESSE) < 100 and dist(c, NEW_MESSE) > 500:
        ev['lat'], ev['lon'] = NEW_MESSE[0], NEW_MESSE[1]; fixed += 1

# Fix all entries
for arr_name in ['blockaden', 'events']:
    for item in js.get(arr_name, []):
        name = item.get('name', '')
        c = [item['lat'], item['lon']]
        best = find_best(name)
        if best and dist(c, best) > 500:
            item['lat'], item['lon'] = best[0], best[1]; fixed += 1
        elif not best:
            # Fallback: Nominatim geocoding for unknown locations
            geo = geocode(name)
            if geo:
                TRUTH[name] = geo  # Save for future
                if dist(c, geo) > 500:
                    item['lat'], item['lon'] = geo[0], geo[1]; fixed += 1
            time.sleep(1.2)

if fixed:
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(js, f, ensure_ascii=False, indent=2)
    with open(COORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(TRUTH, f, ensure_ascii=False, indent=2)
    print(f"{fixed} Koordinaten korrigiert. Neue Orte in coordinates.json gespeichert.")
else:
    print("Alle Koordinaten OK.")
