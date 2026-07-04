"""EINMALIGE Komplett-Geokodierung ALLER Orte. Output: coordinates.json als SINGLE SOURCE OF TRUTH."""
import json, urllib.request, urllib.parse, time

PLACES = [
    "Messe Erfurt",
    "Gothaer Platz, Erfurt",
    "Blumenstraße, Erfurt",
    "Clara-Zetkin-Straße, Erfurt",
    "Geratalstraße, Erfurt",
    "Winzerstraße, Erfurt",
    "Binderslebener Landstraße, Erfurt",
    "Hauptfriedhof, Erfurt",
    "Schmira, Erfurt",
    "Brühler Herrenberg, Erfurt",
    "Wartburgstraße, Erfurt",
    "Cyriakstraße, Erfurt",
    "Eisenacher Straße, Erfurt",
    "Domplatz, Erfurt",
    "Anger, Erfurt",
    "Willy-Brandt-Platz, Erfurt",
    "Petersberg, Erfurt",
    "Bahnhof Erfurt",
    "Frienstedt, Erfurt",
    "Bindersleben, Erfurt",
    "Gispersleben, Erfurt",
    "Gottstedt, Erfurt",
    "Alach, Erfurt",
    "Bischleben, Erfurt",
    "Molsdorf, Erfurt",
    "Stotternheim, Erfurt",
    "Mittelhausen, Erfurt",
    "Hohenwinden, Erfurt",
    "Erfurter Kreuz",
]

coords = {}
for place in PLACES:
    try:
        q = urllib.parse.quote(place)
        url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'ErfurtGeocoder/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data:
            lat, lon = float(data[0]['lat']), float(data[0]['lon'])
            coords[place] = [round(lat, 5), round(lon, 5)]
            print(f"OK  {place}: {coords[place]}")
        else:
            print(f"MISS {place}")
    except Exception as e:
        print(f"ERR {place}: {e}")
    time.sleep(1.2)

# Add manual overrides for known-correct locations
coords["Messe Erfurt (manuell)"] = [50.939, 10.989]
coords["Messe-Vorplatz"] = [50.95932, 10.98967]

with open(r'C:\Users\tomri\Desktop\ISATIS\coordinates.json', 'w', encoding='utf-8') as f:
    json.dump(coords, f, ensure_ascii=False, indent=2)

print(f"\n{len(coords)} Orte geokodiert → coordinates.json")
