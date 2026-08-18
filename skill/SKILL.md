---
name: budget-suhl
description: "Haushalt und Finanzen der Stadt Suhl (2021-2028): Ausgaben, Einnahmen, Teilplaene, Jahresvergleiche, Top-Ausgaben, Pflicht- vs. freiwillige Leistungen (Haushaltssatzung). Ausserdem: Stellenplan/Personalstellen (Planstellen, Beamte, Tarifbeschaeftigte, Besoldungsgruppen), Personalausgaben/Personalkosten/Personalquote, Haushaltssicherungskonzept HSK (Konsolidierungs-/Sparmassnahmen), Beteiligungen der Stadt (Gewinne/Verluste/Kennzahlen der staedtischen Gesellschaften wie Stadtwerke, GeWo, EBKDS, SNG), Bilanz (Ruecklagen, Rueckstellungen, Verbindlichkeiten, Forderungen, Eigenkapital, Bilanzuebersicht 2020/2021). Verwende diesen Skill bei jeder Frage zu Haushalt, Finanzen, Personal, Stellen, HSK, Beteiligungen oder Bilanz der Stadt Suhl."
metadata: { "openclaw": { "emoji": "🏛️" } }
---

# budget-suhl — Haushaltsplan Stadt Suhl

Offizielle Haushaltsdaten der Stadt Suhl auf Basis der Haushaltssatzungen 2023-2025.
Kommunale Doppik (ThuerKDG): Ergebnisplan (Ertraege/Aufwendungen) + Finanzplan (Ein-/Auszahlungen).

## Befehle

### Gesamthaushalt / Teilplan
```bash
budget-suhl "Gesamthaushalt 2025"
budget-suhl "Haushalt 2023"
budget-suhl "Ausgaben fuer Soziales 2025"
budget-suhl "Was kostet Kultur und Sport 2024?"
budget-suhl "Kinder Jugend Familien 2025"
budget-suhl "Ordnung und Sicherheit 2024"
```

### Jahresvergleich
```bash
budget-suhl "Soziales 2023 vs 2025"
budget-suhl "Entwicklung Schulen 2023 vs 2025"
```

### Top-N / Steuerungskategorien
```bash
budget-suhl "Top 5 Ausgaben 2025"
budget-suhl "Die 10 groessten Ausgabeposten 2024"
budget-suhl "Welche Ausgaben sind Pflichtaufgaben 2025"
budget-suhl "Freiwillige Leistungen 2025"
```

### Stellenplan (Personalstellen / Headcount — NICHT Personalkosten)
```bash
budget-suhl "Wie viele Planstellen hat Suhl 2025?"
budget-suhl "Wie viele Beamte gibt es 2025?"
budget-suhl "Stellenplan 2024 vs 2025"
budget-suhl "Wie viele Stellen hat die Feuerwehr?"
budget-suhl "Besoldungsgruppen Beamte 2025"
```

### Personalausgaben (Personalkosten in Euro — NICHT Stellenanzahl)
```bash
budget-suhl "Finde alle Personalausgaben 2025"
budget-suhl "Personalkosten 2023 vs 2025"
budget-suhl "Wie hoch ist die Personalquote 2025?"
budget-suhl "Dienstbezuege im Sozialdezernat 2025"
```

### Haushaltssicherungskonzept (HSK)
```bash
budget-suhl "HSK Uebersicht"
budget-suhl "Wie viel hat Suhl durch das HSK gespart?"
budget-suhl "Welche HSK-Massnahmen gibt es fuer Soziales?"
budget-suhl "HSK Massnahmen aktiv"
```

### Beteiligungen (staedtische Gesellschaften: Stadtwerke, GeWo, EBKDS, SNG, CCS, ...)
```bash
budget-suhl "Welche Gewinne erwirtschaften die Beteiligungen?"
budget-suhl "Beteiligungen Uebersicht 2024"
budget-suhl "Wie hat sich die GEWO entwickelt?"
budget-suhl "Jahresergebnis SWSZ"
```

### Bilanz (Ruecklagen, Verbindlichkeiten, Eigenkapital — Datenbasis nur 2020/2021)
```bash
budget-suhl "Gibt es Rueckstellungen?"
budget-suhl "Wie hoch sind die Verbindlichkeiten?"
budget-suhl "Bilanzuebersicht 2021"
budget-suhl "Eigenkapital der Stadt"
```

### Verfuegbare Daten / JSON fuer Weiterverarbeitung
```bash
budget-suhl "Welche Jahre sind verfuegbar"
budget-suhl --json "Gesamthaushalt 2025"
```

## Haushaltliche Eckwerte 2025 (Ground Truth §1 Haushaltssatzung)
- Ordentliche Ertraege:       136.395.290 EUR
- Ordentliche Aufwendungen:   138.003.230 EUR
- Jahresergebnis:              -1.607.940 EUR (geplantes Defizit)
- Personalquote 2025 (Plan):   24,2 % der Aufwendungen (KK5)

## Datenbasis
- Datenbank: /opt/omni-haushalt/suhl_haushalt.db (SQLite)
- Haushalt: IST-Ergebnisse 2021-2023, Plan 2023-2025, Finanzplanung 2026-2028 —
  12 Teilplaene, ~300 Produkte, kommunale Doppik ThuerKDG
- Stellenplan: 2024 (Plan+Ist), 2025 (Plan) — 2023 noch nicht verfuegbar
- HSK: 78 Massnahmen (9. Fortschreibung, Beschluss 2023-09-07)
- Beteiligungen: 15 staedtische Gesellschaften, Kennzahlen 2021-2024
- Bilanz: Bilanzpositionen nur fuer 2020/2021 verfuegbar (Aktiva/Passiva, 2 Ebenen)

## Pflege-Hinweis
Diese Datei ist im Projekt-Repo unter `skill/SKILL.md` versioniert und wird per
`scp` auf den Server gespiegelt (siehe CLAUDE.md, Server-Update-Prozedur). Das
`description`-Feld im Frontmatter entscheidet, ob Orsi diesen Skill ueberhaupt
fuer eine Nutzerfrage in Betracht zieht — bei jeder Erweiterung von
`budget_query.py` um neue Fragetypen muss diese Datei mit aktualisiert und
neu hochgeladen werden, sonst "kennt" Orsi die neue Faehigkeit nicht.
