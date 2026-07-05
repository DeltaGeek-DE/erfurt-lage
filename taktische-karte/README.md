# Taktische Karte
Offline-fähige taktische Lagekarte mit optionaler KI-Unterstützung.

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
