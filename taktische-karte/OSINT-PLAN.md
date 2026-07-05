# OSINT-Modul — Plan

## Übersicht

Ein Recherche-Modul für die Taktische Karte. Der Anwender fügt Links zu Social-Media-Profilen ein. Ein KI-Agent (wenn verfügbar) recherchiert selbstständig zur Person/Organisation. Ergebnisse werden in einem eigenen Browser-Tab dargestellt. Ohne KI: manuelle Dateneingabe.

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│  Admin-Panel: Tab "🔍 OSINT"                            │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Link-Queue                                       │   │
│  │ [https://x.com/BeispielUser]  [➕] [▶ Starten]  │   │
│  │ [https://facebook.com/BeispielUser]              │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ▼ KI verfügbar?                                        │
│  ┌─── JA ──────────────────────────────────────────┐   │
│  │ POST /osint/start → Hermes-Local-Agent startet  │   │
│  │ SSE /osint/progress → Live-Fortschritt          │   │
│  │ → Ergebnis im neuen Tab: osint-results.html     │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─── NEIN ────────────────────────────────────────┐   │
│  │ Manuelles Formular:                              │   │
│  │   Name, Alias, Organisation                      │   │
│  │   Notizen, Bewertung (1-5)                       │   │
│  │   Medien-Upload (Bilder, Screenshots)            │   │
│  │   Verknüpfte Orte (Karte klicken)               │   │
│  │ → Daten in osint-data.json                       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Datenstruktur

```json
// osint-data.json
{
  "personen": [{
    "id": "uuid",
    "name": "Max Mustermann",
    "alias": ["@MaxMuster", "Maximilian"],
    "profile_urls": ["https://x.com/MaxMuster", "https://facebook.com/..."],
    "plattform": "x",
    "bewertung": {"stufe": 1, "text": "..."},
    "besuchte_orte": [{"lat": 50.97, "lon": 10.99, "name": "Erfurt Hbf"}],
    "beziehungen": ["uuid2", "uuid3"],
    "notizen": "...",
    "medien": ["screenshots/abc.jpg"],
    "recherche_stand": "2026-07-05",
    "quelle": "ki" // oder "manuell"
  }]
}
```

## KI-Agent-Workflow

```
Eingabe: Profil-URL
  │
  ├─ 1. web_search("site:x.com MaxMuster")
  ├─ 2. web_extract(url) → Profilseite parsen
  ├─ 3. web_search("Max Mustermann Erfurt")  → Ortsbezüge
  ├─ 4. web_search("Max Mustermann Freund")  → Beziehungen
  ├─ 5. Zusammenfassung generieren:
  │     - Name, Alias
  │     - Standort(e)
  │     - Soziales Umfeld
  │     - Risikobewertung
  │     - Letzte Aktivität
  │     - Auffälligkeiten
  │
  └─ Ergebnis → osint-data.json + osint-results.html
```

## Benötigte Dateien

| Datei | Zweck |
|---|---|
| `app/osint.html` | Recherche-Tab (eigenständige Seite) |
| `app/scripts/osint.py` | KI-Agent-Skript (wird vom Server aufgerufen) |
| `app/data/osint-data.json` | Persistente Recherche-Daten |
| `server.py` (Update) | Neue Routen: `/osint/start`, `/osint/progress`, `/osint/data` |

## Manueller Modus (ohne KI)

```
┌─────────────────────────────────────────┐
│  Name:          [________________]       │
│  Alias:         [________________]       │
│  Profile-Links: [________________] [➕]  │
│  Notizen:       [________________]       │
│                  [________________]       │
│  Risiko:        [●○○○○] 1-5             │
│  Besuchte Orte: [Auf Karte klicken]      │
│  Medien:        [📎 Upload]              │
│  Verknüpfungen: [Max ↭ Anna]            │
│                                          │
│  [💾 Speichern]  [📤 Exportieren]       │
└─────────────────────────────────────────┘
```

## Ergebnis-Darstellung (osint-results.html)

```
┌──────────────────────────────────────────────────┐
│  🔍 OSINT: Max Mustermann (@MaxMuster)            │
├──────────────────────────────────────────────────┤
│                                                    │
│  ⚠️ RISIKO: ●○○○○ (Niedrig)                       │
│                                                    │
│  📍 Letzter Standort: Erfurt Hbf (gestern)         │
│  📍 Häufig besucht: Gothaer Platz, Messe           │
│                                                    │
│  👥 Beziehungen:                                   │
│    ↭ Anna Schmidt (Freundin)                       │
│    ↭ @DemoOrg (Organisation)                       │
│                                                    │
│  📝 Notizen:                                       │
│  Wiederholt bei Blockaden am Gothaer Platz         │
│  gesichtet. Keine Gewalttätigkeit bekannt.         │
│                                                    │
│  📅 Letzte Aktivität: 4. Juli 2026                 │
│  🔗 Profile: X, Facebook, Instagram               │
│                                                    │
│  🖼 Screenshots (3)                                │
│  [Bild1] [Bild2] [Bild3]                          │
│                                                    │
│  [✏️ Bearbeiten] [🗑 Löschen] [📤 Exportieren]   │
└──────────────────────────────────────────────────┘
```

## DSGVO

- Alle OSINT-Daten bleiben lokal
- Keine externen APIs außer Hermes-interner `web_search` / `web_extract`
- Medien (Screenshots) werden lokal im `osint/`-Ordner gespeichert
- Löschen = Ordner löschen

## Implementierung

### Phase 1: Manueller Modus (2-3h)
1. `app/osint.html` — Formular + Tab
2. `app/data/osint-data.json` — initiale Struktur
3. `server.py` — `/osint/data` GET/POST-Endpunkte
4. Verlinkung im Admin-Panel

### Phase 2: KI-Modus (2h)
5. `app/scripts/osint.py` — Agent-Skript
6. `server.py` — `/osint/start` + `/osint/progress` (SSE)
7. `osint-results.html` — Ergebnis-Seite

### Phase 3: Medien & Visualisierung (1h)
8. Medien-Upload (Bilder im Formular)
9. Karten-Integration (besuchte Orte auf Karte)
10. Verknüpfungs-Graph (Person A → Person B)
