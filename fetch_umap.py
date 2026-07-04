"""Fetch uMap data and save as JSON for the map overlay."""
import json, urllib.request, sys
from datetime import datetime, timezone, timedelta

MAP_ID = "1428416"
LAYERS = {
    "blockadepunkte": "17bc6971-46c1-40a0-9008-1567c1b06f0e",
    "versammlungen": "25a07815-f9c3-4858-8472-0c3b040008d6",
}

all_features = []

for name, layer_id in LAYERS.items():
    url = f"https://umap.openstreetmap.fr/en/datalayer/{MAP_ID}/{layer_id}/"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'ErfurtMap/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        feats = data.get('features', data.get('data', {}).get('features', []))
        for f in feats:
            f['properties']['_layer'] = name
        all_features.extend(feats)
        print(f"{name}: {len(feats)} Features")
    except Exception as e:
        print(f"{name}: ERROR {e}", file=sys.stderr)

now = datetime.now(timezone(timedelta(hours=2))).strftime("%Y-%m-%dT%H:%M:%S%z")
# Insert colon in timezone offset: +0200 -> +02:00
now = now[:-2] + ":" + now[-2:]

output = {
    "type": "FeatureCollection",
    "features": all_features,
    "source": "https://umap.openstreetmap.fr/en/map/online-aktionskarte_1428416",
    "stand": now,
    "note": "Geplante Maßnahmen der Gegenseite (uMap Online-Aktionskarte)"
}

with open(r'C:\Users\tomri\Desktop\ISATIS\umap-data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nTotal: {len(all_features)} Features → umap-data.json")
