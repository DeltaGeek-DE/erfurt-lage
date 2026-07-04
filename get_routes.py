"""Holt echte Straßen-Geometrien per Overpass API via curl."""
import json, subprocess, math, sys

def overpass_query(query):
    """Execute Overpass QL via curl (reliable)."""
    cmd = ['curl', '-s', '--max-time', '20',
           '-H', 'Accept: application/json',
           '--data-urlencode', f'data={query}',
           'https://overpass-api.de/api/interpreter']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    if result.returncode != 0:
        raise Exception(f"curl failed: {result.stderr}")
    return json.loads(result.stdout)

def assemble_route(segments):
    """Assemble many OSM way segments into one continuous line."""
    if not segments:
        return None

    # Build endpoint→segment index map
    endpoints = {}
    for i, seg in enumerate(segments):
        s = tuple(round(x,5) for x in seg[0])
        e = tuple(round(x,5) for x in seg[-1])
        endpoints.setdefault(s, []).append((i, 'start'))
        endpoints.setdefault(e, []).append((i, 'end'))

    used = set()
    routes = []

    for i in range(len(segments)):
        if i in used: continue
        route = list(segments[i])
        used.add(i)
        growing = True
        while growing:
            growing = False
            last = tuple(round(x,5) for x in route[-1])
            for j, pos in endpoints.get(last, []):
                if j not in used:
                    seg = segments[j]
                    route.extend(seg[1:] if pos == 'start' else reversed(seg[:-1]))
                    used.add(j)
                    growing = True
                    break
        routes.append(route)

    routes.sort(key=len, reverse=True)
    longest = routes[0]

    # Remove consecutive duplicates
    cleaned = [longest[0]]
    for pt in longest[1:]:
        if pt != cleaned[-1]:
            cleaned.append(pt)

    # Simplify to ~80 points
    if len(cleaned) > 100:
        step = len(cleaned) // 80
        simplified = [cleaned[0]]
        for k in range(step, len(cleaned)-1, step):
            simplified.append(cleaned[k])
        simplified.append(cleaned[-1])
    else:
        simplified = cleaned

    return [[round(p[0],5), round(p[1],5)] for p in simplified]


def get_highway(highway_ref, south, west, north, east):
    query = f'[out:json];(way({south},{west},{north},{east})[highway=motorway][ref="{highway_ref}"];);out geom;'
    result = overpass_query(query)
    segments = []
    for e in result.get('elements', []):
        if 'geometry' in e and len(e['geometry']) >= 2:
            segments.append([[c['lat'], c['lon']] for c in e['geometry']])

    if not segments:
        print(f"  {highway_ref}: 0 Segmente!", file=sys.stderr)
        return None

    route = assemble_route(segments)
    print(f"  {highway_ref}: {len(segments)} Segmente → {len(route)} Punkte", file=sys.stderr)
    return route


if __name__ == '__main__':
    # A71 Erfurt
    a71 = get_highway('A 71', 50.90, 10.93, 51.05, 11.05)
    if a71:
        print("A71:", json.dumps(a71))

    # B7 Frienstedt-Gamstaedt
    b7 = get_highway('B 7', 50.946, 10.86, 50.955, 10.92)
    if b7:
        print("B7:", json.dumps(b7))
