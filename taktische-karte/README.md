# Taktische Karte
Offline-fähige taktische Lagekarte mit optionaler KI-Unterstützung.

## 🔒 DSGVO-Konformität

Die Taktische Karte ist **vollständig DSGVO-konform** (DSGVO = GDPR):

- ✅ **Keine Cloud** — Alle Daten bleiben lokal auf dem Rechner des Anwenders
- ✅ **Kein Tracking** — Keine Analyse-Cookies, keine Telemetrie
- ✅ **Keine Drittanbieter** — Keine Datenweitergabe an externe Server
- ✅ **Datenhoheit** — Der Anwender hat volle Kontrolle über alle Daten (JSON-Dateien, localStorage)
- ✅ **Löschbarkeit** — Alle Daten können jederzeit vollständig gelöscht werden (Ordner löschen genügt)
- ✅ **Opt-in Internet** — Internetzugriff nur bei aktivierter KI-News-Suche oder manuellem Tile-Download
- ⚠️ **Tile-Download**: Bei Download von Kartendaten werden Kacheln von OpenStreetMap/ESRI geladen — kein Personenbezug

Die einzige clientseitige Speicherung ist `localStorage` für die Geländetaufe (taktische Gebäudemarkierungen). Keine personenbezogenen Daten.

## Abhängigkeiten

| Komponente | Benötigt | Für |
|---|---|---|
| Python 3.11+ | ✅ Pflicht | Server, Geocoding, Build |
| Browser (Chrome/Firefox/Edge) | ✅ Pflicht | Karten-Darstellung |
| Internet | ⚪ Optional | Nur für KI-Auto-Update |
| Hermes Agent | ⚪ Optional | Nur für KI-Cronjob |

## Schnellstart (Offline)

```bash
python server.py
# Öffne http://localhost:8765
```

## Schnellstart (mit KI)

```bash
# 1. Server starten
python server.py

# 2. Hermes Cronjob einrichten
hermes cron create "*/5 * * * *" --prompt "..."
```

## Release bauen

```bash
python build.py
# Erzeugt taktische-karte.zip im dist/-Ordner
```
