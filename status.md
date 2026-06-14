# Projektstatus: Haushaltsplan Stadt Suhl — Dashboard
<!-- Cortex AI Dashboard Scanner v1 — wird automatisch durch den Sync-Button eingelesen -->

## Meta
id: haushalt-suhl
status: dev
lastUpdate: 2026-06-14
monthlyRevenue: 0
monthlyRunningCost: 0

## Nächste Aktionen
- [ ] HH-Plan 2024 PDF beschaffen → Stellenplan 2023 ergänzen
- [ ] HSK Stufe 3: Zielerreichungsquote implementieren (ab_haushaltsjahr als Baseline)
- [ ] 17 HSK-Maßnahmen ohne TP-Zuordnung manuell zuweisen (FALLBACK_TP_MAP)
- [ ] Orsi-Skill: Bilanz-Abfragen (detect_bilanz, query_bilanz) → Elestio
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

## Offene Punkte
🟡 [Mittel] Stellenplan 2023: Benötigt HH-Plan 2024 PDF (Seiten 893–898)
🟡 [Mittel] HSK Zielerreichungsquote: ab_haushaltsjahr in DB ist NULL für alle 78 Maßnahmen
🟢 [Niedrig] 17 Maßnahmen ohne TP: FALLBACK_TP_MAP in pipeline_hsk.py ergänzen
🟢 [Niedrig] Orsi-Skill Bilanz-Abfragen (Jahresabschluss) noch nicht implementiert
🟢 [Niedrig] Jahresabschluss 2022+ sobald verfügbar → pipeline_bilanz.py erweitern

## KPIs
Haushaltswerte: 89.808
ETL-Jahrgänge: 2023, 2024, 2025
Dashboard-Tabs: 8 (Überblick, Details, Personal, Jahresvergleich, Zeitreihe, HSK, Simulator, Vermögen)
HSK-Maßnahmen: 78 (43 aktiv, 4 erledigt, 31 entfallen)
HSK-Kumuliert 2013–2022: 40,0 Mio €
Jahresergebnis 2025 (Soll): −1.607.940 €
Finanzierungssaldo 2025 (Soll): +563.350 € (Einz. 136,4 Mio − Ausz. 135,8 Mio)
Bilanzsumme 2021 (Stadt): 279.459 T€ = 279,5 Mio € (EK-Quote 53,9 %, VB 16,6 Mio €, Entwicklung seit 2013: +38.365 T€)
EB KDS Bilanzsumme 2024: 5,59 Mio € (EK 690 T€, Jahresverlust −409 T€, 110 MA)
Beteiligungen: 15 Gesellschaften (14 direkt/mittelbar + EB KDS); SWSZ-Umsatz 59 Mio € (2024); EAV-Kette → CCS 4.052 T€; SNG-Defizit 2.852 T€ quersubventioniert

## Notizen
Live unter https://cortex-ai-solutions.github.io/Suhler-Haushalt-/ — Dashboard mit 8 Tabs + mobiler Hamburger-Navigation. Orsi-Skill budget_query.py auf Elestio unterstützt Haushalt + Stellenplan + HSK. Vermögen-Tab: Bilanz mit Level-3-Detail (160 Positionen: Sachanlagen 10 Kategorien, Finanzanlage 8, Forderungen 7, VB 11) + Bilanzentwicklung seit 2013. EB KDS Kennzahlen (2021–2024). Evidenzbasis-Infothek live: 4 Quellen. Kritische Constraints: CRLF in index.html, kein Unicode in JS-Strings, Monkey-Patching für Template-Literal-Sicherheit. Server: ssp-framework-2-u68900.vm.elestio.app, DB: /opt/omni-haushalt/suhl_haushalt.db
