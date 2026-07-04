"""Rebuild and fix the JSON file."""
import json

path = r'C:\Users\tomri\Desktop\ISATIS\blockaden-data.json'

# Read raw, normalize line endings
with open(path, 'r', encoding='utf-8', newline=None) as f:
    text = f.read()

# Normalize \r\n to \n
text = text.replace('\r\n', '\n').replace('\r', '\n')

# Write back with \n line endings
with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print("Normalized line endings.")

# Now try parsing
try:
    with open(path, 'r', encoding='utf-8') as f:
        js = json.load(f)
    print(f"VALID! Blockaden: {len(js['blockaden'])}, Events: {len(js.get('events',[]))}, Keys: {list(js.keys())}")
    print(f"Stand: {js['stand']}")
    print(f"lage_gesamt[:60]: {js['lage_gesamt'][:60]}")
    print(f"strassen_abschnitte[0].name: {js['strassen_abschnitte'][0]['name']}")
    
    # Check for Brühler duplicates
    bruehler_blockaden = [b for b in js['blockaden'] if 'brühler' in b['name'].lower()]
    bruehler_events = [e for e in js.get('events',[]) if 'brühler' in e['name'].lower()]
    print(f"Brühler in blockaden: {len(bruehler_blockaden)}")
    print(f"Brühler in events: {len(bruehler_events)}")
    for b in bruehler_blockaden + bruehler_events:
        print(f"  - {b['name']} (typ={b['typ']})")
        
except json.JSONDecodeError as e:
    print(f"STILL INVALID: {e}")
    lines = text.split('\n')
    for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+3)):
        marker = '>>>' if i+1 == e.lineno else '   '
        print(f"{marker} L{i+1}: {lines[i][:150]}")
