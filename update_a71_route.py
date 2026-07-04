import json, urllib.request

# NUR Nord- und Süd-Endpunkt der A71
NORTH = (51.0317, 10.99475)
SOUTH = (50.89937, 10.94715)

coords = f'{NORTH[1]},{NORTH[0]};{SOUTH[1]},{SOUTH[0]}'
url = f'https://router.project-osrm.org/route/v1/driving/{coords}?geometries=geojson&overview=full&alternatives=false'

print("OSRM: Nord->Süd (2 Punkte)...")
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read())

coords = data['routes'][0]['geometry']['coordinates']
route = [[round(c[1],5), round(c[0],5)] for c in coords]

print(f"Route: {len(route)} Punkte")
print(f"Start: {route[0]}, End: {route[-1]}")

# Check
lons = [p[1] for p in route]
lats = [p[0] for p in route]
print(f"Lat: {min(lats):.4f} - {max(lats):.4f}")
print(f"Lon: {min(lons):.4f} - {max(lons):.4f}")

# Check monotonic (should always go south)
reversals = sum(1 for i in range(1,len(lats)) if lats[i] > lats[i-1] + 0.0005)
print(f"Richtungswechsel: {reversals}")

# Simplify to ~200 points
step = max(1, len(route)//200)
final = [route[0]] + [route[i] for i in range(step, len(route)-1, step)] + [route[-1]]
print(f"Final: {len(final)} pts")

with open(r'C:\Users\tomri\Desktop\ISATIS\blockaden-data.json', 'r', encoding='utf-8') as f:
    js = json.load(f)
js['strassen_abschnitte'][0]['route'] = final
js['strassen_abschnitte'][0]['note'] = f'A71: OSRM Direkt-Route, {len(final)} pts, {reversals} Richtungswechsel'
with open(r'C:\Users\tomri\Desktop\ISATIS\blockaden-data.json', 'w', encoding='utf-8') as f:
    json.dump(js, f, ensure_ascii=False, indent=2)
print("OK")
