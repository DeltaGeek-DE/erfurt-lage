"""Fix coordinates in blockaden-data.json using OSM Nominatim + known-good table."""
import json, urllib.request, urllib.parse, time

GOOD = {
    'gothaer platz': (50.97135, 11.01139),
    'blumenstraße': (50.98432, 11.00614),
    'blumenstr': (50.98432, 11.00614),
    'clara-zetkin': (50.97242, 11.04254), 
    'clara zetkin': (50.97242, 11.04254),
    'frienstedt': (50.95608, 10.90877),
    'gispersleben': (51.01889, 10.99087),
    'b4': (51.01889, 10.99087),
    'geratalstraße': (50.94820, 10.99577),
    'geratalstr': (50.94820, 10.99577),
    'bischleben': (50.94820, 10.99577),
    'winzerstraße': (50.95890, 11.00043),
    'winzerstr': (50.95890, 11.00043),
    'bindersleben': (50.97452, 10.94897),
    'hauptfriedhof': (50.97294, 10.99332),
    'friedhof': (50.97294, 10.99332),
    'schmira': (50.95361, 10.97081),
    'brühler herrenberg': (50.97272, 11.00602),
    'brühler': (50.97272, 11.00602),
    'wartburgstraße': (50.96143, 11.00288),
    'wartburgstr': (50.96143, 11.00288),
    'cyriakstraße': (50.96534, 11.01026),
    'cyriakstr': (50.96534, 11.01026),
    'eisenacher': (50.95613, 10.97656),
    'messe': (50.95932, 10.98967),
    'erfurter kreuz': (50.92000, 10.96400),
    'k14': (50.97452, 10.94897),
    'gottstedter': (50.96919, 10.91043),
    'alach': (50.96919, 10.91043),
    'gottstedt': (50.96919, 10.91043),
    'stotternheim': (51.056, 11.043),
    'mittelhausen': (51.035, 11.002),
    'hohenwinden': (51.017, 11.038),
}

def geocode(query):
    try:
        q = urllib.parse.quote(f"{query}, Erfurt")
        url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'ErfurtLagekarte/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except:
        pass
    return None

with open(r'C:\Users\tomri\Desktop\ISATIS\blockaden-data.json', 'r', encoding='utf-8') as f:
    js = json.load(f)

fixed = 0
for b in js['blockaden']:
    name_lower = b['name'].lower()
    
    # Check known-good table first (substring match)
    matched = False
    for key, (glat, glon) in GOOD.items():
        if key in name_lower:
            if abs(b['lat'] - glat) > 0.001 or abs(b['lon'] - glon) > 0.001:
                old = (b['lat'], b['lon'])
                b['lat'], b['lon'] = glat, glon
                print(f"FIXED (table) {b['name']}: {old} -> ({glat}, {glon})")
                fixed += 1
            matched = True
            break
    
    # If not in table, try geocoding
    if not matched:
        result = geocode(b['name'])
        if result:
            glat, glon = result
            if abs(b['lat'] - glat) > 0.003 or abs(b['lon'] - glon) > 0.003:
                old = (b['lat'], b['lon'])
                b['lat'], b['lon'] = glat, glon
                print(f"FIXED (geo) {b['name']}: {old} -> ({glat}, {glon})")
                fixed += 1
        time.sleep(1.5)  # Nominatim rate limit

if fixed > 0:
    print(f"\nTotal fixed: {fixed}")
else:
    print("All coordinates OK — no fixes needed.")

# Don't save here — let the caller decide. Just report.
# The cronjob prompt will handle saving if fixes were made.
