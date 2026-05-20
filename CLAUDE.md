# Implementierungsplan: Haushaltsplan Suhl → Orsi-Skill

> **Verwendung:** Diese Datei ist die primäre Arbeitsanweisung für Claude Code.
> Öffne den Projektordner `Haushalt Suhl` in VS Code, starte Claude Code
> (`claude` im Terminal) und sage: *"Lies CLAUDE.md und führe Phase 1 aus."*

---

## Kontext & Projektziel

Das Projektziel: Orsi (KI-Assistent auf elest.io) soll den Haushaltsplan der Stadt
Suhl per natürlichsprachiger Anfrage abfragen können — z. B. `"Wie viel hat Suhl
2024 für Kitas ausgegeben?"` oder `"Vergleiche die Aufwendungen für Soziales
2023 vs. 2025"`.

Das Web-Dashboard existiert bereits. Es muss **nicht** neu erstellt werden.

Die Haushaltsdaten (2023–2025) sind bereits in der lokalen SQLite-Datenbank
`suhl_haushalt_2025.db` vorhanden. Die Datenbank muss auf den Elestio-Server
hochgeladen werden, damit Orsi darauf zugreifen kann.

---

## Bestehende Projektstruktur (Stand: Mai 2026)

```
Haushalt Suhl/
├── suhl_haushalt_2025.db          ← SQLite-Datenbank (lokal, muss auf Server)
├── pipeline.py                    ← ETL-Pipeline (PDF → DB), bereits ausgeführt
├── validate.py                    ← Validierung der DB gegen Haushaltssatzung
├── setup_database.py              ← DB-Schema-Setup
├── import_dimensions.py           ← Stammdaten-Import
├── kategorisierung.py             ← Steuerungskategorien
├── pdf_chunks/                    ← Aufgeteilte PDFs der 12 Teilpläne
│   ├── tp_01_Verwaltungsfuehrung.pdf
│   ├── tp_02_Kultur_Tourismus_und_Sport.pdf
│   └── ... (tp_03 bis tp_12)
├── knowledge/                     ← Fachliche Hintergrunddokumente
└── CLAUDE.md                      ← Diese Datei
```

### Datenbankschema (SQLite — Sternschema)

```sql
-- Dimensionstabellen
teilplaene           (id, nummer, bezeichnung)                        -- 12 Dezernate
hauptproduktbereiche (id, nummer, bezeichnung)                        -- 6 Bereiche
produkte             (id, produkt_nummer, bezeichnung,
                      teilplan_id, hauptproduktbereich_id,
                      steuerungs_kategorie_id)                        -- ~146 Produkte
kontenklassen        (id, nummer, bezeichnung, rechnungstyp)          -- 4=Erträge, 5=Aufwendungen, 6=Einzahlungen, 7=Auszahlungen
konten               (id, konto_nummer, bezeichnung, kontenklasse_id) -- Sachkonten (6-stellig)
steuerungs_kategorien(id, code, bezeichnung, ebene_zustaendigkeit)    -- PFLICHT_STRIKT, FREIWILLIG etc.

-- Faktentabelle
haushaltswerte (id, haushaltsplan_jahr, daten_jahr, wert_typ,
                produkt_id, konto_id, betrag)
  -- wert_typ: 'IST_ERGEBNIS' | 'ANSATZ_VORJAHR' | 'PLAN_ANSATZ' | 'FINANZPLANUNG'
  -- haushaltsplan_jahr: Jahr des Berichts (z.B. 2025)
  -- daten_jahr: Zieljahr des Betrags (2023, 2024, 2025, 2026–2028)

-- View (bereits erstellt)
view_dashboard_flach  -- denormalisiert, für einfache Frontend-Abfragen
```

### Ground Truth (Validierungswerte aus Haushaltssatzung 2025)

| Kontenklasse | Beschreibung         | Soll-Wert (€)   |
|:------------|:---------------------|----------------:|
| 4           | Erträge              | 136.395.290,00  |
| 5           | Aufwendungen         | 138.003.230,00  |
| 6           | Einzahlungen         | 136.365.830,00  |
| 7           | Auszahlungen         | 135.802.480,00  |

---

## Serverarchitektur (Elestio)

### Zugangsdaten & Erreichbarkeit

```
┌─────────────────────────────────────────────────────────────────────┐
│  ELESTIO — Web-Konsole                                              │
│  URL:      https://app.elest.io                                     │
│  Login:    tobias.uske@gmail.com  (Google-SSO oder Passwort)        │
│  Projekt:  ssp-framework-2  →  Service "openclaw"                   │
│  Dort:     Terminal-Zugang, Logs, Docker-Container-Übersicht        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  SSH-DIREKTZUGANG (für scp / Remote-Befehle)                        │
│  Host:     ssp-framework-2-u68900.vm.elestio.app                   │
│  IP:       46.225.236.11                                            │
│  User:     root                                                     │
│  Key:      C:/Users/Tobias/.ssh/ssh-key.txt                         │
│                                                                     │
│  Befehl:   ssh -i "C:/Users/Tobias/.ssh/ssh-key.txt" \             │
│                root@ssp-framework-2-u68900.vm.elestio.app           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  DOCKER-CONTAINER (OpenClaw / Orsi)                                 │
│  Name:     app-openclaw-gateway-1                                   │
│  Shell:    docker exec -it app-openclaw-gateway-1 /bin/sh           │
│  Logs:     docker logs app-openclaw-gateway-1 --tail 50             │
└─────────────────────────────────────────────────────────────────────┘
```

> **Hinweis für Claude Code:** Der SSH-Key liegt lokal unter
> `C:/Users/Tobias/.ssh/ssh-key.txt`. Alle `ssh` und `scp` Befehle
> müssen diesen Key mit `-i` referenzieren. Auf dem Server als `root`
> einloggen — kein sudo nötig.

### Verzeichnisstruktur auf dem Server

```
/opt/
├── omni-weather-hub/                  ← Wetter-Projekt (Referenz)
│   └── weather.db
├── omni-haushalt/                     ← NEU (in Phase 3 anlegen)
│   └── suhl_haushalt.db               ← DB-Datei (hochgeladen aus lokalem Projekt)
└── app/
    └── skills/
        ├── weather-history-skill/     ← Bestehender Skill (Referenz)
        │   └── weather-history        ← CLI-Executable (Node.js)
        └── budget-skill/              ← NEU (in Phase 3 anlegen)
            ├── budget_query.py        ← Orsi-Skill (Python)
            └── requirements.txt       ← (leer oder: python-dateutil)
```

### OpenClaw — Wie Skills funktionieren

OpenClaw ist das Skill-Framework, das Orsi nutzt. Ein Skill ist ein CLI-Programm,
das OpenClaw mit Argumenten aufruft und dessen stdout-Output Orsi als Antwort
zurückbekommt. Aufrufmuster:

```bash
# Orsi ruft intern auf:
python /opt/app/skills/budget-skill/budget_query.py "Wie viel für Soziales 2025?"

# Mit JSON-Flag für strukturierte Weiterverarbeitung:
python /opt/app/skills/budget-skill/budget_query.py --json "Soziales 2025"
```

Der Skill muss:
- selbstständig die DB unter `$BUDGET_DB_PATH` finden (Fallback: `/opt/omni-haushalt/suhl_haushalt.db`)
- bei unklaren Abfragen eine hilfreiche Fehlermeldung zurückgeben
- `--json` für Maschinenoutput unterstützen
- keine externen APIs benötigen (reine DB-Abfragen)

---

## Phase 1 — Datenbank validieren

**Ziel:** Sicherstellen, dass `suhl_haushalt_2025.db` vollständig und korrekt ist,
bevor sie auf den Server hochgeladen wird.

### Aufgaben

```bash
# 1. Validierung ausführen
python validate.py

# 2. Datenbankinhalt prüfen (direkte SQLite-Abfrage)
python -c "
import sqlite3
con = sqlite3.connect('suhl_haushalt_2025.db')
print('=== Haushaltswerte pro Jahr und Typ ===')
for row in con.execute('''
    SELECT daten_jahr, wert_typ, COUNT(*) as anzahl, SUM(betrag) as summe
    FROM haushaltswerte
    GROUP BY daten_jahr, wert_typ
    ORDER BY daten_jahr, wert_typ
'''):
    print(f'  {row[0]} | {row[1]:<20} | {row[2]:>6} Zeilen | {row[3]:>15,.2f} EUR')
print()
print('=== Teilpläne ===')
for row in con.execute('SELECT nummer, bezeichnung FROM teilplaene ORDER BY nummer'):
    print(f'  TP {row[0]}: {row[1]}')
con.close()
"
```

### Erfolgskriterien

- `validate.py` gibt `✓ VALIDATION ERFOLGREICH` aus
- Alle 4 Ground-Truth-Summen zeigen `DIFF=+0.00`
- `daten_jahr 2025 | PLAN_ANSATZ` ist vorhanden
- Idealerweise auch 2023 (IST_ERGEBNIS) und 2024 (ANSATZ_VORJAHR)

### Falls die Validierung fehlschlägt

Fehlende Haushaltswerte (ETL noch nicht vollständig gelaufen):
```bash
python pipeline.py
```
Fehlende Stammdaten:
```bash
python setup_database.py
python import_dimensions.py
python kategorisierung.py
```

---

## Phase 2 — Orsi-Skill entwickeln (`budget_query.py`)

**Ziel:** Datei `skill/budget_query.py` im Projektordner erstellen.

### Erstelle: `skill/budget_query.py`

Der Skill muss folgende natürlichsprachige Anfragen verstehen:

| Kategorie          | Beispiel-Anfragen                                                          |
|:-------------------|:---------------------------------------------------------------------------|
| Jahressummen        | `"Gesamtaufwendungen 2025"`, `"Erträge 2024"`                             |
| Teilplan            | `"Was kostet Soziales 2025?"`, `"Budget Kultur 2024"`                      |
| Produkt             | `"Ausgaben Kitas 2025"`, `"Kosten Schulen 2023"`                           |
| Jahresvergleich     | `"Soziales 2023 vs 2025"`, `"Entwicklung Personalkosten"`                  |
| Top-N               | `"Die 5 größten Ausgabeposten 2025"`                                        |
| Kontenklasse        | `"Investitionen 2025"`, `"Einzahlungen aus Steuern"`                       |
| Steuerung           | `"Welche Ausgaben sind Pflicht?"`, `"Freiwillige Leistungen 2025"`         |

### Technische Anforderungen an `budget_query.py`

```python
"""
OpenClaw CLI-Skill: Natürlichsprachige Abfragen auf dem Haushaltsplan Suhl.

Aufruf:
  python budget_query.py "Wie viel hat Suhl 2025 für Soziales ausgegeben?"
  python budget_query.py "Top 5 Ausgaben 2025"
  python budget_query.py --json "Kitas 2023 vs 2025"

Umgebungsvariable:
  BUDGET_DB_PATH  Pfad zur SQLite-DB (Standard: /opt/omni-haushalt/suhl_haushalt.db)
"""
```

Der Skill muss:

1. **Jahr erkennen** via Regex `\b(20\d{2})\b` — fehlendes Jahr → aktuellstes PLAN_ANSATZ-Jahr
2. **Teilplan erkennen** via Keyword-Mapping (Deutsch → Teilplan-ID):
   ```python
   TEILPLAN_KEYWORDS = {
       "verwaltung": ["01", "03"],
       "sozial": ["09", "12"],
       "kinder": ["11"],
       "jugend": ["11"],
       "kita": ["11"],
       "schule": ["10"],
       "kultur": ["02"],
       "sport": ["02"],
       "ordnung": ["07"],
       "sicherheit": ["07"],
       "umwelt": ["08"],
       "straße": ["05"],
       "verkehr": ["05"],
       "finanzen": ["04", "06"],
       "personal": ["03"],
   }
   ```
3. **Kontenklasse erkennen**:
   ```python
   KONTENKLASSE_KEYWORDS = {
       "ertrag": 4, "einnahme": 4, "steuer": 4,
       "aufwand": 5, "ausgabe": 5, "kosten": 5,
       "einzahlung": 6,
       "auszahlung": 7, "investition": 7,
   }
   ```
4. **Vergleichsmodus erkennen**: `"vs"`, `"versus"`, `"vergleich"`, `"entwicklung"`, `"von ... bis"`
5. **Top-N erkennen**: `"top 5"`, `"größten"`, `"wichtigsten"`
6. **Steuerungskategorie erkennen**: `"pflicht"`, `"freiwillig"`, `"ermessen"`
7. **Datenbankabfrage** auf `view_dashboard_flach` (oder direkt auf Tabellen für komplexere Abfragen)
8. **Ausgabe**:
   - Standard: Klartextantwort in Deutsch, mit Einheiten in Tausend EUR oder Mio EUR je nach Betrag
   - `--json`: strukturiertes JSON mit allen Rohdaten

### Ausgabe-Beispiel (Standard)

```
Anfrage: Ausgaben für Soziales und Gesundheit 2025

Teilplan 09 – Soziales und Gesundheit
Haushaltsjahr 2025 (PLAN_ANSATZ)

Ergebnisplan:
  Erträge    (Kl. 4):   19.074.000 €
  Aufwendungen (Kl. 5):  54.198.450 €
  Saldo:                -35.124.450 €

Finanzplan:
  Einzahlungen (Kl. 6): 18.950.000 €
  Auszahlungen (Kl. 7):  52.100.000 €

Datenpunkte: 847
```

### Ausgabe-Beispiel (Vergleich)

```
Anfrage: Soziales 2023 vs 2025

Teilplan 09 – Soziales und Gesundheit

                     2023 (IST)       2025 (PLAN)    Veränderung
  Aufwendungen:    51.420.000 €     54.198.450 €    +2.778.450 € (+5,4%)
  Erträge:         17.890.000 €     19.074.000 €    +1.184.000 € (+6,6%)
  Saldo:          -33.530.000 €    -35.124.450 €    -1.594.450 €
```

### Ausgabe-Beispiel (Top-N)

```
Anfrage: Top 5 Ausgaben 2025

Die 5 größten Aufwendungen (PLAN_ANSATZ 2025):

  1. Soziale Sicherung               54.198.450 €   (TP 09)
  2. Personal / Zentrale Dienste     35.180.000 €   (TP 03)
  3. Transfer Sozialhilfe            22.770.000 €   (TP 09)
  4. Kinder-/Jugend-/Familienhilfe   18.340.000 €   (TP 11)
  5. Schulträgeraufgaben             12.890.000 €   (TP 10)
```

### Erstelle auch: `skill/requirements.txt`

```
# keine externen Pakete nötig — nur Python-stdlib + sqlite3 (built-in)
```

---

## Phase 3 — Deployment auf Elestio

**Ziel:** DB und Skill auf den Server bringen, Orsi kann Abfragen stellen.

### Schritt 3.1 — Verzeichnis auf Server anlegen

```bash
ssh -i "C:/Users/Tobias/.ssh/ssh-key.txt" root@ssp-framework-2-u68900.vm.elestio.app \
  "mkdir -p /opt/omni-haushalt && mkdir -p /opt/app/skills/budget-skill"
```

### Schritt 3.2 — Datenbank hochladen

```bash
# Lokale DB umbenennen für Server (jahresübergreifend)
cp suhl_haushalt_2025.db suhl_haushalt.db

scp -i "C:/Users/Tobias/.ssh/ssh-key.txt" \
  suhl_haushalt.db \
  root@ssp-framework-2-u68900.vm.elestio.app:/opt/omni-haushalt/suhl_haushalt.db
```

### Schritt 3.3 — Skill hochladen

```bash
scp -i "C:/Users/Tobias/.ssh/ssh-key.txt" \
  skill/budget_query.py \
  root@ssp-framework-2-u68900.vm.elestio.app:/opt/app/skills/budget-skill/budget_query.py
```

### Schritt 3.4 — Skill auf Server testen

```bash
ssh -i "C:/Users/Tobias/.ssh/ssh-key.txt" root@ssp-framework-2-u68900.vm.elestio.app

# Im Server-Terminal:
export BUDGET_DB_PATH=/opt/omni-haushalt/suhl_haushalt.db
python3 /opt/app/skills/budget-skill/budget_query.py "Gesamtaufwendungen 2025"
python3 /opt/app/skills/budget-skill/budget_query.py "Top 5 Ausgaben 2025"
python3 /opt/app/skills/budget-skill/budget_query.py --json "Soziales 2023 vs 2025"
```

### Schritt 3.5 — Skill in OpenClaw-Container registrieren

```bash
# Container-Shell öffnen
docker exec -it app-openclaw-gateway-1 /bin/sh

# Skill-Konfigurationsdatei prüfen/anlegen
# (Pfad analog zum bestehenden weather-history-skill)
ls /app/skills/
cat /app/skills/weather-history-skill/skill.json   # Referenz ansehen

# Neue skill.json anlegen für budget-skill
cat > /app/skills/budget-skill/skill.json << 'EOF'
{
  "name": "budget-suhl",
  "description": "Abfrage des Haushaltsplans der Stadt Suhl (2023-2025). Beantwortet Fragen zu Ausgaben, Einnahmen, Teilplänen und Jahresvergleichen auf Basis der offiziellen Haushaltssatzung.",
  "command": "python3",
  "args": ["/opt/app/skills/budget-skill/budget_query.py"],
  "env": {
    "BUDGET_DB_PATH": "/opt/omni-haushalt/suhl_haushalt.db"
  }
}
EOF
```

> **Hinweis:** Die genaue Struktur der `skill.json` und den Registrierungsbefehl
> aus dem bestehenden `weather-history-skill` ableiten — dieser ist die
> Referenzimplementierung auf dem Server.

---

## Phase 4 — Orsi-Memory aktualisieren

**Ziel:** Orsi weiß, was sie jetzt kann und wie sie Anfragen formulieren soll.

Orsi's Memory-Dateien liegen im OpenClaw-Container. Analog zur Struktur des
bestehenden Projekts müssen folgende Einträge hinzugefügt werden:

### Memory-Datei: `skill_budget_suhl.md`

Diese Datei beschreibt Orsi den neuen Skill — was er kann, wie sie ihn aufruft
und welche Fragen er beantworten kann.

```markdown
---
name: skill-budget-suhl
description: Orsi kennt den Skill budget-suhl für Haushaltsplan-Abfragen der Stadt Suhl
type: skill
---

# Skill: budget-suhl — Haushaltsplan Stadt Suhl

## Was dieser Skill kann

Ich kann den offiziellen Haushaltsplan der Stadt Suhl abfragen.
Die Datenbank enthält die Haushaltsjahre **2023 (Ist-Ergebnis),
2024 (Ansatz) und 2025 (Plan-Ansatz)** sowie die Finanzplanung bis 2028.

Der Haushalt basiert auf kommunaler Doppik (ThürKDG) und gliedert sich in:
- **12 Teilpläne** (Dezernate/Fachämter)
- **~146 Produkte** (Leistungseinheiten)
- **Ergebnisplan** (Erträge/Aufwendungen) und **Finanzplan** (Einzahlungen/Auszahlungen)

## Wann ich diesen Skill nutze

Bei Fragen wie:
- "Wie viel hat Suhl 2025 für [Bereich] ausgegeben?"
- "Vergleiche [Bereich] 2023 und 2025"
- "Was sind die größten Ausgabeposten?"
- "Wie hoch sind die Steuereinnahmen?"
- "Welche Leistungen sind freiwillig / Pflicht?"
- "Wie hat sich das Budget für [Bereich] entwickelt?"

## Wie ich den Skill aufrufe

**Einfache Abfrage:**
```
budget-suhl: "Wie viel hat Suhl 2025 für Kitas ausgegeben?"
```

**Jahresvergleich:**
```
budget-suhl: "Soziale Ausgaben 2023 vs 2025"
```

**Top-N:**
```
budget-suhl: "Top 5 Ausgabeposten 2025"
```

**JSON für Weiterverarbeitung:**
```
budget-suhl --json: "Aufwendungen Soziales 2025"
```

## Wichtige Fachbegriffe

| Begriff         | Bedeutung                                          |
|:---------------|:---------------------------------------------------|
| Erträge        | Einnahmen aus laufendem Betrieb (Kontenklasse 4)   |
| Aufwendungen   | Ausgaben laufender Betrieb (Kontenklasse 5)        |
| Einzahlungen   | Tatsächl. Geldzuflüsse (Kontenklasse 6)            |
| Auszahlungen   | Tatsächl. Geldabflüsse inkl. Investitionen (Kl. 7)|
| PLAN_ANSATZ    | Geplante Werte für 2025 (Haushaltssatzung)         |
| IST_ERGEBNIS   | Tatsächliche Werte 2023                            |
| Teilplan       | Organisationseinheit (Dezernat/Fachamt)            |
| Produkt        | Kleinste Leistungseinheit (z. B. "Kita-Betrieb")  |

## Die 12 Teilpläne

| Nr | Bezeichnung                          |
|:--|:-------------------------------------|
| 01 | Verwaltungsführung                  |
| 02 | Kultur, Tourismus und Sport         |
| 03 | Personal und Zentrale Dienste       |
| 04 | Finanzverwaltung                    |
| 05 | Öffentliche Flächen und Straßen     |
| 06 | Allgemeine Finanzwirtschaft         |
| 07 | Ordnung und Sicherheit              |
| 08 | Umwelt                              |
| 09 | Soziales und Gesundheit             |
| 10 | Schulträgeraufgaben                 |
| 11 | Kinder-, Jugend- und Familienhilfe  |
| 12 | Einrichtungen Sozialdezernat        |

## Haushaltliche Eckwerte 2025 (Ground Truth)

- Ordentliche Erträge:    **136.395.290 €**
- Ordentliche Aufwendungen: **138.003.230 €**
- Jahresergebnis:           **-1.607.940 €** (geplantes Defizit)
- Veränderung Finanzmittelbestand: **+563.350 €**
```

### Memory-Datei: `project_haushalt_suhl.md`

```markdown
---
name: project-haushalt-suhl
description: Orsi kennt das Projekt Haushaltsplan Suhl — Ziel, Datenstand und Einschränkungen
type: project
---

# Projekt: Haushaltsplan Stadt Suhl

**Fact:** Strukturierte SQLite-Datenbank des kommunalen Haushaltsplans Suhl.
**Why:** Transparenz und Analysierbarkeit der kommunalen Finanzen für Bürger und Politik.

## Technischer Stand

- Datenbank: `/opt/omni-haushalt/suhl_haushalt.db` (SQLite)
- Skill: `/opt/app/skills/budget-skill/budget_query.py`
- Datenstand: Haushaltsjahre 2023, 2024, 2025; Finanzplanung 2026–2028
- Grundlage: Offizieller Haushaltsplan Stadt Suhl 2025 (1116 Seiten PDF)
- Schema: Kommunale Doppik, Sternschema mit 6 Dimensionstabellen + Faktentabelle

## Einschränkungen

- Die Datenbank enthält **Plan-/Ist-Werte**, keine Echtzeit-Buchhaltungsdaten
- Unterjährige Änderungen (Nachtragshaushalt) sind **nicht** automatisch enthalten
- Aktualisierung erfolgt **einmal jährlich** nach Veröffentlichung des neuen Haushaltsplans
- Bei Fragen zu konkreten Einzelrechnungen oder Verträgen kann der Skill nicht helfen —
  dort auf offizielle Stadtunterlagen verweisen

## Jährliche Aktualisierung

Wenn ein neuer Haushaltsplan erscheint (typisch: Herbst/Winter):
1. Neues PDF lokal mit `pipeline.py` parsen
2. `suhl_haushalt.db` per `scp` auf Server hochladen
3. Kein Skill-Update nötig — Skill liest immer aktuelle DB
```

### Speicherorte der Memory-Dateien auf dem Server

```bash
# Im OpenClaw-Container prüfen, wo Memory-Dateien liegen:
docker exec -it app-openclaw-gateway-1 find / -name "*.md" -path "*/memory/*" 2>/dev/null

# Dann dort ablegen:
# (Beispielpfad — aus bestehenden Memory-Dateien ableiten)
/app/memory/skill_budget_suhl.md
/app/memory/project_haushalt_suhl.md
```

---

## Testfragen für Orsi nach dem Deployment

Diese Fragen direkt an Orsi stellen, um den Skill zu verifizieren:

```
Einfach:
  "Wie hoch waren die Gesamtaufwendungen der Stadt Suhl 2025?"
  "Was hat Suhl 2025 für Schulen ausgegeben?"
  "Wie hoch sind die Steuereinnahmen 2025?"

Teilplan:
  "Was kostet der Bereich Soziales und Gesundheit 2025?"
  "Wie viel gibt Suhl für Kultur aus?"
  "Budget für Ordnung und Sicherheit 2025"

Vergleich:
  "Vergleiche die Sozialausgaben 2023 und 2025"
  "Wie haben sich die Personalkosten entwickelt?"
  "Kinder- und Jugendhilfe 2023 vs 2025"

Top-N:
  "Was sind die 5 größten Ausgabeposten 2025?"
  "Welcher Teilplan hat das höchste Budget?"
  "Top 3 Ertragsquellen der Stadt Suhl"

Fachlich:
  "Wie hoch ist das geplante Defizit 2025?"
  "Welche Ausgaben sind Pflichtaufgaben?"
  "Wie viel investiert Suhl 2025?"
```

---

## Reihenfolge der Umsetzung

```
Phase 1:  python validate.py ausführen — DB-Status prüfen
Phase 2:  skill/budget_query.py entwickeln und lokal testen
Phase 3:  DB + Skill auf Elestio hochladen und testen
Phase 4:  Memory-Dateien in OpenClaw-Container ablegen
```

**Start-Befehl für Claude Code:**
> *"Lies CLAUDE.md. Führe zunächst Phase 1 aus: Validiere die Datenbank und zeige
> mir den vollständigen Statusbericht. Dann erstelle `skill/budget_query.py`
> gemäß Phase 2."*

---

## Stellenplan-Pipeline — Stufe 2

**Status:** Geplant. Stufe 1 (Personalkosten aus DB) ist live im Dashboard.

### Was Stufe 1 bereits liefert (Personal-Tab)

Der Personal-Tab im Dashboard zeigt Personalkosten aus der bestehenden DB:
- Konten 501x–507x gruppiert in 7 Kategorien (Beamte/Tarif Bezüge, Versorgung, SV, Beihilfen, Sonstiges)
- Je Teilplan und Jahr (2023–2025), ~34,8 Mio € Personalkosten 2025

**Fehlende Daten:** Köpfe (Vollzeitstellen), Besoldungsgruppen (A1-B / E1-E15)

### Was Stufe 2 hinzufügt

Aus dem Stellenplan-PDF (je ca. 30–50 Seiten im Haushaltsplan) extrahieren:
- **Planstellen je Besoldungsgruppe:** A6–A16, B2–B8 (Beamte), E1–E15, SuE (Tarif)
- **Planstellenanzahl 2023/2024/2025** (Soll-Stellen, genehmigt)
- **Teilplan-Zuordnung** der Stellen

### Datenbankschema Stufe 2 (neue Tabellen)

```sql
-- Stellenplan-Dimensionen
besoldungsgruppen (id, kuerzel, typ, beschreibung)
  -- typ: BEAMTE | TARIF
  -- kuerzel: 'A6', 'A7', ..., 'E1', 'E2', ..., 'SuE'

stellenplan (id, teilplan_id, besoldungsgruppe_id, daten_jahr, planstellen)
  -- planstellen: DECIMAL(5,2) — ganze und halbe Stellen
```

### Pipeline Stufe 2

```
Dateien:
  smart_split_stellenplan.py    ← PDF-Chunks aus Stellenplan-Abschnitt
  pipeline_stellenplan.py       ← OCR/Regex-Extraktion → DB
  validate_stellenplan.py       ← Prüfung gegen Summen im PDF-Stellenplan

Aufruf:
  python smart_split_stellenplan.py  # Stellenplan-PDF aufteilen
  python pipeline_stellenplan.py     # Stellen in DB importieren
  python generate_json.py            # JSON neu generieren (personal.by_year erhält stellenplan-Schlüssel)
```

### Herausforderungen

1. **Tabellenstruktur variiert** je Jahrgang (2022 vs. 2025 unterschiedliche Spaltenbreiten)
2. **Mehrseitige Tabellen** — Seitenumbrüche zerschneiden Zeilen
3. **Halbe Stellen** — PDF zeigt "0,5" (Komma, nicht Punkt)
4. **Querverweise** — Stellenplan verweist auf Fußnoten für kw-Stellen (künftig wegfallend)

### Erwartetes Ergebnis im JSON (`personal.by_year["2025"]`)

```json
{
  "gesamt": 34780000,
  "bez_beamte": 4360000,
  ...
  "stellenplan": {
    "gesamt_stellen": 412.5,
    "beamte_stellen": 78.0,
    "tarif_stellen": 334.5,
    "nach_gruppe": {
      "A6": 12, "A7": 8, "A8": 14, "A9": 11,
      "E6": 45, "E8": 62, "E9a": 38, ...
    },
    "nach_tp": {
      "03": { "gesamt": 89.5, "beamte": 22, "tarif": 67.5 },
      ...
    }
  }
}
```

### Jahrgänge für Stufe 2

Folgende Haushaltspläne haben Stellenpläne und können mit der Pipeline verarbeitet werden:
- 2022 (online verfügbar, ca. 1.100 Seiten)
- 2023 (bereits für ETL genutzt — Stellenplan noch nicht extrahiert)
- 2024 (bereits für ETL genutzt — Stellenplan noch nicht extrahiert)
- 2025 (bereits für ETL genutzt — Stellenplan noch nicht extrahiert)

**Hinweis:** PDFs liegen lokal unter `knowledge/` (nicht im Repo).
