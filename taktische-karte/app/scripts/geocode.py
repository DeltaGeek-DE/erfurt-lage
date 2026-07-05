"""Geocode locations using local coordinates.json or OSM Nominatim (online)."""
import json, urllib.request, urllib.parse, time, os

COORDS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'coordinates.json')

with open(COORDS_FILE, 'r', encoding='utf-8') as f:
    TRUTH = json.load(f)

def geocode(place, online=False):
    """Geocode a place. Uses local table first, optionally falls back to Nominatim."""
    key = place.lower().replace(', erfurt', '').replace(' erfurt', '').strip()
    if key in TRUTH:
        return TRUTH[key]
    if online:
        try:
            time.sleep(1.2)
            q = urllib.parse.quote(place)
            url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
            req = urllib.request.Request(url, headers={'User-Agent': 'TaktischeKarte/1.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            if data:
                lat, lon = round(float(data[0]['lat']), 5), round(float(data[0]['lon']), 5)
                TRUTH[key] = [lat, lon]
                with open(COORDS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(TRUTH, f, ensure_ascii=False, indent=2)
                return [lat, lon]
        except Exception as e:
            print(f"Geocoding error: {e}")
    return None

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        result = geocode(sys.argv[1], online='--online' in sys.argv)
        print(result if result else 'Nicht gefunden')
    else:
        print(f"{len(TRUTH)} Orte in coordinates.json")
