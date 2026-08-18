# Projektstatus: Haushaltsplan Stadt Suhl — Dashboard
<!-- Cortex AI Dashboard Scanner v1 — wird automatisch durch den Sync-Button eingelesen -->

## Meta
id: haushalt-suhl
status: dev
lastUpdate: 2026-08-05
monthlyRevenue: 0
monthlyRunningCost: 0

## Nächste Aktionen
- [ ] HH-Plan 2024 PDF beschaffen → Stellenplan 2023 ergänzen
- [ ] HSK Stufe 3: Zielerreichungsquote implementieren (ab_haushaltsjahr als Baseline)
- [ ] 17 HSK-Maßnahmen ohne TP-Zuordnung manuell zuweisen (FALLBACK_TP_MAP)
- [ ] bodyfit-lead-analyzer aus app-openclaw-gateway-1 in eigenen Container auslagern (Kopplungsrisiko)
- [x] Orsi-Skill: Personalausgaben, Beteiligungen, Bilanz-Abfragen (detect_bilanz, query_bilanz) → auf Elestio deployed (2026-08-05)
- [x] skill/SKILL.md erstellt + versioniert (Skill-Discovery war unvollständig) + auf Elestio deployed (2026-08-05)
- [x] Orsi-Gateway auf Elestio neu gestartet, damit neuer Skill-Katalog geladen wird (2026-08-05)
- [x] memory_budget_suhl.md (Orsis eigenes Gedächtnis) um neue Fähigkeiten ergänzt + deployed (2026-08-05)
- [x] D) Personalquote: KPI-Chip + Zeitreihe 2021-2025 im Personal-Tab erledigt
- [x] ETL-Pipeline für 2023, 2024, 2025 abgeschlossen (89.808 Haushaltswerte)
- [x] Dashboard mit 8 Tabs live auf GitHub Pages
- [x] Stellenplan 2024 + 2025 in DB und Personal-Tab
- [x] HSK-Integration Stufe 1+2 (Tab + Soll/Ist-Abgleich)
- [x] Konsolidierungs-Simulator mit Drei-Zonen-Balken (Stufe A+B+C)
- [x] Orsi-Skill: Haushalt + Stellenplan-Abfragen funktionieren auf Elestio
- [x] Orsi-Skill HSK: detect_hsk(), query_hsk_massnahmen(), format_hsk() implementiert + Elestio
- [x] Evidenzbasis-Infothek: 4 Quellen mit pdfminer extrahiert + Detail-Toggle
- [x] FINANZPLANUNG-Bug behoben + Finanzplan-KPIs im Überblick-Tab
- [x] HSK-Tab-Sichtbarkeits-Bug + Personal-TP-Accordion + Mobile-Navigation
- [x] Vermögen-Tab (8. Tab): Bilanz 2020/2021 + EB KDS 2022-2024 mit Charts + Level-3-Detail
- [x] Beteiligungen-Subtab: 15 Gesellschaften, Sankey Finanzströme 2024, Kennzahlen-Tabelle, JÜ-Chart
- [x] A) Haushaltslage + C) Investitionen & Substanzerhalt im Zeitreihe-Tab (3 neue Charts)
- [x] B) Schuldenentwicklung 2013–2026: pipeline_schulden.py + Chart im Vermögen-Tab

## Nächste Feature-Iteration: "Was Stadträte wirklich brauchen"

### A) Haushaltslage im Zeitverlauf — ✅ ERLEDIGT
- Zeitreihe-Tab: KPI-Chips (Jahresergebnis, Finanzierungssaldo) + Gruppenbalken-Chart 2021–2025
- Daten aus DATA.zeitreihe (IST 2021–2023, Plan 2024/2025), kein neuer ETL

### B) Schulden und Eigenkapital — ✅ ERLEDIGT
- pipeline_schulden.py: schulden_entwicklung-Tabelle (14 Einträge 2013–2026, Quelle S.83)
- Vermögen-Tab Bilanz-Subtab: Schuldenentwicklung-Karte mit 3 KPI-Chips + Dual-Achsen-Chart
- Schlüsselbefund: Schuldenstand 2013=54.419 T€ → 2025=2.020 T€ (Plan), 56 €/EW, Keine Neuverschuldung seit 2013

### C) Investitionen und Substanzerhalt — ✅ ERLEDIGT
- Zeitreihe-Tab: Balkendiagramm AfA vs. Investitions-Auszahlungen + Investitionsquoten-Linie
- Schlüsselbefund: 2024 Investitionsquote=42% → Substanzverzehr (in Chart rot markiert)

### D) Personalquote — ERLEDIGT (2026-06-15)
- pers-kpi-quote KPI-Chip + Zeitreihe 2021-2025 im Personal-Tab
- Werte: 26,0 % (2021 IST) -> 24,2 % (2025 Plan); stabil 24-26 %

### Zweckverbände — ERLEDIGT (2026-06-15)
- pipeline_zweckverband.py: 13 Verbände in DB (6 Kategorien)
- patch_zweckverband_tab.py: 4. Subtab im Vermögen-Tab mit KPI-Chips + kategorisierter Tabelle

## Offene Punkte
🟡 [Mittel] Stellenplan 2023: Benötigt HH-Plan 2024 PDF (Seiten 893–898)
🟡 [Mittel] HSK Zielerreichungsquote: ab_haushaltsjahr in DB ist NULL für alle 78 Maßnahmen
🟡 [Mittel] bodyfit-lead-analyzer läuft im selben Container wie Orsi-Gateway → jeder Skill-Neustart bounct auch bodyfit-Telegram-Listener (self-heilt via stündlichem Watchdog-Cron, aber Risikofenster). Kundendashboard bodyfit-app selbst ist unabhängig und nicht betroffen.
🟢 [Niedrig] 17 Maßnahmen ohne TP: FALLBACK_TP_MAP in pipeline_hsk.py ergänzen
🟢 [Niedrig] Orsi-Skill Bilanz-Abfragen: Datenbasis nur 2020/2021 (neuere Bilanz fehlt)
🟢 [Niedrig] Jahresabschluss 2022+ sobald verfügbar → pipeline_bilanz.py erweitern
🟢 [Niedrig] Orsi/Telegram: Health-Monitor stuft Verbindung nach 30 Min Inaktivität faelschlich als "stuck" ein und startet Kanal neu (kann Nachrichten verschlucken). Ursache identifiziert (gateway.channelHealthCheckMinutes, hartcodierte 30-Min-Schwelle), bewusst nicht geändert (2026-08-05) — einzige Abhilfe wäre Health-Monitor komplett zu deaktivieren (betrifft alle Kanäle)

## KPIs
Schulden 2025 (Plan): 2.020 T€ = 56 €/EW; Schuldenabbau 2013→2025: −52.399 T€ (−96 %)
Haushaltswerte: 89.808
ETL-Jahrgänge: 2023, 2024, 2025
Dashboard-Tabs: 8; Vermögen-Tab Subtabs: 4 (Bilanz, EB KDS, Beteiligungen, Zweckverbände)
Personalquote 2025 Plan: 24,2 % | IST 2023: 26,1 %
Zweckverbände: 13 (4 Wasser, 3 Gewässer, 1 Rettung, 1 Abfall, 2 Energie, 2 Sonstiges)
HSK-Maßnahmen: 78 (43 aktiv, 4 erledigt, 31 entfallen)
HSK-Kumuliert 2013–2022: 40,0 Mio €
Jahresergebnis 2025 (Soll): −1.607.940 €
Finanzierungssaldo 2025 (Soll): +563.350 € (Einz. 136,4 Mio − Ausz. 135,8 Mio)
Bilanzsumme 2021 (Stadt): 279.459 T€ = 279,5 Mio € (EK-Quote 53,9 %, VB 16,6 Mio €, Entwicklung seit 2013: +38.365 T€)
EB KDS Bilanzsumme 2024: 5,59 Mio € (EK 690 T€, Jahresverlust −409 T€, 110 MA)
Beteiligungen: 15 Gesellschaften (14 direkt/mittelbar + EB KDS); SWSZ-Umsatz 59 Mio € (2024); EAV-Kette → CCS 4.052 T€; SNG-Defizit 2.852 T€ quersubventioniert

## Notizen
Live unter https://cortex-ai-solutions.github.io/Suhler-Haushalt-/ — Dashboard mit 8 Tabs + mobiler Hamburger-Navigation. Orsi-Skill budget_query.py auf Elestio (Docker-Pfad: /app/skills/budget-skill/budget_query.py) unterstützt Haushalt + Stellenplan + HSK + Personalausgaben + Beteiligungen + Bilanz/Rückstellungen (deployed 2026-08-05). Vermögen-Tab: Bilanz mit Level-3-Detail (160 Positionen: Sachanlagen 10 Kategorien, Finanzanlage 8, Forderungen 7, VB 11) + Bilanzentwicklung seit 2013. EB KDS Kennzahlen (2021–2024). Evidenzbasis-Infothek live: 4 Quellen. Kritische Constraints: CRLF in index.html, kein Unicode in JS-Strings, Monkey-Patching für Template-Literal-Sicherheit. Server: ssp-framework-2-u68900.vm.elestio.app, DB: /opt/omni-haushalt/suhl_haushalt.db

**Elestio-Infrastruktur (Stand 2026-08-05):** Skill-Katalog wird von Orsi nur beim Gateway-Boot gescannt (kein Hot-Reload) — jede Skill-Änderung (budget_query.py, SKILL.md) erfordert Container-Neustart (`kill <gateway-PID>`, RestartPolicy: always fängt das auf). SKILL.md (Frontmatter-`description`) steuert, ob Orsi einen Skill überhaupt erwägt; separat davon liest Orsi Wissen aus eigenen Memory-Dateien (`/home/node/.openclaw/workspace/memory/memory_budget_suhl.md`, live pro Anfrage gelesen, kein Neustart nötig) — beide lokal versioniert unter `skill/SKILL.md` und `skill/memory_budget_suhl.md`. app-openclaw-gateway-1 hostet NICHT nur Orsi, sondern auch den bodyfit-lead-analyzer-Telegram-Listener (Kopplungsrisiko, siehe Offene Punkte). Server hat insgesamt 7 Container (Orsi, bodyfit-app/-db/-lead-agent/-caddy, ssb-ar-portal, elestio-nginx/-postfix), 2 vCPU/3,7GB RAM, ~2,4GB frei.
