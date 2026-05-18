# Haushaltsplan Stadt Suhl 2025 – Interaktives Dashboard

Statisches Web-Dashboard für den Haushaltsplan der Stadt Suhl 2025.
Vollständig clientseitig – kein Server, keine Backend-Abhängigkeiten.
Kann direkt auf **GitHub Pages** gehostet werden.

## Live-Demo

Nach Deployment erreichbar unter:
`https://<dein-username>.github.io/<repo-name>/`

---

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `index.html` | Dashboard (Tailwind CSS + Plotly.js, vollständig statisch) |
| `budget_data.json` | Exportierte Haushaltsdaten (aus `generate_json.py`) |
| `generate_json.py` | Python-Exporter: SQLite → JSON |
| `pipeline.py` | ETL-Pipeline: PDF → SQLite |
| `suhl_haushalt_2025.db` | SQLite-Datenbank (lokal, nicht im Repo) |

---

## Dashboard-Funktionen

### Überblick-Tab
- **KPI-Karten**: Gesamterträge, Aufwendungen, Jahresergebnis, Pro-Kopf-Aufwand
- **Sankey-Diagramm**: Mittelfluss von Ertragsquellen (Steuern, Schlüsselzuweisungen, Gebühren…) zu den 12 Teilplänen
- **Treemap**: Aufwendungen nach Teilplan und Steuerungstyp (freiwillig / Pflicht / strikt)
  - Toggle „Nur gestaltbar": blendet PFLICHT_STRIKT und UEBERTRAGEN aus
- **Balkendiagramm**: Saldo (Erträge − Aufwendungen) je Teilplan

### Zeitreihe-Tab
- Liniendiagramm Erträge & Aufwendungen 2023–2028
- Schraffierter Bereich = Finanzplanung (Prognose 2026–2028)

### Konsolidierungs-Simulator-Tab
- Regler für alle 87 Produkte mit Steuerungskategorie
- **PFLICHT_STRIKT** und **UEBERTRAGEN**: gesperrt (0 % Kürzung möglich)
- **PFLICHT_ERMESSEN**: max. 15 % Kürzung
- **FREIWILLIG**: max. 100 % Kürzung
- Simuliertes Jahresergebnis aktualisiert sich in Echtzeit
- **Wechselwirkung – Präventions-Kosten-Spirale**: Kürzungen der Jugendarbeit (362xxx) > 20 % lösen automatisch einen Risikozuschlag von +5 % auf Hilfen zur Erziehung (363000) aus

---

## Deployment auf GitHub Pages

### Erstmalig

```bash
# 1. Repo anlegen (einmalig auf github.com)

# 2. Lokal initialisieren
git init
git remote add origin https://github.com/<username>/<repo>.git

# 3. Nur die Web-Dateien committen (DB bleibt lokal!)
git add index.html budget_data.json README.md
git commit -m "feat: Haushalts-Dashboard Suhl 2025"
git push -u origin main

# 4. GitHub Pages aktivieren
# → Repository Settings → Pages → Source: "Deploy from branch" → branch: main
```

### Daten aktualisieren

```bash
# DB wurde neu befüllt, JSON neu generieren:
python generate_json.py

# Nur JSON und HTML aktualisieren:
git add budget_data.json index.html
git commit -m "data: Haushaltsdaten aktualisiert"
git push
```

---

## Lokale Vorschau

```bash
# Python 3 (einfachster Weg):
python -m http.server 8080
# → http://localhost:8080

# Node.js (alternativ):
npx serve .
```

> **Wichtig**: `index.html` direkt als Datei öffnen (`file://`) funktioniert nicht,
> da `fetch("budget_data.json")` einen lokalen HTTP-Server benötigt.

---

## JSON neu generieren

```bash
# Voraussetzung: suhl_haushalt_2025.db muss befüllt sein (pipeline.py)
python generate_json.py
```

Ausgabe zeigt Anzahl Datensätze und ETL-Validierungswerte.

---

## Datenquelle

Haushaltsplan der Stadt Suhl 2025 (öffentliches Dokument der Stadtverwaltung Suhl, Thüringen).
ETL-Pipeline: Cortex AI Solutions, 2025/2026.
