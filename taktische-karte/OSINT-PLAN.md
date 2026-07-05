# OSINT-Modul — Vollständiger technischer Plan

## 0. Ziel

Ein Recherche-Modul für die Taktische Karte zur Erfassung und Analyse von Personen, Organisationen und Orten mittels Open Source Intelligence (OSINT). Zwei Modi:

- **KI-Modus**: Agent recherchiert selbstständig von Social-Media-Profilen
- **Manueller Modus**: Anwender trägt Daten selbst ein (inkl. Medien-Upload)

Alles lokal, DSGVO-konform, kein externer Datenverkehr außer den vom Anwender explizit beauftragten Web-Recherchen.

---

## 1. Architektur

```
server.py (Port 8765)
├── GET  /osint                    → osint.html (Recherche-Oberfläche)
├── GET  /osint-results            → osint-results.html (Ergebnis-Seite)
├── GET  /osint/data               → osint-data.json ausliefern
├── POST /osint/save               → Person speichern/aktualisieren
├── DELETE /osint/delete?id=...    → Person löschen
├── POST /osint/upload             → Medien-Upload (Screenshot)
├── POST /osint/start              → KI-Recherche starten (Agent)
├── GET  /osint/progress           → SSE-Stream (Live-Fortschritt)
├── GET  /osint/media/{file}       → Gespeicherte Medien ausliefern
└── POST /osint/export             → Einzelperson/alle als JSON exportieren

osint.py (KI-Agent)
├── search_profile(url)            → Profilseite parsen (web_extract)
├── find_locations(name)           → Ortsbezüge suchen (web_search)
├── find_relations(name)           → Soziales Umfeld (web_search)
├── find_posts(name)               → Letzte Aktivitäten (web_search)
├── assess_risk(person)            → Risikobewertung generieren
└── generate_report(person)        → Zusammenfassung als HTML
```

### Datenfluss

```
                       ┌──────────────┐
Anwender fügt URL ──▶  │ osint.html   │
                       └──────┬───────┘
                              │
                    KI verfügbar?
                     │         │
                   JA        NEIN
                     │         │
                     ▼         ▼
              ┌──────────┐  ┌──────────────┐
              │ osint.py │  │ Formular      │
              │ (Agent)  │  │ (manuell)     │
              └────┬─────┘  └──────┬───────┘
                   │               │
                   ▼               ▼
              ┌──────────────────────────┐
              │ osint-data.json          │
              │ (Persistenz, localStorage│
              │  + Server-Datei)          │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ osint-results.html       │
              │ (Ergebnis-Darstellung)   │
              └──────────────────────────┘
```

---

## 2. Datenmodell

```json
{
  "version": 1,
  "stand": "2026-07-05T12:00:00Z",
  "personen": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Max Mustermann",
      "alias": ["@MaxMuster", "Maximilian", "MusterMax"],
      "organisation": "DemoGruppe Erfurt",
      "profile_urls": [
        {"plattform": "x", "url": "https://x.com/MaxMuster"},
        {"plattform": "facebook", "url": "https://facebook.com/max.muster.123"}
      ],
      "bewertung": {
        "stufe": 2,
        "skala": [1,5],
        "kategorien": {
          "gewalttätigkeit": 1,
          "organisationsgrad": 3,
          "mobilität": 4,
          "vernetzung": 3
        },
        "begründung": "Wiederholt bei friedlichen Blockaden gesichtet. Keine Gewaltdelikte bekannt. Gut vernetzt in lokaler Szene."
      },
      "besuchte_orte": [
        {
          "lat": 50.97135,
          "lon": 11.01139,
          "name": "Gothaer Platz",
          "häufigkeit": "regelmäßig",
          "letzter_besuch": "2026-07-04",
          "kontext": "Blockade-Teilnahme"
        },
        {
          "lat": 50.97781,
          "lon": 11.02938,
          "name": "Fischmarkt",
          "häufigkeit": "einmalig",
          "letzter_besuch": "2026-07-05",
          "kontext": "Fahrrad-Demo"
        }
      ],
      "beziehungen": [
        {
          "ziel_id": "b2c3d4e5-...",
          "ziel_name": "Anna Schmidt",
          "typ": "bekannt",
          "kontext": "Gemeinsame Demo-Teilnahmen"
        }
      ],
      "posts": [
        {
          "plattform": "x",
          "datum": "2026-07-04T08:30:00Z",
          "inhalt": "Heute #EF0407! Treffpunkt 9 Uhr am Hauptbahnhof.",
          "url": "https://x.com/MaxMuster/status/123456"
        },
        {
          "plattform": "x",
          "datum": "2026-07-03T22:15:00Z",
          "inhalt": "Blockade-Material besorgt. #NoAfD",
          "url": "https://x.com/MaxMuster/status/123455"
        }
      ],
      "notizen": "Trägt meist schwarze Kleidung, rote Fahne. Ca. 25-30 Jahre alt.",
      "medien": [
        {
          "pfad": "osint/media/a1b2c3d4/screenshot1.jpg",
          "beschreibung": "Profilbild X",
          "datum": "2026-07-05",
          "größe": 245760
        },
        {
          "pfad": "osint/media/a1b2c3d4/vorort.jpg",
          "beschreibung": "Vor-Ort-Aufnahme Gothaer Platz",
          "datum": "2026-07-04",
          "größe": 1048576
        }
      ],
      "quellen": [
        {"typ": "web_extract", "url": "https://x.com/MaxMuster", "datum": "2026-07-05"},
        {"typ": "web_search", "query": "Max Mustermann Erfurt Demo", "datum": "2026-07-05"},
        {"typ": "manuell", "bearbeiter": "Einsatzleiter", "datum": "2026-07-05"}
      ],
      "recherche_stand": "2026-07-05T12:00:00Z",
      "recherche_modus": "ki",
      "tags": ["demo", "erfurt", "wiederholungstäter"],
      "priorität": "mittel"
    }
  ],
  "organisationen": [
    {
      "id": "org-1234-...",
      "name": "DemoGruppe Erfurt",
      "alias": ["DGE"],
      "mitglieder": ["a1b2c3d4-..."],
      "standorte": [{"lat": 50.97, "lon": 11.01, "name": "Erfurt Zentrum"}],
      "bewertung": {"stufe": 3, "...": "..."},
      "notizen": "..."
    }
  ]
}
```

### Typen-Definition (Python/Pydantic-Modell)

```python
from typing import Literal, Optional
from uuid import uuid4

class Bewertung:
    stufe: int  # 1-5
    kategorien: dict  # {"gewalttätigkeit": 1-5, ...}
    begründung: str

class Ort:
    lat: float
    lon: float
    name: str
    häufigkeit: Literal["einmalig", "gelegentlich", "regelmäßig", "ständig"]
    letzter_besuch: str  # ISO-Datum
    kontext: str

class Beziehung:
    ziel_id: str
    ziel_name: str
    typ: Literal["familie", "freund", "bekannt", "organisation", "feind"]
    kontext: str

class Post:
    plattform: Literal["x", "facebook", "instagram", "telegram", "andere"]
    datum: str
    inhalt: str
    url: Optional[str]

class Medium:
    pfad: str
    beschreibung: str
    datum: str
    größe: int

class Person:
    id: str = uuid4()
    name: str
    alias: list[str]
    organisation: Optional[str]
    profile_urls: list[dict]
    bewertung: Bewertung
    besuchte_orte: list[Ort]
    beziehungen: list[Beziehung]
    posts: list[Post]
    notizen: str
    medien: list[Medium]
    quellen: list[dict]
    recherche_stand: str
    recherche_modus: Literal["ki", "manuell", "gemischt"]
    tags: list[str]
    priorität: Literal["niedrig", "mittel", "hoch", "kritisch"]
```

---

## 3. Benutzeroberfläche

### 3.1 osint.html — Recherche-Oberfläche

Drei Tabs:

```
┌─ Tab "🔍 Profil" ────────────────────────────────┐
│                                                     │
│  🔗 Link einfügen:                                  │
│  ┌─────────────────────────────────────────────┐   │
│  │ https://x.com/MaxMuster               [➕]  │   │
│  │ https://facebook.com/max.muster        [✕]  │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─ KI-Recherche ─────────────────────────────┐   │
│  │ [▶ Recherche starten]                       │   │
│  │ ████████████░░░░ 75%                        │   │
│  │ ✅ Profil analysiert                        │   │
│  │ ✅ Posts durchsucht                         │   │
│  │ ⏳ Orte recherchieren...                    │   │
│  │ ⏸ Beziehungen analysieren                  │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─ Manuelle Eingabe ──────────────────────────┐   │
│  │ Name:        [Max Mustermann          ]      │   │
│  │ Alias:       [@MaxMuster] [Maximilian] [➕]│   │
│  │ Organisation:[DemoGruppe Erfurt       ]      │   │
│  │ Priorität:   [Mittel ▼]                      │   │
│  │ Tags:        [demo] [erfurt] [➕]            │   │
│  │                                              │   │
│  │ 📍 Besuchte Orte:                            │   │
│  │  Gothaer Platz (regelmäßig)           [✕]   │   │
│  │  Fischmarkt (einmalig)                [✕]   │   │
│  │  [+ Ort hinzufügen (Karte)]                  │   │
│  │                                              │   │
│  │ 👥 Beziehungen:                              │   │
│  │  ↭ Anna Schmidt (bekannt)             [✕]   │   │
│  │  [+ Beziehung hinzufügen]                    │   │
│  │                                              │   │
│  │ [💾 Speichern]  [🗑 Löschen]                │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘

┌─ Tab "📋 Datenbank" ───────────────────────────────┐
│                                                     │
│  🔍 [Suchen...]    [Filter: Alle ▼]                │
│                                                     │
│  ┌─ Max Mustermann ────────────────────────────┐   │
│  │ ⚠️ Risiko 2/5 | @MaxMuster | DemoGruppe      │   │
│  │ Orte: 2 | Beziehungen: 1 | Posts: 2         │   │
│  │ Letzte Recherche: 5.7.2026 (KI)              │   │
│  │ [Öffnen] [Exportieren] [Löschen]             │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌─ Anna Schmidt ──────────────────────────────┐   │
│  │ ⚠️ Risiko 1/5 | @AnnaS | —                  │   │
│  │ Orte: 0 | Beziehungen: 1 | Posts: 0         │   │
│  │ Letzte Recherche: 5.7.2026 (manuell)         │   │
│  │ [Öffnen] [Exportieren] [Löschen]             │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘

┌─ Tab "📤 Export" ───────────────────────────────────┐
│                                                     │
│  Format: [JSON ▼]  [CSV ▼]  [PDF-Bericht ▼]       │
│  Umfang: [Alle ▼] [Nur Markierte ▼]                │
│                                                     │
│  [📤 Exportieren]                                   │
│  [📥 Importieren (JSON)]                            │
└─────────────────────────────────────────────────────┘
```

### 3.2 osint-results.html — Ergebnis-Seite

Eigenständige Seite, über Direktlink oder aus Datenbank aufrufbar:

```
┌──────────────────────────────────────────────────────┐
│  🔍 OSINT: Max Mustermann                            │
│  ID: a1b2c3d4 | Recherche: KI | 5.7.2026            │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌─ Profil ──────────────────────────────────────┐   │
│  │ 📛 Name:     Max Mustermann                    │   │
│  │ 🏷 Alias:     @MaxMuster, Maximilian           │   │
│  │ 🏢 Org:      DemoGruppe Erfurt                 │   │
│  │ 🏷 Priorität: Mittel                           │   │
│  │ 🏷 Tags:      #demo #erfurt                    │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌─ ⚠️ Risikobewertung ──────────────────────────┐   │
│  │ Gesamt: ●●○○○ (2/5)                            │   │
│  │                                                 │   │
│  │ Gewalttätigkeit  ●○○○○ (1/5)                    │   │
│  │ Organisationsgrad ●●●○○ (3/5)                   │   │
│  │ Mobilität        ●●●●○ (4/5)                    │   │
│  │ Vernetzung       ●●●○○ (3/5)                    │   │
│  │                                                 │   │
│  │ Wiederholt bei friedlichen Blockaden gesichtet. │   │
│  │ Keine Gewaltdelikte bekannt. Gut vernetzt in    │   │
│  │ lokaler Szene.                                  │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌─ 📍 Besuchte Orte ────────────────────────────┐   │
│  │ 🗺 [Mini-Karte mit Markern]                    │   │
│  │                                                 │   │
│  │ Gothaer Platz (50.971, 11.011)                  │   │
│  │   ▸ Regelmäßig | Letzter: 4.7.2026             │   │
│  │   ▸ Blockade-Teilnahme                         │   │
│  │                                                 │   │
│  │ Fischmarkt (50.978, 11.029)                     │   │
│  │   ▸ Einmalig | Letzter: 5.7.2026               │   │
│  │   ▸ Fahrrad-Demo                               │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌─ 👥 Beziehungen ──────────────────────────────┐   │
│  │                                                 │   │
│  │  Max Mustermann ─── bekannt ──▶ Anna Schmidt   │   │
│  │  Gemeinsame Demo-Teilnahmen                    │   │
│  │                                                 │   │
│  │ [Beziehungs-Graph anzeigen]                    │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌─ 📝 Posts & Aktivitäten ──────────────────────┐   │
│  │                                                 │   │
│  │ 🐦 4.7.2026 08:30 — X                          │   │
│  │ "Heute #EF0407! Treffpunkt 9 Uhr am Hbf."     │   │
│  │ 🔗 https://x.com/MaxMuster/status/123456       │   │
│  │                                                 │   │
│  │ 🐦 3.7.2026 22:15 — X                          │   │
│  │ "Blockade-Material besorgt. #NoAfD"            │   │
│  │ 🔗 https://x.com/MaxMuster/status/123455       │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌─ 📝 Notizen ──────────────────────────────────┐   │
│  │ Trägt meist schwarze Kleidung, rote Fahne.     │   │
│  │ Ca. 25-30 Jahre alt.                           │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌─ 🖼 Medien (2) ───────────────────────────────┐   │
│  │ [Profilbild X]  [Vor-Ort-Aufnahme]            │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌─ 📚 Quellen ──────────────────────────────────┐   │
│  │ 🌐 web_extract: https://x.com/MaxMuster        │   │
│  │ 🔍 web_search: "Max Mustermann Erfurt Demo"    │   │
│  │ ✏️ manuell: Einsatzleiter (5.7.2026)           │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  [✏️ Bearbeiten] [🗑 Löschen] [📤 Exportieren]     │
└──────────────────────────────────────────────────────┘
```

### 3.3 Mini-Karte (eingebettet in osint-results.html)

Eine Leaflet-Instanz (ca. 400×300px) zeigt alle besuchten Orte als Marker. Kein eigener Layer-Switcher — nur die Marker der Person. Klick auf Marker zeigt Kontext.

---

## 4. KI-Agent (osint.py)

### 4.1 Ablauf

```python
def recherchiere_person(urls: list[str]) -> dict:
    person = {"id": str(uuid4())}

    # SCHRITT 1: Profil extrahieren
    for url in urls:
        plattform = erkenne_plattform(url)  # "x", "facebook", "instagram"
        profil_html = web_extract(url)
        person['name'] = extrahiere_name(profil_html)
        person['alias'].append(extrahiere_handle(profil_html))
        # SSE: {"step": 1, "status": "ok", "text": "Profil analysiert"}

    # SCHRITT 2: Posts durchsuchen
    suchbegriff = f"site:{plattform_domain} {person['name']} {person['alias'][0]}"
    posts = web_search(suchbegriff, limit=10)
    for post in posts:
        inhalt = web_extract(post['url'])
        person['posts'].append(extrahiere_post(inhalt))
    # SSE: {"step": 2, "status": "ok", "text": "10 Posts gefunden"}

    # SCHRITT 3: Ortsbezüge finden
    orte = web_search(f"{person['name']} {STANDORT}", limit=5)
    # Ortsnamen per NER (Named Entity Recognition) aus Suchergebnissen extrahieren
    # ODER: Nach konkreten Städtenamen im Post-Inhalt suchen
    for ort in orte:
        koord = geocode(ort)  # Nominatim
        person['besuchte_orte'].append({...})
    # SSE: {"step": 3, "status": "ok", "text": "3 Orte identifiziert"}

    # SCHRITT 4: Beziehungen analysieren
    freunde = web_search(f"{person['name']} Freund Kontakt", limit=5)
    # Aus Post-Texten: "@Erwähnungen" extrahieren
    erwähnungen = extrahiere_erwähnungen(person['posts'])
    for erw in erwähnungen:
        person['beziehungen'].append({...})
    # SSE: {"step": 4, "status": "ok", "text": "2 Beziehungen gefunden"}

    # SCHRITT 5: Risikobewertung
    person['bewertung'] = bewerte(person)
    # Sucht nach Keywords: "Gewalt", "Festnahme", "Waffe", "Haftbefehl"
    # Prüft Posting-Frequenz, Organisationsgrad, geografische Reichweite
    # SSE: {"step": 5, "status": "ok", "text": "Risikobewertung erstellt"}

    # SCHRITT 6: Bericht generieren
    person['recherche_stand'] = jetzt()
    person['recherche_modus'] = "ki"
    return person
```

### 4.2 Erkennungslogik

```python
def erkenne_plattform(url: str) -> str:
    if "x.com" in url or "twitter.com" in url:
        return "x"
    if "facebook.com" in url:
        return "facebook"
    if "instagram.com" in url:
        return "instagram"
    if "t.me" in url or "telegram" in url:
        return "telegram"
    if "linkedin.com" in url:
        return "linkedin"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return "andere"

def extrahiere_handle(html: str) -> str:
    # @Handle aus Profilseite extrahieren
    import re
    match = re.search(r'@(\w+)', html)
    return match.group(1) if match else ""

def extrahiere_erwähnungen(posts: list[dict]) -> list[str]:
    handles = set()
    for post in posts:
        handles.update(re.findall(r'@(\w+)', post['inhalt']))
    return list(handles)

def bewerte(person: dict) -> dict:
    # Keyword-basierte Risikoanalyse
    gewalt_kw = ["gewalt", "waffe", "messer", "schlag", "kampf", "polizei",
                 "festnahme", "verletzt", "blut", "angriff", "militant"]
    organisation_kw = ["orga", "treffen", "planung", "mobilisierung",
                       "koordination", "gruppe", "kollektiv"]
    mobilität_kw = ["reise", "anreise", "zug", "bus", "auto", "überregional",
                    "bundesweit", "auswärts"]

    gewalt_score = sum(1 for kw in gewalt_kw if kw in str(person).lower())
    org_score = sum(1 for kw in organisation_kw if kw in str(person).lower())
    mob_score = sum(1 for kw in mobilität_kw if kw in str(person).lower())

    return {
        "stufe": min(5, max(1, (gewalt_score + org_score + mob_score) // 3)),
        "kategorien": {
            "gewalttätigkeit": min(5, gewalt_score),
            "organisationsgrad": min(5, org_score),
            "mobilität": min(5, mob_score),
            "vernetzung": min(5, len(person.get('beziehungen', [])))
        },
        "begründung": "Automatisch generierte Bewertung basierend auf "
                      f"{len(person.get('posts',[]))} Posts und "
                      f"{len(person.get('besuchte_orte',[]))} Orten."
    }
```

### 4.3 Steuerung

```python
class OSINTAgent:
    def __init__(self):
        self.state = "idle"  # idle, running, paused, error, done
        self.steps = []
        self.current_step = 0
        self.progress = 0
        self.result = None

    def start(self, urls, ort_name):
        self.state = "running"
        self.steps = [
            "Profil analysieren",
            "Posts durchsuchen",
            "Orte recherchieren",
            "Beziehungen analysieren",
            "Risikobewertung",
            "Bericht erstellen"
        ]
        # ... führt Schritte sequenziell aus

    def pause(self):
        self.state = "paused"

    def resume(self):
        self.state = "running"

    def stop(self):
        self.state = "idle"
```

---

## 5. Server-Endpunkte (Erweiterung server.py)

```python
# Neuer Handler-Zweig in do_GET / do_POST

def do_GET(self):
    if self.path == '/osint':
        self.serve_file('app/osint.html', 'text/html')
        return

    if self.path == '/osint-results':
        self.serve_file('app/osint-results.html', 'text/html')
        return

    if self.path == '/osint/data':
        data = load_json('app/data/osint-data.json')
        self.json_response(data)
        return

    if self.path.startswith('/osint/media/'):
        # Sicherheits-Check: Pfad-Traversal verhindern
        filename = self.path.split('/osint/media/')[1]
        safe_path = os.path.join(DATA_DIR, 'osint', 'media', filename)
        if os.path.exists(safe_path):
            self.serve_file(safe_path, 'image/jpeg')
        return

    if self.path == '/osint/progress':
        # SSE-Stream
        self.sse_response(osint_agent)
        return

def do_POST(self):
    if self.path == '/osint/save':
        body = self.read_json()
        data = load_json('app/data/osint-data.json')
        person = body['person']
        # Update oder Insert
        idx = find_index(data['personen'], person['id'])
        if idx >= 0:
            data['personen'][idx] = person
        else:
            data['personen'].append(person)
        save_json('app/data/osint-data.json', data)
        self.json_response({"status": "ok", "id": person['id']})
        return

    if self.path == '/osint/delete':
        person_id = self.query_params.get('id', '')
        data = load_json('app/data/osint-data.json')
        data['personen'] = [p for p in data['personen'] if p['id'] != person_id]
        save_json('app/data/osint-data.json', data)
        self.json_response({"status": "ok"})
        return

    if self.path == '/osint/upload':
        # Multipart-Form: Bild-Upload
        content_type = self.headers.get('Content-Type', '')
        if 'multipart/form-data' in content_type:
            # Parse multipart, speichere Datei
            filedata = self.parse_multipart()
            person_id = filedata.get('person_id', '')
            media_dir = os.path.join(DATA_DIR, 'osint', 'media', person_id)
            os.makedirs(media_dir, exist_ok=True)
            # ... speichere Datei, returniere Pfad
        return

    if self.path == '/osint/start':
        body = self.read_json()
        urls = body.get('urls', [])
        ort = body.get('ort', '')
        # Starte Agent in Thread
        thread = threading.Thread(target=osint_agent.start, args=(urls, ort))
        thread.start()
        self.json_response({"status": "started"})
        return

    if self.path == '/osint/stop':
        osint_agent.stop()
        self.json_response({"status": "stopped"})
        return

    if self.path == '/osint/export':
        person_id = self.query_params.get('id', '')
        data = load_json('app/data/osint-data.json')
        if person_id:
            person = next(p for p in data['personen'] if p['id'] == person_id)
            self.json_response(person)
        else:
            self.json_response(data)
        return
```

---

## 6. Dateien und Änderungen

| Datei | Aktion | Beschreibung |
|---|---|---|
| `app/osint.html` | **NEU** | Recherche-Oberfläche (3 Tabs) |
| `app/osint-results.html` | **NEU** | Ergebnis-Seite (Einzelperson-Detail) |
| `app/data/osint-data.json` | **NEU** | Leere initiale Struktur |
| `app/scripts/osint.py` | **NEU** | KI-Agent-Logik |
| `app/data/osint/media/` | **NEU** | Ordner für Screenshots |
| `server.py` | **UPDATE** | +12 neue Routen |
| `app/admin.html` | **UPDATE** | Tab "🔍 OSINT" verlinkt |

---

## 7. Technische Details

### 7.1 Medien-Upload

- HTML: `<input type="file" accept="image/*" multiple>`
- JS: `FormData` + `fetch POST /osint/upload`
- Server: `cgi.FieldStorage` oder manuelles Multipart-Parsing
- Speicher: `app/data/osint/media/{person_id}/` (pro Person Unterordner)
- Max-Größe: 10 MB pro Datei (server-seitig prüfen)
- Formate: JPG, PNG, WebP

### 7.2 Daten-Persistenz

- Primär: `osint-data.json` auf dem Server
- Backup: `localStorage` im Browser (automatischer Sync beim Speichern)
- Konfliktlösung: Server gewinnt (letzter `recherche_stand`)

### 7.3 Suche/Filter

- Volltextsuche über alle Felder (name, alias, notizen, tags)
- Filter: Priorität, Risikostufe, Recherche-Modus, Tags
- Sortierung: Name, Datum, Risiko (auf-/absteigend)

### 7.4 Export-Formate

- **JSON**: Vollständiger Datensatz (für Import/Backup)
- **CSV**: Flache Tabelle (Name, Alias, Risiko, Orte, Beziehungen)
- **PDF-Bericht**: Wie osint-results.html, aber als PDF (node make_pdf.js)

### 7.5 Beziehungs-Graph

- D3.js oder vis.js (optional, nur im Browser)
- Knoten = Personen, Kanten = Beziehungen
- Farbe = Risikostufe, Größe = Anzahl Beziehungen

---

## 8. DSGVO

- Keine Cloud-Speicherung — alles in `app/data/osint/`
- Medien werden NIE nach extern gesendet
- Löschung: Person löschen = alle Daten + Medien der Person weg
- Export enthält nur die angefragte Person (bzw. alle mit Einwilligung)
- Kein Tracking, keine Logs mit Personenbezug

---

## 9. Implementierungs-Reihenfolge

### Phase 1: Grundgerüst (2h)
1. `app/data/osint-data.json` — Leere Struktur
2. `server.py` — `/osint/data` GET, `/osint/save` POST, `/osint/delete` DELETE
3. `app/osint.html` — Tab "📋 Datenbank" (Liste + Suche)
4. Test: Person manuell speichern, laden, löschen

### Phase 2: Manuelle Eingabe (2h)
5. `app/osint.html` — Tab "🔍 Profil" (Formular mit allen Feldern)
6. Medien-Upload (POST `/osint/upload`)
7. Ort-Hinzufügen per Klick auf Mini-Karte
8. Beziehung-Hinzufügen (Dropdown bestehender Personen)

### Phase 3: KI-Integration (2h)
9. `app/scripts/osint.py` — Agent
10. `server.py` — `/osint/start`, `/osint/progress` (SSE)
11. `app/osint.html` — Link-Queue + Fortschrittsanzeige

### Phase 4: Ergebnis-Darstellung (1.5h)
12. `app/osint-results.html` — Detail-Seite
13. Mini-Karte mit besuchten Orten
14. Beziehungs-Graph (optional)

### Phase 5: Export & Integration (1h)
15. JSON/CSV/PDF-Export
16. Verlinkung Admin-Panel → OSINT-Tab
17. Integration in build.py + Handbuch-Update

---

## 10. Geschätzte Aufwände

| Phase | Stunden | Dateien |
|---|---|---|
| 1 Grundgerüst | 2h | 3 |
| 2 Manuelle Eingabe | 2h | 2 |
| 3 KI-Integration | 2h | 3 |
| 4 Ergebnis-Darstellung | 1.5h | 2 |
| 5 Export & Integration | 1h | 3 |
| **Gesamt** | **8.5h** | **13** |
