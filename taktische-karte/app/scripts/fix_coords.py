"""fix_coords.py — ERZWINGT alle Koordinaten aus coordinates.json. Kein Toleranzbereich mehr."""
import json

COORDS_FILE = r'C:\Users\tomri\Desktop\ISATIS\taktische-karte\app\data\coordinates.json'
DATA_FILE = r'C:\Users\tomri\Desktop\ISATIS\taktische-karte\app\data\blockaden-data.json'

with open(COORDS_FILE, 'r', encoding='utf-8') as f:
    TRUTH = json.load(f)

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    js = json.load(f)

fixed = 0

def force_fix(item):
    """Find matching truth coord and force-overwrite."""
    name = item.get('name', '').lower()
    for key, coord in TRUTH.items():
        kl = key.lower().replace(', erfurt', '').replace(' erfurt', '')
        for word in kl.split():
            if word in name:
                old = [item['lat'], item['lon']]
                new = [coord[0], coord[1]]
                if old != new:
                    item['lat'], item['lon'] = new[0], new[1]
                    global fixed
                    fixed += 1
                    print(f"  FIX {name[:50]}: {old} → {new}")
                return
    # No match found
    print(f"  ? {name[:60]} — kein Match in coordinates.json")

# Force-fix Messe
if js.get('messe') and 'Messe Erfurt' in TRUTH:
    c = TRUTH['Messe Erfurt']
    old = [js['messe']['lat'], js['messe']['lon']]
    if old != [c[0], c[1]]:
        js['messe']['lat'], js['messe']['lon'] = c[0], c[1]
        fixed += 1
        print(f"  FIX messe: {old} → {c}")

# Force-fix ALL blockades
print("\n=== BLOCKADEN ===")
for b in js.get('blockaden', []):
    force_fix(b)

# Force-fix ALL events
print("\n=== EVENTS ===")
for ev in js.get('events', []):
    force_fix(ev)

if fixed:
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(js, f, ensure_ascii=False, indent=2)
    print(f"\n{fixed} Koordinaten korrigiert.")
else:
    print("\nAlle Koordinaten OK.")
