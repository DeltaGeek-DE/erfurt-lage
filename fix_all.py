"""Fix ALL coordinates in blockaden-data.json using coordinates.json as source of truth."""
import json, math

def dist(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2) * 111000

with open(r'C:\Users\tomri\Desktop\ISATIS\coordinates.json', 'r', encoding='utf-8') as f:
    TRUTH = json.load(f)

with open(r'C:\Users\tomri\Desktop\ISATIS\blockaden-data.json', 'r', encoding='utf-8') as f:
    js = json.load(f)

fixed = 0

def find_best(name):
    """Find best matching coordinate from TRUTH."""
    nl = name.lower()
    # Build reverse index: shorter keys are more specific
    best_key, best_coord = None, None
    for key, coord in TRUTH.items():
        kl = key.lower().replace(', erfurt', '').replace(' erfurt', '')
        # Check if any word from key appears in name
        words = kl.split()
        matches = sum(1 for w in words if w in nl)
        if matches >= 2 or (matches == 1 and len(words) == 1 and words[0] in nl):
            if best_key is None or len(key) < len(best_key):
                best_key = key
                best_coord = coord
    return best_coord

# Fix messe object
if js.get('messe'):
    truth_coord = TRUTH.get('Messe Erfurt')
    current = [js['messe']['lat'], js['messe']['lon']]
    d = dist(current, truth_coord)
    if d > 500:
        old = current
        js['messe']['lat'], js['messe']['lon'] = truth_coord[0], truth_coord[1]
        print(f"FIX messe: {old} -> {truth_coord} ({int(d)}m off)")
        fixed += 1

# Fix blockades
for b in js.get('blockaden', []):
    current = [b['lat'], b['lon']]
    best = find_best(b['name'])
    if best:
        d = dist(current, best)
        if d > 500:
            old = [b['lat'], b['lon']]
            b['lat'], b['lon'] = best[0], best[1]
            print(f"FIX blockade {b['name']}: {old} -> {best} ({int(d)}m off)")
            fixed += 1

# Fix events
for ev in js.get('events', []):
    current = [ev['lat'], ev['lon']]
    best = find_best(ev['name'])
    if best:
        d = dist(current, best)
        if d > 500:
            old = [ev['lat'], ev['lon']]
            ev['lat'], ev['lon'] = best[0], best[1]
            print(f"FIX event {ev['name']}: {old} -> {best} ({int(d)}m off)")
            fixed += 1

if fixed > 0:
    with open(r'C:\Users\tomri\Desktop\ISATIS\blockaden-data.json', 'w', encoding='utf-8') as f:
        json.dump(js, f, ensure_ascii=False, indent=2)
    print(f"\n{fixed} Koordinaten korrigiert.")
else:
    print("\nAlle Koordinaten korrekt.")
