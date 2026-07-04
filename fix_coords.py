"""fix_coords.py — Korrigiert ALLE Koordinaten anhand coordinates.json (Single Source of Truth)."""
import json, math

COORDS_FILE = r'C:\Users\tomri\Desktop\ISATIS\coordinates.json'
DATA_FILE = r'C:\Users\tomri\Desktop\ISATIS\blockaden-data.json'

with open(COORDS_FILE, 'r', encoding='utf-8') as f:
    TRUTH = json.load(f)

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    js = json.load(f)

def dist(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2) * 111000

def find_best(name):
    nl = name.lower()
    for key, coord in TRUTH.items():
        kl = key.lower().replace(', erfurt', '').replace(' erfurt', '')
        words = kl.split()
        if sum(1 for w in words if w in nl) >= 1:
            return coord
    return None

fixed = 0

if js.get('messe'):
    t = TRUTH.get('Messe Erfurt')
    if t and dist([js['messe']['lat'], js['messe']['lon']], t) > 500:
        js['messe']['lat'], js['messe']['lon'] = t[0], t[1]; fixed += 1

for arr_name in ['blockaden', 'events']:
    for item in js.get(arr_name, []):
        c = [item['lat'], item['lon']]
        best = find_best(item.get('name', ''))
        if best and dist(c, best) > 500:
            item['lat'], item['lon'] = best[0], best[1]; fixed += 1

if fixed:
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(js, f, ensure_ascii=False, indent=2)
    print(f"{fixed} Koordinaten korrigiert.")
else:
    print("Alle Koordinaten OK.")
