# memory_budget_suhl.md — Haushaltsplan Stadt Suhl

**Zweck:** Wissen ueber den budget-suhl Skill und wann/wie ich ihn einsetze.

---

## Was ist budget-suhl?

Skill fuer den offiziellen Haushaltsplan der Stadt Suhl (Thueringen).
Datengrundlage: SQLite-DB /opt/omni-haushalt/suhl_haushalt.db
mit ~175.000 Haushaltswerten aus den Haushaltssatzungen 2023-2025
PLUS Stellenplan, Haushaltssicherungskonzept (HSK), Beteiligungen der Stadt
und Bilanz-Positionen.

**Staerken:**
- Echte offizielle Zahlen (gem. Haushaltssatzung §1)
- Ergebnisplan (Ertraege/Aufwendungen) + Finanzplan (Ein-/Auszahlungen)
- Jahresvergleiche 2023-2025, IST-Daten 2021/2022 verfuegbar
- Rechtsgrundlagen zu Pflichtaufgaben (SGB VIII, SGB XII, ThuerKitaG ...)
- Steuerungskategorien: Pflicht vs. freiwillig
- Stellenplan: Planstellen je Besoldungsgruppe (A6-B5, E1-E15, SuE), je Teilplan, 2024+2025
- Personalausgaben: Personalkosten in Euro + Personalquote, nach Kontengruppe aufgeschluesselt
- HSK: 78 Konsolidierungs-/Sparmassnahmen (9. Fortschreibung), Umsetzungsstatus + Soll/Ist
- Beteiligungen: Kennzahlen (Umsatz, Jahresergebnis) von 15 staedtischen Gesellschaften
- Bilanz: Rueckstellungen, Verbindlichkeiten, Eigenkapital (nur 2020/2021 verfuegbar)

---

## Wann nutze ich den Skill?

**Aktivierungsmuster:**
- Fragen zum Haushalt der Stadt Suhl
- 'Was hat Suhl fuer [Bereich] ausgegeben?'
- 'Wie hoch ist das Defizit der Stadt Suhl?'
- 'Vergleiche Soziales 2023 und 2025'
- 'Was sind die groessten Ausgabeposten?'
- 'Welche Leistungen sind Pflichtaufgaben?'
- 'Wie viel investiert Suhl in Schulen / Kitas / Strassen?'
- 'Wie viele Mitarbeiter hat Suhl?' (Stellenplan = Anzahl Stellen)
- 'Wie viele Beamte / Tarifbeschaeftigte gibt es?'
- 'Welche Besoldungsgruppen hat die Feuerwehr?'
- 'Stellenplan 2024 vs 2025'
- 'Wie hoch sind die Personalkosten / Personalausgaben?' (Geld, NICHT Stellenanzahl!)
- 'Wie hoch ist die Personalquote?'
- 'Was hat Suhl durch das HSK gespart?' / 'Welche Sparmassnahmen gibt es?'
- 'Welche Gewinne erwirtschaften die staedtischen Beteiligungen/Gesellschaften?'
- 'Wie hat sich die GEWO/SWSZ/EBKDS entwickelt?'
- 'Gibt es Rueckstellungen?' / 'Wie hoch sind die Verbindlichkeiten der Stadt?'

**Wichtig — Stellenplan vs. Personalausgaben nicht verwechseln:**
- "Wie viele Stellen/Mitarbeiter/Beamte gibt es" → Stellenplan (Anzahl)
- "Wie hoch sind die Personalkosten/-ausgaben/-quote" → Personalausgaben (Euro)

**Nicht fuer:**
- Andere Staedte/Kommunen (nur Suhl)
- Echtzeit-Buchhaltung, Einzel-Rechnungen oder Vertragsdetails
- Aktuelle Bilanz (nur 2020/2021 in der DB, keine neueren Jahresabschluesse)

---

## Befehle

### Haushalt (Finanzen)
budget-suhl "Gesamthaushalt 2025"
budget-suhl "Ausgaben fuer Soziales 2025"
budget-suhl "Kinder Jugend Familien 2024"
budget-suhl "Soziales 2023 vs 2025"
budget-suhl "Top 5 Ausgaben 2025"
budget-suhl "Welche Ausgaben sind Pflichtaufgaben 2025"
budget-suhl "Freiwillige Leistungen 2025"
budget-suhl "Welche Jahre sind verfuegbar"
budget-suhl --json "Gesamthaushalt 2025"

### Stellenplan (Personalstellen / Headcount)
budget-suhl "Wie viele Planstellen hat Suhl 2025"
budget-suhl "Wie viele Beamte gibt es 2025"
budget-suhl "Wie viele Mitarbeiter hat die Feuerwehr"
budget-suhl "Stellenplan 2024 vs 2025"
budget-suhl "Welche Besoldungsgruppen gibt es im Sozialbereich"

### Personalausgaben (Personalkosten in Euro)
budget-suhl "Finde alle Personalausgaben 2025"
budget-suhl "Personalkosten 2023 vs 2025"
budget-suhl "Wie hoch ist die Personalquote 2025?"
budget-suhl "Dienstbezuege im Sozialdezernat 2025"

### Haushaltssicherungskonzept (HSK)
budget-suhl "HSK Uebersicht"
budget-suhl "Wie viel hat Suhl durch das HSK gespart?"
budget-suhl "Welche HSK-Massnahmen gibt es fuer Soziales?"
budget-suhl "HSK Massnahmen aktiv"

### Beteiligungen (staedtische Gesellschaften)
budget-suhl "Welche Gewinne erwirtschaften die Beteiligungen?"
budget-suhl "Beteiligungen Uebersicht 2024"
budget-suhl "Wie hat sich die GEWO entwickelt?"
budget-suhl "Jahresergebnis SWSZ"

### Bilanz (nur 2020/2021 verfuegbar)
budget-suhl "Gibt es Rueckstellungen?"
budget-suhl "Wie hoch sind die Verbindlichkeiten?"
budget-suhl "Bilanzuebersicht 2021"
budget-suhl "Eigenkapital der Stadt"

---

## Haushaltliche Eckwerte 2025 (Ground Truth S.1 Haushaltssatzung)

Ordentliche Ertraege (KK4):    136.395.290 EUR
Ordentliche Aufwendungen (KK5): 138.003.230 EUR
Jahresergebnis:                  -1.607.940 EUR (geplantes Defizit)
Einzahlungen (KK6):            136.365.830 EUR
Auszahlungen (KK7):            135.802.480 EUR
Personalquote 2025 (Plan):        24,2 % der Aufwendungen (KK5)

## Stellenplan-Eckwerte 2025 (Plan-Ansatz)

Planstellen gesamt:  490,238
davon Beamte:         77,000  (15,7%)
davon Tarif:         413,238  (84,3%)

Groesste Teilplaene nach Stellen:
  TP07 Ordnung/Sicherheit: 102,675 (davon 49 Beamte = Feuerwehr + Ordnungsamt)
  TP09 Soziales:            74,709
  TP03 Personal/ZD:         70,420
  TP11 Kinder/Jugend:       54,736

Beamte-Besoldungsgruppen: A7 (19), A8 (16), A11 (12), A9 (8), A10 (6), A13 (5), ...
Tarif-Entgeltgruppen: E9a (86,4), E9b (55,9), E10 (49,8), E6 (47,8), E5 (32,5), ...

## HSK-Eckwerte (9. Fortschreibung, Beschluss 2023-09-07)

78 Massnahmen gesamt: 43 aktiv, 4 erledigt, 31 entfallen
Kumuliert 2013-2022:  40,0 Mio EUR
Plan 2024:             6,6 Mio EUR
Plan 2025:             6,4 Mio EUR
Gesamtziel 2013-2025: ~59,4 Mio EUR

## Beteiligungen-Eckwerte (Jahresergebnisse 2024, in T EUR)

Positiv: Stadtwerke SWSZ (+5.155), SWB (+2.865), GeWo (+2.276), KIV (+1.460),
         ITM (+920), SWSZ-Netz (+336), SSB (+83), Suhler Werkstaetten (+69), ...
Negativ: EB KDS (-409), CCS (-1.644), SNG (-2.852, quersubventioniert)
15 staedtische Gesellschaften insgesamt.

## Bilanz-Eckwerte 2021 (nur 2020/2021 verfuegbar!)

Aktiva:  Anlagevermoegen 257,6 Mio EUR, Umlaufvermoegen 20,9 Mio EUR
Passiva: Eigenkapital 150,7 Mio EUR, Sonderposten 89,9 Mio EUR,
         Rueckstellungen 21,4 Mio EUR, Verbindlichkeiten 16,6 Mio EUR

---

## Datenbasis

DB: /opt/omni-haushalt/suhl_haushalt.db (SQLite)
IST-Ergebnisse: 2021, 2022, 2023
Plan-Ansaetze: 2023, 2024, 2025
Finanzplanung: 2026, 2027, 2028
Stellenplan: 2024 (Plan+Ist-30.06) und 2025 (Plan) — 2023 noch nicht verfuegbar
HSK: 78 Massnahmen, Jahreswerte 2013-2025
Beteiligungen: 15 Gesellschaften, Kennzahlen 2021-2024
Bilanz: nur 2020/2021 (Aktiva/Passiva, 2 Ebenen)
12 Teilplaene, ~300 Produkte, kommunale Doppik ThuerKDG
Steuerungskategorien: PFLICHT_STRIKT, PFLICHT_ERMESSEN, FREIWILLIG, UEBERTRAGEN

## Die 12 Teilplaene

TP01 Verwaltungsfuehrung
TP02 Kultur, Tourismus und Sport
TP03 Personal und Zentrale Dienste
TP04 Finanzverwaltung
TP05 Oeffentliche Flaechen und Strassen
TP06 Allgemeine Finanzwirtschaft
TP07 Ordnung und Sicherheit
TP08 Umwelt
TP09 Soziales und Gesundheit
TP10 Schultraegeraufgaben
TP11 Kinder-, Jugend- und Familienhilfe
TP12 Einrichtungen Sozialdezernat

---

## Web-Dashboard (zusaetzlich)

https://cortex-ai-solutions.github.io/Suhler-Haushalt-/
Features: Sankey, Treemap, Jahresvergleich, Detail-Ansicht, Personal-Tab
(inkl. Personalquote-Zeitreihe), Stellenplan-Merkzettel, HSK-Tab +
Konsolidierungs-Simulator, Vermoegen-Tab (Bilanz, Beteiligungen, Zweckverbaende).

## Aktualisiert

2026-08-05 von Tobias (via Claude Code) — Personalausgaben, HSK, Beteiligungen
und Bilanz/Rueckstellungen als neue Faehigkeiten ergaenzt (skill/budget_query.py
+ SKILL.md erweitert und auf Elestio deployed).
