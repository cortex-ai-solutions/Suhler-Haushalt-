# Projektdokumentation: Haushaltsplan Suhl — Dashboard + Orsi-Skill

> **Für Claude Code:** Diese Datei ist die primäre Arbeitsanweisung.
> Lies sie vollständig, bevor du Code schreibst oder änderst.

---

## Kontext & Projektziel

Orsi (KI-Assistent auf elest.io) soll den Haushaltsplan der Stadt Suhl per
natürlichsprachiger Anfrage abfragen können. Parallel dazu gibt es ein
öffentliches Web-Dashboard auf GitHub Pages für Stadträte und Bürger.

**GitHub Pages:** `https://cortex-ai-solutions.github.io/Suhler-Haushalt-/`
**Elestio:** `https://app.elest.io` → Projekt `ssp-framework-2` → Service `openclaw`

---

## Projektstand (Juni 2026)

### Was vollständig implementiert ist

| Bereich | Status | Details |
|---------|--------|---------|
| ETL-Pipeline | ✅ fertig | 2023, 2024, 2025 — 89.808 Haushaltswerte |
| Datenbankschema | ✅ fertig | Sternschema + HSK + Stellenplan |
| Dashboard Tabs | ✅ fertig | 7 Tabs live auf GitHub Pages |
| Stellenplan | ✅ fertig | 2024+2025 in DB, Personal-Tab im Dashboard |
| HSK-Integration | ✅ fertig | 78 Maßnahmen, 3 Stufen |
| Simulator-Integration | ✅ fertig | Stufe A+B+C |
| Orsi-Skill (Haushalt) | ✅ fertig | budget_query.py auf Elestio |
| Orsi-Skill (Stellenplan) | ✅ fertig | detect_stellenplan() in budget_query.py |
| Orsi-Skill (HSK) | ❌ offen | DB hochladen + Skill erweitern |
| Stellenplan 2023 | ❌ offen | Erfordert HH-Plan 2024 PDF |
| Zielerreichungsquote (HSK) | ❌ offen | Stufe 3 noch nicht implementiert |

---

## Datenbankschema (SQLite — `suhl_haushalt_2025.db`)

### Kern-Tabellen (Haushalt)

```sql
-- Dimensionen
teilplaene           (id, nummer, bezeichnung)          -- 12 Dezernate
hauptproduktbereiche (id, nummer, bezeichnung)          -- 6 Bereiche
produkte             (id, produkt_nummer, bezeichnung,
                      teilplan_id, hauptproduktbereich_id,
                      steuerungs_kategorie_id,
                      rechtsgrundlage)                  -- 314 Produkte
kontenklassen        (id, nummer, bezeichnung, rechnungstyp)
konten               (id, konto_nummer, bezeichnung, kontenklasse_id)
steuerungs_kategorien(id, code, bezeichnung,
                      ebene_zustaendigkeit, beschreibung)
-- Fakten
haushaltswerte (id, haushaltsplan_jahr, daten_jahr, wert_typ,
                produkt_id, konto_id, betrag)
  -- wert_typ: IST_ERGEBNIS | ANSATZ_VORJAHR | PLAN_ANSATZ | FINANZPLANUNG
  -- Verfügbare daten_jahre: 2021–2028 (je nach wert_typ)
```

### HSK-Tabellen (Haushaltssicherungskonzept)

```sql
hsk_massnahmen (id, nr, bezeichnung, produkte, verantwortlich,
                rechtsform, ab_haushaltsjahr,       -- ab_haushaltsjahr=NULL (noch nicht geparst)
                betrag_kumulativ, betrag_2023, betrag_2024, betrag_2025,
                betrag_gesamt, umsetzungsstatus, kategorie, beschreibung)
  -- umsetzungsstatus: aktiv | erledigt | entfallen | geprueft
  -- kategorie: ERTRAG | AUFWAND | PERSONAL
  -- 78 Maßnahmen: 43 aktiv, 4 erledigt, 31 entfallen

hsk_jahreswerte (id, massnahme_id, jahr, umgesetzter_betrag)
  -- 1.014 Zeilen, Jahre 2013–2025

hsk_massnahmen_produkte (massnahme_id, produkt_nummer)
  -- 63 Verknüpfungen; 17 Maßnahmen ohne Produktbindung

-- VIEW (IST_ERGEBNIS für 2022/2023, PLAN_ANSATZ für 2024/2025)
hsk_abgleich  -- joins massnahmen × jahreswerte × produkte × haushaltswerte
```

### Stellenplan-Tabellen

```sql
besoldungsgruppen (id, kuerzel, typ, beschreibung)
  -- typ: BEAMTE | TARIF; 36 Gruppen (A7–B3, E2–S18)
stellenplan (id, teilplan_id, besoldungsgruppe_id, daten_jahr, wert_typ, planstellen)
  -- wert_typ: PLAN_ANSATZ | IST
  -- daten_jahre: 2024 (Plan+Ist) + 2025 (Plan); 387 Zeilen
  -- FEHLT: 2023 (erfordert HH-Plan 2024 PDF in knowledge/)
```

### Views

```sql
view_dashboard_flach  -- denormalisiert für Frontend (JOIN aller Dimensionen)
hsk_abgleich          -- HSK-Maßnahmen × Haushaltswerte
```

---

## Dashboard — Tab-Übersicht

**URL:** `https://cortex-ai-solutions.github.io/Suhler-Haushalt-/`

| Tab | Inhalt |
|-----|--------|
| Überblick | KPI-Chips, Sankey-Mittelfluss, Treemap, Balkendiagramm TP |
| Details | Drill-Down TP → Produkt → Konto, Merkzettel |
| Personal | Personalkosten 2023–2025 je TP, Stellenplan-Tabelle, Donut |
| Jahresvergleich | TP- und Produkt-Vergleich zwischen zwei Jahren |
| Zeitreihe | Entwicklung KK4/5 je TP über alle verfügbaren Jahre |
| **HSK & Konsolidierung** | Haushaltssicherungskonzept (78 Maßnahmen) |
| **Konsolidierungs-Simulator** | Schieberegler-Simulation mit HSK-Integration |

### HSK & Konsolidierung Tab — Features

- **KPI-Chips**: Anzahl Maßnahmen, aktiv, kumulativ 2013–2022, 2024/2025
- **5. KPI-Chip**: Produktabgleich-Statistik (61/78 verknüpft, X positiv/negativ)
- **Schmerzskala**: Progress-Bar Gesamtziel (Kumuliert 40 Mio€ / Ziel ~59 Mio€)
- **Jahresverlauf-Chart**: Plotly-Balkendiagramm 2013–2025 je Maßnahme
  - Grün = Einsparung, Rot = Mehraufwand, Dunkelgrüner Balken = Wirksamkeitsjahr
  - Metadaten: wirksam_ab + Sparwirkung gesamt in T€
- **Maßnahmen-Tabelle**: Sortiert nach Nr., mit Status-Filter + Freitextsuche
  - Spalten: Nr., Maßnahme, Kategorie, Kumulativ, 2024, 2025, Tendenz-Pfeil, Status
  - IST/PLAN-Badges in der Jahres-Abgleich-Tabelle
  - Aufklappen: Beschreibung + Chart + Haushaltsabgleich (Soll/Ist)
- **TP-Filter**: Klick auf Simulator-Badge → zeigt nur Maßnahmen des TPs
- **Filter-Info-Leiste**: zeigt aktiven TP-Filter + "× Filter entfernen"

### Konsolidierungs-Simulator Tab — Features

- **Szenario-Buttons**: "HSK 2025 aktiv" / "HSK vollständig" / "Zurücksetzen"
- **TP-Abschnitte**: Produkte gruppiert nach Teilplan mit Trennzeile
- **Vorbelastungs-Badge** je TP: kumulierte HSK-Einsparungen + Schmerzgrad
  - ●●● rot (>5 Mio€), ●●○ orange (>2 Mio€), ●○○ gelb (>0,5 Mio€), ○○○ grün
  - **Anklickbar**: navigiert direkt zu HSK-Tab gefiltert nach diesem TP
- **HSK-Badge** je Produkt: HSK-Einsparziel als % des Budgets
- **Drei-Zonen-Balken (Stufe C)** über jedem Schieberegler:
  - 🔵 Blau = HSK-Einsparziel 2025
  - 🟠 Orange = Eigene Zusatz-Kürzung über HSK-Ziel hinaus
  - 🌑 Dunkelblau = HSK-Ziel noch nicht erreicht
  - ⬛ Grau = ungenutzter Spielraum
- Wechselwirkung-Warnung (Präventions-Kosten-Spirale)
- Jahresergebnis-Anzeige in Echtzeit

---

## Datendateien

### Lokal (Projekt-Ordner)

```
suhl_haushalt_2025.db     ← SQLite-Hauptdatenbank (lokal)
budget_data.json          ← Exportiertes Dashboard-JSON (~723 KB)
index.html                ← Dashboard (Single-Page-App, GitHub Pages)
generate_json.py          ← Exportiert budget_data.json aus DB
```

### Patch-Skripte (NICHT löschen — Nachvollziehbarkeit)

```
patch_hsk_tab.py          ← HSK Stufe 1: Tab + Tabelle
patch_hsk_stufe2.py       ← HSK Stufe 2: Soll/Ist-Abgleich (Monkey-Patching)
patch_hsk_ui.py           ← HSK Stufe 3: Plotly-Chart + verbesserter Abgleich
patch_hsk_stufe2.py       ← HSK Stufe 2: Soll/Ist-Abgleich
patch_sim_hsk.py          ← Simulator Stufe A+B: Badges + Szenario-Loader
patch_sim_hsk_link.py     ← Simulator: TP-Badge → HSK-Tab Navigation
patch_sim_stufe_c.py      ← Simulator Stufe C: Drei-Zonen-Balken
patch_personal_tab.py     ← Personal-Tab (Stellenplan-Integration)
patch_sp_format.py        ← Stellenplan-Formatierung
patch_sp_merkzettel.py    ← Stellenplan-Merkzettel
patch_stellenplan_tab.py  ← Stellenplan-Tab-Erweiterungen
```

### Pipeline-Skripte

```
pipeline.py               ← Haushalt-ETL (PDF → DB), für 2023/2024/2025 gelaufen
pipeline_hsk.py           ← HSK-PDF-Parser (Anlage XVII a+b → DB)
pipeline_stellenplan.py   ← Stellenplan-Parser (Seiten 893–898 des HH-Plans 2025)
setup_database.py         ← DB-Schema-Setup + Stammdaten-Seeding
import_dimensions.py      ← Stammdaten-Import
validate.py               ← Validierung gegen Haushaltssatzung Ground Truth
generate_json.py          ← DB → budget_data.json (für Dashboard)
```

### Wissensdokumente (`knowledge/`)

```
HSK-9-2025.pdf            ← Haushaltssicherungskonzept 9. Fortschreibung (Quelle)
haushalt_suhl_2023.pdf    ← HH-Plan 2023 (ETL abgeschlossen)
haushalt_suhl_2024.pdf    ← HH-Plan 2024 (ETL abgeschlossen)
haushalt_suhl_2025.pdf    ← HH-Plan 2025 (ETL abgeschlossen)
-- FEHLT: HH-Plan 2024 PDF für Stellenplan 2023 --
```

---

## Technische Constraints (WICHTIG für alle Code-Änderungen)

### index.html — CRLF-Pflicht

`index.html` verwendet Windows-Zeilenenden (CRLF = `\r\n`). **Niemals** den
`Edit`-Tool für mehrzeilige JS-Blöcke verwenden — immer Python-Patch-Skripte
mit `content.encode("utf-8")` und `open(..., "wb")` schreiben.

### index.html — Kein Unicode in JavaScript-Strings

Pfeilzeichen (↑↓→) und andere Unicode-Symbole in JS-Strings/Template-Literals
brechen den Parser. Stattdessen:
- HTML-Entities: `&uarr;` `&darr;` `&rarr;` `&ndash;` `&euro;`
- In Plotly-Strings: `'€'` (Escape-Notation)

### index.html — Template-Literal-Sicherheit

Template-Literals (Backticks) dürfen nie direkt editiert werden. Der Patch-Ansatz:
1. **Monkey-Patching**: `const _orig = fn; fn = function() { _orig(); /* extra */ };`
2. **Funktions-Überschreibung**: `buildAbgleichCard = function(m) { ... };`
3. **String-Concatenation** statt Template-Literals in neuen Funktionen

Backtick-Anzahl muss immer **gerade** bleiben. Check: `content.count('\x60') % 2 == 0`

### JS-Reihenfolge und Hoisting

- `function`-Deklarationen werden gehoisted — auch wenn Monkey-Patch vorher im File steht
- `const/let`-Deklarationen NICHT hoisted → `const _orig = fn;` braucht fn bereits definiert
  (kein Problem bei function-Deklarationen, aber aufpassen bei `const fn = ...`)
- Mehrere Monkey-Patches stacken sich: neuester Patch wrappet alle vorherigen

### generate_json.py — nach DB-Änderungen

Nach jeder Änderung an DB oder Views immer:
```bash
python generate_json.py
# Dann budget_data.json committen
```

---

## Serverarchitektur (Elestio)

```
SSH:     ssh -i "C:/Users/Tobias/.ssh/ssh-key.txt" root@ssp-framework-2-u68900.vm.elestio.app
Docker:  docker exec -it app-openclaw-gateway-1 /bin/sh
DB-Pfad: /opt/omni-haushalt/suhl_haushalt.db
Skill:   /opt/app/skills/budget-skill/budget_query.py
```

**Aktueller Stand auf Server:** Haushaltsdaten 2023–2025 + Stellenplan ✅
**Fehlt auf Server:** HSK-Tabellen (hsk_massnahmen, hsk_jahreswerte, hsk_massnahmen_produkte, hsk_abgleich VIEW)

### Server-Update-Prozedur (nach lokalen DB-Änderungen)

```bash
# 1. Lokale DB umbenennen (jahresübergreifend)
cp suhl_haushalt_2025.db suhl_haushalt.db

# 2. Hochladen
scp -i "C:/Users/Tobias/.ssh/ssh-key.txt" \
  suhl_haushalt.db \
  root@ssp-framework-2-u68900.vm.elestio.app:/opt/omni-haushalt/suhl_haushalt.db

# 3. Skill hochladen (wenn geändert)
scp -i "C:/Users/Tobias/.ssh/ssh-key.txt" \
  skill/budget_query.py \
  root@ssp-framework-2-u68900.vm.elestio.app:/opt/app/skills/budget-skill/budget_query.py

# 4. Testen
ssh -i "C:/Users/Tobias/.ssh/ssh-key.txt" root@ssp-framework-2-u68900.vm.elestio.app
export BUDGET_DB_PATH=/opt/omni-haushalt/suhl_haushalt.db
python3 /opt/app/skills/budget-skill/budget_query.py "Gesamtaufwendungen 2025"
python3 /opt/app/skills/budget-skill/budget_query.py "Wie viele Stellen hat TP 09?"
```

---

## Offene Punkte (priorisiert)

### 🔴 Hoch — Server-Update (Elestio)

Die lokale DB enthält HSK-Daten die auf dem Server fehlen. Bis zum Upload
kann Orsi keine HSK-Fragen beantworten.

**Aufgabe:** `suhl_haushalt.db` via `scp` hochladen (siehe Server-Update-Prozedur).

### 🔴 Hoch — Orsi-Skill HSK-Erweiterung

`skill/budget_query.py` unterstützt Haushalt + Stellenplan, aber noch kein HSK.

**Aufgabe:** Funktionen ergänzen:
- `detect_hsk(query)` → erkennt HSK-Anfragen
- `query_hsk_massnahmen(...)` → sucht nach Maßnahmen
- `format_hsk(...)` → formatiert Ergebnis
- Beispiel-Anfragen: `"Welche HSK-Maßnahmen gibt es für Soziales?"`,
  `"Wie viel hat Suhl durch das HSK gespart?"`, `"Was sind die aktivsten Konsolidierungsmaßnahmen?"`

### 🟡 Mittel — Stellenplan 2023

**Problem:** `pipeline_stellenplan.py` sucht Seiten 893–898 im HH-Plan 2025 PDF.
Für 2023-Daten wird das HH-Plan 2024 PDF benötigt.

**Aufgabe:** HH-Plan 2024 PDF in `knowledge/` ablegen, dann:
```bash
python pipeline_stellenplan.py  # mit angepasstem PDF_PATH und daten_jahr=2023
python generate_json.py
# Dashboard bekommt automatisch neue 2023-Spalte im Personal-Tab
```

### 🟡 Mittel — HSK Stufe 3: Zielerreichungsquote

**Ziel:** Für jede HSK-Maßnahme mit Produktabgleich berechnen:
- Basis-Budget (aus `ab_haushaltsjahr` → baseline year)
- Ist-Entwicklung des KK4/KK5-Werts seit Baseline
- Zielerreichungsquote: (tatsächliche Budgetentwicklung) / (HSK-Einsparziel) × 100%
- Anzeige: "Maßnahme erreicht 87% des Ziels" im Abgleich-Klappsection

**Blocker:** `ab_haushaltsjahr` ist in der DB für alle 78 Maßnahmen NULL.
Entweder aus PDF nachparsen oder aus `hsk_jahreswerte` (erstes nicht-null Jahr) ableiten.
`wirksam_ab` (bereits im JSON) kann als Proxy verwendet werden.

### 🟢 Niedrig — HSK: 17 Maßnahmen ohne TP-Zuordnung

17 Maßnahmen haben kein `tp_nr` im JSON (keine Produktverknüpfung in DB).
Beispiele: Nr. 13 (Hortbeiträge), Nr. 19 (Personaloptimierungskonzept), Nr. 46 (Zinsaufwendungen).

Diese tauchen bei keinem TP-Filter auf. Mögliche Lösung:
- Manuelle `tp_nr`-Zuweisung in einem FALLBACK_TP_MAP-Dict in `pipeline_hsk.py`
- Oder: `verantwortlich`-Feld parsen (enthält oft TP-Bezeichnung)

### 🟢 Niedrig — SK-Kategorien unvollständig

Für einige Produkte fehlt die Steuerungskategorie (`steuerungs_kategorie_id = NULL`).
Priorität: TP 09 (Soziales) und TP 11 (Kinder/Jugend).

```bash
python kategorisierung.py  # prüft und ergänzt fehlende Kategorien
```

### 🟢 Niedrig — `ab_haushaltsjahr` aus PDF parsen

Das Feld `hsk_massnahmen.ab_haushaltsjahr` ist für alle Maßnahmen NULL.
In `pipeline_hsk.py` gibt es `apply_fallbacks()` mit `FALLBACK_MASSNAHMEN` —
hier könnten `ab_haushaltsjahr`-Werte ergänzt werden.
Alternativ: `wirksam_ab = min(year for year, val in jahreswerte if val != 0)` (bereits im JSON).

---

## HSK-Datenbasis (Referenz)

### Quelle: HSK-9-2025.pdf (9. Fortschreibung, Beschluss 2023-09-07)

| Kennzahl | Wert |
|----------|------|
| Maßnahmen gesamt | 78 |
| Aktiv | 43 |
| Erledigt | 4 |
| Entfallen | 31 |
| Mit Produktabgleich | 61 |
| Kumuliert 2013–2022 | 40,0 Mio € |
| Plan 2024 | 6,6 Mio € |
| Plan 2025 | 6,4 Mio € |
| Gesamtziel 2013–2025 | ~59,4 Mio € |

### TP-Verteilung der HSK-Maßnahmen

| TP | Bezeichnung | Maßnahmen |
|----|-------------|-----------|
| 01 | Verwaltungsführung | 4 |
| 02 | Kultur, Tourismus und Sport | 6 |
| 03 | Personal / Zentrale Dienste | 7 |
| 04 | Finanzverwaltung | 6 |
| 05 | Öffentliche Flächen und Straßen | 2 |
| 06 | Allgemeine Finanzwirtschaft | 14 |
| 07 | Ordnung und Sicherheit | 3 |
| 08 | Umwelt | 8 |
| 09 | Soziales und Gesundheit | 1 |
| 11 | Kinder-, Jugend- und Familienhilfe | 2 |
| 12 | Einrichtungen Sozialdezernat | 8 |
| — | Ohne TP (übergreifend) | 17 |

---

## Ground Truth (Validierungswerte Haushaltssatzung 2025)

| KK | Beschreibung | Soll-Wert (€) |
|:---|:-------------|-------------:|
| 4 | Erträge | 136.395.290,00 |
| 5 | Aufwendungen | 138.003.230,00 |
| 6 | Einzahlungen | 136.365.830,00 |
| 7 | Auszahlungen | 135.802.480,00 |

Jahresergebnis (Soll): **−1.607.940 €** (geplantes Defizit)

---

## Orsi-Skill — aktuelle Fähigkeiten

`skill/budget_query.py` auf Elestio unterstützt:

| Kategorie | Beispiel |
|-----------|---------|
| Jahressummen | "Gesamtaufwendungen 2025" |
| Teilplan | "Was kostet Soziales 2025?" |
| Produkt | "Ausgaben Kitas 2025" |
| Jahresvergleich | "Soziales 2023 vs 2025" |
| Top-N | "5 größte Ausgabeposten 2025" |
| Steuerung | "Welche Ausgaben sind Pflicht?" |
| Stellenplan | "Wie viele Stellen hat TP 09?" |
| Stellenplan | "Beamtenstruktur Personal 2024 vs 2025" |

**Noch nicht unterstützt:** HSK-Abfragen (Blocker: DB-Upload + Skill-Erweiterung)

---

## Wichtige Design-Entscheidungen

### Warum IST_ERGEBNIS für 2022/2023 im HSK-Abgleich?
Die `hsk_abgleich`-View nutzt `IST_ERGEBNIS` für ≤2023 und `PLAN_ANSATZ` für ≥2024.
Das zeigt tatsächliche Ausgaben (nicht Planwerte) für historische Vergleiche.
2023 IST kann signifikant vom PLAN abweichen (Beispiel Gewässerschutz: IST 287T€ vs. Plan 341T€).

### Warum Monkey-Patching statt direktes Template-Literal-Editing?
Template-Literals in index.html sind durch CRLF + potenzielle Unicode-Zeichen
fehleranfällig. Monkey-Patching erlaubt sichere Erweiterung ohne Template-Eingriff.

### Simulator-Semantik: Was bedeutet kk5_2025?
`kk5_2025` ist der **konsolidierte Planansatz 2025** — historische HSK-Einsparungen
sind bereits eingepreist. Der Simulator modelliert **zusätzliche** Kürzungen
on top des bestehenden Plans. Die blaue Zone zeigt das HSK-2025-Jahresziel
als Referenzpunkt für die Zusatzkùrzung.

---

## Commit-Historie (letzte Meilensteine)

```
c9e32d2  fix: Zone-Bar Sichtbarkeit (helle Farben)
d807595  feat: Stufe C — Drei-Zonen-Visualisierung Simulator
0a21037  fix: HSK TP-Filter (renderHskTable direkt aufrufen)
a0489fc  feat: Simulator-TP-Badge → HSK-Tab Navigation
29d5544  feat: Simulator Stufe A+B (Vorbelastungs-Badges + Szenario-Loader)
774829e  feat: HSK-Tab neben Simulator, Tab umbenannt
dd5411c  feat: HSK-Detail Balkendiagramm + IST/PLAN-Abgleich
419b719  fix: renderHskTable JS-Syntaxfehler (fehlende })
d15999b  feat: HSK Stufe 2 Soll/Ist-Abgleich (stabile Version)
e32b0ed  feat: HSK-Subtab Stufe 1
2366a32  feat: Stellenplan-Abfragen in Orsi-Skill
0f3da2a  feat: Stellenplan 2024+2025 in DB + Personal-Tab
```
