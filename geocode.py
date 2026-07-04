import json, urllib.request, time, urllib.parse

PLACES = {
    "B7 Frienstedt–Gamstädt": "B7 Frienstedt, Erfurt",
    "Gothaer Platz": "Gothaer Platz, Erfurt",
    "B4 AS Gispersleben": "Gispersleben, Erfurt",
    "Blumenstraße": "Blumenstraße, Erfurt",
    "Geratalstraße (Bischleben)": "Geratalstraße, Erfurt",
    "Ortseingang Bindersleben": "Bindersleben, Erfurt",
    "Clara-Zetkin-Straße": "Clara-Zetkin-Straße, Erfurt",
    "Winzerstraße": "Winzerstraße, Erfurt",
    "Binderslebener Landstr. (Höhe Friedhof)": "Hauptfriedhof, Erfurt",
    "Schmira (abgeriegelt)": "Schmira, Erfurt",
    "Gottstedter Str. / Neue Alacher Chaussee": "Gottstedt, Erfurt",
    "K14 / Bindersleben": "Bindersleben, Erfurt",
    "Messe-Vorplatz": "Messe Erfurt",
    "Brühler Herrenberg": "Brühler Herrenberg, Erfurt",
    "Wartburgstraße / Creuzburgweg": "Wartburgstraße, Erfurt",
    "Cyriakstraße / Ecke Espachstraße": "Cyriakstraße, Erfurt",
    "Eisenacher Str. / Gothaer Str.": "Eisenacher Straße, Erfurt",
    "A71 Höhe Gottstedt": "Gottstedt, Erfurt",
    "A71 Höhe Gispersleben (Sitzblockade)": "Gispersleben, Erfurt",
    "Erfurter Kreuz / A71": "Erfurter Kreuz, Erfurt",
}

coords = {}
for name, query in PLACES.items():
    try:
        q = urllib.parse.quote(query)
        url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'ErfurtLagekarte/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data:
            coords[name] = (float(data[0]['lat']), float(data[0]['lon']))
            print(f"OK  {name}: {coords[name]}")
        else:
            print(f"MISS {name}")
    except Exception as e:
        print(f"ERR {name}: {e}")
    time.sleep(1.5)

# Now update the JSON
with open(r'C:\Users\tomri\Desktop\ISATIS\blockaden-data.json', 'r', encoding='utf-8') as f:
    js = json.load(f)

updated = 0
for b in js['blockaden']:
    if b['name'] in coords:
        old = (b['lat'], b['lon'])
        b['lat'], b['lon'] = coords[b['name']]
        print(f"FIX {b['name']}: {old} -> {coords[b['name']]}")
        updated += 1

js['stand'] = '2026-07-04T14:05:00+02:00'

with open(r'C:\Users\tomri\Desktop\ISATIS\blockaden-data.json', 'w', encoding='utf-8') as f:
    json.dump(js, f, ensure_ascii=False, indent=2)

print(f"\nUpdated {updated} locations. Committing...")
