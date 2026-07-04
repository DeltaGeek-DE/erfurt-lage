import json, urllib.request, urllib.parse, time

with open(r'C:\Users\tomri\Desktop\ISATIS\blockaden-data.json', 'r', encoding='utf-8') as f:
    js = json.load(f)

print('=== ALLE BLOCKADEN GEGEN NOMINATIM ===')
fixed_count = 0

for b in js['blockaden']:
    current = (b['lat'], b['lon'])
    name = b['name']
    try:
        q = urllib.parse.quote(name + ", Erfurt")
        url = 'https://nominatim.openstreetmap.org/search?q=' + q + '&format=json&limit=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'ErfurtCheck/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data:
            real = (float(data[0]['lat']), float(data[0]['lon']))
            dlat = (current[0] - real[0]) * 111000
            dlon = (current[1] - real[1]) * 71000
            dist_m = int((dlat**2 + dlon**2)**0.5)
            if dist_m > 500:
                print('FIX ' + name + ': ' + str(current) + ' -> ' + str(real) + ' (' + str(dist_m) + 'm off)')
                b['lat'], b['lon'] = real
                fixed_count += 1
            else:
                print('OK  ' + name + ' (' + str(dist_m) + 'm)')
        else:
            print('?   ' + name + ': Nominatim found nothing')
    except Exception as e:
        print('ERR ' + name + ': ' + str(e))
    time.sleep(1.2)

if fixed_count > 0:
    with open(r'C:\Users\tomri\Desktop\ISATIS\blockaden-data.json', 'w', encoding='utf-8') as f:
        json.dump(js, f, ensure_ascii=False, indent=2)
    print('\n' + str(fixed_count) + ' Koordinaten korrigiert und gespeichert.')
else:
    print('\nAlle Koordinaten innerhalb 500m Toleranz.')
