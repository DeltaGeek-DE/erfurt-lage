# Taktische Karte — Anleitung für KI-Agenten (Hermes)

> Diese Datei wird vom KI-Agenten automatisch gelesen.
> Sie enthält alle Informationen, um eine Live-Lagekarte einzurichten und zu betreiben.

## 1. Projekt-Übersicht

Die **Taktische Karte** ist ein Dashboard zur Live-Darstellung von Ereignissen auf einer interaktiven Karte. Sie besteht aus:

- `app/index.html` — Live-Karte (Leaflet)
- `app/admin.html` — Admin-Panel (manuelle Dateneingabe per Klick)
- `app/data/blockaden-data.json` — Datenquelle (wird vom Cronjob aktualisiert)
- `app/data/coordinates.json` — Geokodierte Orte (Single Source of Truth)
- `app/scripts/fix_coords.py` — Koordinaten-Korrektur
- `app/scripts/geocode.py` — Geocoding (Offline: lokale Tabelle, Online: Nominatim)
- `server.py` — Lokaler HTTP-Server für Offline-Betrieb
- `build.py` — Release-Builder

## 2. Einrichtung

### 2.1 GitHub Pages Deployment (empfohlen)

```bash
cd app/
git init
git add .
git commit -m "Taktische Karte initial"
gh repo create MEIN_ORG/MEIN_REPO --public --source=. --push
gh api repos/MEIN_ORG/MEIN_REPO/pages --method PUT -F build_type=workflow
```

Danach ist die Karte unter `https://MEIN_ORG.github.io/MEIN_REPO/` erreichbar.

### 2.2 Datenformat

Die Datei `app/data/blockaden-data.json` hat dieses Format:

```json
{
  "stand": "2026-07-04T12:00:00+02:00",
  "blockaden": [
    {
      "name": "Gothaer Platz",
      "lat": 50.97135,
      "lon": 11.01139,
      "tn": 800,
      "typ": "gross",
      "note": "Sitzblockade"
    }
  ],
  "strassen_abschnitte": [
    {
      "name": "A71 GESPERRT",
      "route": [[50.919,10.964],[50.963,10.965]],
      "farbe": "#1a1a2e",
      "note": "Voll gesperrt"
    }
  ],
  "events": [
    {
      "name": "Abseilaktion Brücke",
      "lat": 51.035,
      "lon": 11.002,
      "typ": "abseil",
      "note": "Brücke A71"
    }
  ],
  "lage_gesamt": "Zusammenfassung der aktuellen Lage",
  "messe": {
    "lat": 50.95932,
    "lon": 10.98967,
    "status": "Parteitag läuft"
  }
}
```

**Blockaden-Typen**: `gross` (≥500 TN), `normal` (<500), `sitz`, `barrikade`

**Event-Typen**: `abseil`, `demo`, `eskalation`, `presse`

## 3. Cronjob für automatische Updates

### 3.0 Wahl: Lokal oder GitHub Pages?

| Modus | Daten | Karte | Internet |
|---|---|---|---|
| **Lokal (empfohlen)** | `localhost` | `http://localhost:8765` | Nur für News-Suche |
| **GitHub Pages** | `github.io` | Öffentlich | ❌ (Tiles offline) |

Für den **Lokal-Modus** (Standard): Die JSON wird lokal gespeichert, der Server liefert sie aus. Kein Git, kein Push.

### 3.1 Hermes Cronjob erstellen (LOKAL)

```python
cronjob(action='create',
  name='Lage-Updater',
  schedule='*/5 * * * *',
  enabled_toolsets=['web','file','terminal'],
  workdir='PFAD/ZUM/PROJEKT',
  prompt='''[Siehe Abschnitt 3.2]'''
)
```

### 3.2 Cronjob-Prompt (komplett)

```
PRÜFE ALLE EINTRÄGE. Alle 5 Minuten. NUR aktuelle Meldungen von HEUTE und MORGEN.

**REGELN**:
- DU DARFST KEINE KOORDINATEN ERFINDEN. Setze neue Einträge auf DIE_ZENTRUM_LAT/DIE_ZENTRUM_LON. fix_coords.py korrigiert danach.
- Bestehende Koordinaten NIEMALS ändern. Nur löschen oder neu hinzufügen.
- NIEMALS Zukunfts-Daten eintragen. Der Stand MUSS die aktuelle Uhrzeit sein.
- Blockaden NUR löschen wenn Quelle explizit "aufgelöst"/"beendet" sagt.
- Events löschen wenn vorbei. Name und Koordinaten nie ändern.

**WEBSEARCH** (6 Queries):
1. "Polizei EREIGNIS_ORT Blockaden aktuell DATUM"
2. "site:x.com HASHTAG OR ORT"
3. "site:x.com @POLIZEI_ACCOUNT OR @REPORTER_ACCOUNT"
4. "EREIGNIS Proteste Blockaden aufgelöst beendet DATUM"
5. "site:presseportal.de POLIZEI ORT DATUM"
6. "site:de.indymedia.org ORT DATUM"

**UPDATES**: Nur FAKTEN. Koordinaten aus coordinates.json.

**TERMINAL**: cd PFAD/ZUM/PROJEKT && python app/scripts/fix_coords.py
# KEIN git push! Daten bleiben lokal.
```

### 3.3 Platzhalter ersetzen

| Platzhalter | Beschreibung | Beispiel |
|---|---|---|
| `EREIGNIS` | Name des Ereignisses | AfD-Parteitag |
| `ORT` | Stadt/Region | Erfurt |
| `HASHTAG` | Social-Media-Hashtag | #EF0407 |
| `DATUM` | Aktuelles Datum | 4. Juli 2026 |
| `POLIZEI_ACCOUNT` | X-Account der Polizei | Polizei_Thuer |
| `REPORTER_ACCOUNT` | X-Account von Reportern vor Ort | chefreporterNRW |
| `DIE_ZENTRUM_LAT` | Breitengrad Stadtzentrum | 50.97 |
| `DIE_ZENTRUM_LON` | Längengrad Stadtzentrum | 10.99 |
| `PFAD/ZUM/PROJEKT` | Absoluter Pfad zum Projekt | C:\Users\tomri\Desktop\ISATIS |

## 4. Koordinaten-System

### 4.1 Single Source of Truth

`coordinates.json` enthält alle geokodierten Orte. Format:

```json
{
  "Gothaer Platz": [50.97135, 11.01139],
  "Messe Erfurt": [50.95932, 10.98967],
  "Erfurter Kreuz": [50.92, 10.964],
  "a71": [50.969, 10.965]
}
```

**Wichtig**: Autobahn-Namen als Keys hinzufügen (a71, a4, b7) — Events mit "A71" im Namen werden dann automatisch korrigiert.

### 4.2 Neue Orte geokodieren

```bash
# Lokal (aus coordinates.json)
python app/scripts/geocode.py "Gothaer Platz"

# Online (mit Nominatim-Fallback)
python app/scripts/geocode.py "Unbekannter Ort" --online
```

### 4.3 fix_coords.py

Läuft nach jedem Cronjob-Update. Erzwingt ALLE Koordinaten aus `coordinates.json` — keine Toleranz, nur Überschreiben.

## 5. Offline-Betrieb

```bash
python server.py
# → http://localhost:8765
# → Admin: http://localhost:8765/admin.html
```

Die Karte lädt Leaflet und MarkerCluster aus `app/assets/` — kein CDN nötig.
Der Font fällt auf System-Monospace zurück wenn offline.

## 6. Straßen-Routing (optional)

Für gesperrte Straßenabschnitte:

1. Overpass API: `way(bbox)[highway=motorway][ref="A 71"];out geom;`
2. Nördlichsten + südlichsten Punkt als OSRM-Endpunkte
3. Route mit genau 2 Punkten → 0 Richtungswechsel

⚠️ Mehr als 2 Via-Punkte erzeugen Loops.

## 7. uMap / IndyMedia Integration

```bash
python fetch_umap.py   # Lädt externe uMap-Daten
```

Die Daten landen in `umap-data.json` und werden als ⚑ Overlay auf der Karte dargestellt.

## 8. Gateway (optional, für persistenten Cronjob)

```bash
hermes gateway install   # Installiert als Windows-Dienst
hermes gateway start     # Startet den Dienst
```

Ohne Gateway läuft der Cronjob nur, wenn die Hermes-App offen ist.

## 9. Prüfliste für KI-Agenten

- [ ] `coordinates.json` mit Stadtzentrum + allen relevanten Orten befüllen
- [ ] `blockaden-data.json` initialisieren (leer oder mit ersten Daten)
- [ ] GitHub Repo erstellen + Pages aktivieren
- [ ] Hermes Cronjob mit Prompt (Abschnitt 3.2) einrichten
- [ ] Platzhalter im Prompt ersetzen (Abschnitt 3.3)
- [ ] Gateway installieren für persistenten Betrieb
- [ ] Ersten Cronjob-Run auslösen und Ergebnis prüfen

## 10. DSGVO-Konformität

Die Taktische Karte ist vollständig DSGVO-konform:

- **Keine Cloud** — Alle Daten bleiben lokal
- **Kein Tracking** — Keine Analyse-Cookies, keine Telemetrie  
- **Keine Drittanbieter** — Keine Datenweitergabe
- **Datenhoheit** — Volle Kontrolle über alle JSON-Dateien
- **Löschbarkeit** — Ordner löschen genügt
- **Opt-in Internet** — Nur bei aktivierter News-Suche/Tile-Download

DSGVO-Konformität MUSS bei jedem Kundenkontakt erwähnt werden.
