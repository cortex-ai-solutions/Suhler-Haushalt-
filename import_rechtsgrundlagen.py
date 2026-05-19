"""
import_rechtsgrundlagen.py
Reichert die Datenbank mit zitierfähigen gesetzlichen Grundlagen an:
  1. Spalte 'rechtsgrundlage' in steuerungs_kategorien (Bindungsrahmen je Kategorie)
  2. Neue Tabelle gesetze_katalog (Vollname, Abk., Fundstelle, Kernaussage)
  3. Aktualisierung produkte.rechtsgrundlage mit präzisen §§-Zitaten

Herkunft der Kategorisierungen:
  Die SK-Zuordnungen wurden auf Basis von Bundesrecht (SGB II/VIII/IX/XII, GG Art. 28 Abs. 2),
  Thüringer Landesrecht (ThürKO, ThürKitaG, ThürSchulG, ThürBKG u.a.) und dem
  qualitativen Kontext aus haushalt_rechtliche_details.md / haushalt_sozialrechtliche_details.md
  erarbeitet. Für rechtssichere Argumentation gegenüber Aufsichtsbehörden empfiehlt sich
  die Abstimmung mit einem Kommunalrechtler.
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "suhl_haushalt_2025.db")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Gesetzeskatalog
# ─────────────────────────────────────────────────────────────────────────────

GESETZE = [
    # (kuerzel, vollname, rechtsebene, fundstelle_kuerzel, kernaussage_kommunal)
    ("GG",
     "Grundgesetz für die Bundesrepublik Deutschland",
     "BUND",
     "BGBl. 1949 S. 1, zul. geänd. 2020",
     "Art. 28 Abs. 2 GG: Verfassungsgarantie kommunaler Selbstverwaltung. "
     "Unterscheidet freiwillige Selbstverwaltungsaufgaben (Kernbereich der Garantie) "
     "von übertragenen Pflichtaufgaben. Einschränkungen nur durch formelles Gesetz."),

    ("ThürKO",
     "Thüringer Kommunalordnung",
     "LAND",
     "GVBl. TH 2003, S. 41, zul. geänd. 2024",
     "§ 2 ThürKO: Kommunale Selbstverwaltungsgarantie (freiwillige Aufgaben). "
     "§ 3 ThürKO: Unterscheidung Pflichtaufgaben ohne Weisung / Auftragsangelegenheiten. "
     "§ 5 ThürKO: Personalhoheit des Hauptverwaltungsbeamten. "
     "§ 75 ThürKO: Kreditverpflichtungen – striktes Gebot zur Haushaltssicherung. "
     "§ 92 ff. ThürKO: Grundsätze der Haushaltswirtschaft (Wirtschaftlichkeit, Sparsamkeit)."),

    ("ThürGemHV",
     "Thüringer Gemeindehaushaltsverordnung (Doppik)",
     "LAND",
     "GVBl. TH 2008, S. 491, zul. geänd. 2022",
     "Regelt die doppische Haushaltswirtschaft der Thüringer Kommunen. "
     "Grundlage für Ergebnis- und Finanzhaushalt, Produkthaushalt und Controlling. "
     "Keine unmittelbare Leistungspflicht, aber Rahmenbedingung jeder Budgetentscheidung."),

    ("ThürFAG",
     "Thüringer Finanzausgleichsgesetz",
     "LAND",
     "GVBl. TH 2021, S. 294, zul. geänd. 2024",
     "§ 7 ThürFAG: Allgemeine Schlüsselzuweisungen (hauptsächliche Einnahmequelle Suhls). "
     "Einwohnerzahl zum 31.12. des Vorvorjahres (§ 30 ThürFAG) ist Berechnungsgrundlage. "
     "Erhöhte Soziallastenansätze fließen nicht zweckgebunden; Allokation liegt beim Stadtrat."),

    ("ThürKAG",
     "Thüringer Kommunalabgabengesetz",
     "LAND",
     "GVBl. TH 1991, S. 169, zul. geänd. 2023",
     "Ermächtigungsgrundlage für kommunale Steuern (Hebesätze Grundsteuer A/B, Gewerbesteuer), "
     "Gebühren und Beiträge. Hebesatzsatzungen beschließt der Stadtrat autonom."),

    ("ThürSchulG",
     "Thüringer Schulgesetz",
     "LAND",
     "GVBl. TH 1993, S. 445, zul. geänd. 2024",
     "§ 13 ThürSchulG: Gemeinden als sächliche Schulträger (Gebäude, Ausstattung). "
     "§ 14 ThürSchulG: Schulnetzplan – Beschlussrecht des Stadtrats. "
     "§ 40 ThürSchulG: Pflicht zur Bereitstellung geeigneter Schulgebäude für Grundschulen. "
     "§ 44 ThürSchulG: Förderschulen. § 69 ThürSchulG: Schülerbeförderungspflicht. "
     "Ausstattungsstandard und Baurhythmus liegen im kommunalen Ermessen."),

    ("ThürKitaG",
     "Thüringer Kindertagesbetreuungsgesetz",
     "LAND",
     "GVBl. TH 2010, S. 2, zul. geänd. 2023",
     "§ 1 ThürKitaG: Pflicht zur Vorhaltung ausreichender Plätze (Rechtsanspruch der Eltern ab 1 Jahr). "
     "§ 7 ThürKitaG: Betriebskostenförderung freier Träger – Gemeinde erstattet das ungedeckte Defizit; "
     "Grundanspruch der Träger, aber Höhe über Finanzierungsrichtlinie steuerbar. "
     "§ 15 ThürKitaG: Mindestanforderungen an Räumlichkeiten. "
     "§ 16 ThürKitaG: Mindestpersonalschlüssel (nicht unterschreitbar). "
     "§ 29 Abs. 3 ThürKitaG: Verpflegungskosten zu 100 % von Eltern zu tragen."),

    ("ThürBKG",
     "Thüringer Brand- und Katastrophenschutzgesetz",
     "LAND",
     "GVBl. TH 2008, S. 183, zul. geänd. 2023",
     "§ 2 ThürBKG: Pflichtaufgabe der Gemeinde – Aufstellung und Unterhaltung leistungsfähiger "
     "Feuerwehr. Keine Ausnahme, keine Unterschreitung der Soll-Stärken. "
     "§ 6 ThürBKG: Ausrüstungs- und Ausstattungspflicht. "
     "Ermessen bei Fahrzeugbeschaffungszeitpunkt und Hallenstandort."),

    ("ThürRettG",
     "Thüringer Rettungsdienstgesetz",
     "LAND",
     "GVBl. TH 2016, S. 166, zul. geänd. 2022",
     "Pflicht zur Sicherstellung des Rettungsdienstes als Pflichtaufgabe des Landkreises / "
     "der kreisfreien Stadt. Hilfsfristen sind gesetzlich vorgegeben (§ 7 ThürRettG). "
     "Finanzierung über Benutzungsgebühren der Krankenkassen (§ 14 ThürRettG)."),

    ("ThürGDG",
     "Thüringer Gesundheitsdienstgesetz",
     "LAND",
     "GVBl. TH 1992, S. 343, zul. geänd. 2021",
     "Pflicht zur Vorhaltung eines Gesundheitsamts (§ 1 ThürGDG). "
     "Aufgaben: amtsärztlicher Dienst, Infektionsschutz, Kinder- und Jugendgesundheit. "
     "Pflichtaufgabe, Umfang im Ermessen der Behörde soweit keine Bundesregelungen (IfSG) greifen."),

    ("ThürOBG",
     "Thüringer Ordnungsbehördengesetz",
     "LAND",
     "GVBl. TH 2000, S. 226, zul. geänd. 2023",
     "Rechtsgrundlage für Ordnungsamt und allgemeine Gefahrenabwehr. "
     "Pflichtige Aufgaben (Gefahrenabwehr) und Ermessensaufgaben (Kontrollen, Sondernutzungen). "
     "Überlagert durch Bundes-Spezialgesetze (GewO, StrVG etc.)."),

    ("ThürStrG",
     "Thüringer Straßengesetz",
     "LAND",
     "GVBl. TH 1993, S. 273, zul. geänd. 2024",
     "§ 10 ThürStrG: Unterhaltungspflicht für Gemeindestraßen. "
     "Pflicht dem Grunde nach; Standard (Belagsqualität, Erneuerungsintervall) im Ermessen. "
     "Verkehrssicherungspflicht (§ 10 Abs. 3) ist strikt – Verletzung begründet Amtshaftung."),

    ("ThürNatSchG",
     "Thüringer Gesetz zur Sicherung des Naturhaushalts und zur Entwicklung der Landschaft "
     "(Thüringer Naturschutzgesetz)",
     "LAND",
     "GVBl. TH 2006, S. 421, zul. geänd. 2023",
     "Pflicht zur Biotopkartierung und Schutzgebietsausweisung als untere Naturschutzbehörde. "
     "Grünanlagen-Pflege über das gesetzliche Maß hinaus ist freiwillig."),

    ("ThürWG",
     "Thüringer Wassergesetz",
     "LAND",
     "GVBl. TH 2009, S. 648, zul. geänd. 2023",
     "Umsetzung WHG auf Landesebene. Gewässerunterhaltungspflicht (§ 38 WHG) liegt bei Gemeinden "
     "für Gewässer 3. Ordnung. Hochwasserschutz: Pflichtaufgabe, Umfang durch Risikoeinschätzung bestimmt."),

    ("ThürBestG",
     "Thüringer Bestattungsgesetz",
     "LAND",
     "GVBl. TH 1971, S. 187, zul. geänd. 2022",
     "§ 12 ThürBestG: Pflicht der Gemeinde zur Bereithaltung ausreichender Bestattungseinrichtungen. "
     "Gebührenfinanziert; Ermessen bei Friedhofsgestaltung, -erweiterung und Gebührenhöhe (via Satzung)."),

    ("ThürArchivG",
     "Thüringer Archivgesetz",
     "LAND",
     "GVBl. TH 2016, S. 144",
     "§§ 2, 7 ThürArchivG: Pflicht zur dauerhaften Aufbewahrung öffentlichen Schriftguts. "
     "Betrieb des Kommunalarchivs ist Pflichtaufgabe. Nutzungskreis, Gebühren und Digitalisierungsgrad "
     "liegen im Ermessen (via Archivsatzung)."),

    ("ThürEBG",
     "Thüringer Erwachsenenbildungsgesetz",
     "LAND",
     "GVBl. TH 1994, S. 1021, zul. geänd. 2021",
     "§ 11 ThürEBG: Pflicht zur Grundversorgung mit Erwachsenenbildung (VHS). "
     "Art. 29 ThürVerf: Erwachsenenbildung als Staatsziel. "
     "Landesförderung unter Haushaltsvorbehalt; Gebührengestaltung und Angebot im Ermessen des Stadtrats."),

    ("ThürFlüAG",
     "Thüringer Flüchtlingsaufnahmegesetz",
     "LAND",
     "GVBl. TH 2015, S. 5, zul. geänd. 2023",
     "Regelung der Aufnahme und Unterbringung von Flüchtlingen als Auftragsangelegenheit. "
     "Kosten werden vom Land erstattet (Kostenerstattungssystem). "
     "Unterbringungsstandards sind Landesvorgaben; Ermessen bei Standortwahl."),

    ("SGB_II",
     "Sozialgesetzbuch Zweites Buch – Grundsicherung für Arbeitsuchende",
     "BUND",
     "BGBl. I 2003, S. 2954, zul. geänd. 2024",
     "§ 16a SGB II: Kommunale Eingliederungsleistungen (Schuldner-, Sucht-, psychosoziale Beratung) – "
     "Pflicht mit kommunalem Ermessen über Art und Umfang. "
     "§ 22 SGB II: Kosten der Unterkunft und Heizung (KdU) – individuell einklagbarer Anspruch; "
     "Höhe durch 'Schlüssiges Konzept' der Gemeinde begrenzbar. "
     "Jobcenter gemeinsame Einrichtung von BA und Kommunen (§ 44b SGB II)."),

    ("SGB_VIII",
     "Sozialgesetzbuch Achtes Buch – Kinder- und Jugendhilfe",
     "BUND",
     "BGBl. I 1990, S. 1163, zul. geänd. 2024",
     "§ 1 SGB VIII: Recht jedes jungen Menschen auf Förderung. "
     "§ 11 SGB VIII: Jugendarbeit – Pflichtaufgabe, Ausgestaltung Ermessen. "
     "§§ 27 ff. SGB VIII: Hilfen zur Erziehung – individuell einklagbarer Rechtsanspruch "
     "(§ 27 Abs. 1: 'hat Anspruch'). Fallverantwortung und Kostenlast beim kommunalen JA (§ 36a SGB VIII). "
     "§§ 42a ff. SGB VIII: Inobhutnahme – sofortige Pflichtreaktion ohne Ermessen. "
     "§§ 78a ff. SGB VIII: Leistungserbringungsverträge – Verhandlungshoheit der Gemeinde über Entgelte."),

    ("SGB_IX",
     "Sozialgesetzbuch Neuntes Buch – Rehabilitation und Teilhabe von Menschen mit Behinderungen",
     "BUND",
     "BGBl. I 2001, S. 1046, zul. geänd. 2024",
     "§§ 90 ff. SGB IX: Eingliederungshilfe für Menschen mit (drohender) Behinderung – "
     "individuell einklagbarer Anspruch. Seit 2020 von der Sozialhilfe (SGB XII) getrennt. "
     "§ 112 SGB IX: Besondere Leistungsgruppen. "
     "Kosten steigen systemisch (Fallzahlen, Fachkräftekosten); Steuerung nur über Qualität der Teilhabe-"
     "planung und Verhandlung von Leistungsbeschreibungen mit Trägern."),

    ("SGB_XII",
     "Sozialgesetzbuch Zwölftes Buch – Sozialhilfe",
     "BUND",
     "BGBl. I 2003, S. 3022, zul. geänd. 2024",
     "§ 27 SGB XII: Hilfe zum Lebensunterhalt – Auffangsystem für Nicht-SGB-II-Berechtigte. "
     "§§ 41 ff. SGB XII: Grundsicherung im Alter und bei Erwerbsminderung – "
     "individuell einklagbarer Rechtsanspruch; Bundeserstattung zu 100 % (§ 46a SGB XII). "
     "§§ 61 ff. SGB XII: Hilfe zur Pflege – subsidiär zur Pflegeversicherung. "
     "§§ 35, 42 SGB XII: Kosten der Unterkunft (KdU) für SGB-XII-Empfänger."),

    ("AsylbLG",
     "Asylbewerberleistungsgesetz",
     "BUND",
     "BGBl. I 1993, S. 1074, zul. geänd. 2024",
     "§§ 1 ff. AsylbLG: Pflichtleistungen für Asylsuchende (Unterkunft, Verpflegung, medizinische Versorgung). "
     "Kosten teilweise durch Land erstattet (ThürFlüAG). "
     "Keine kommunale Ermessensreduzierung bei Grundleistungen; Effizienz via Sachleistungsprinzip (§ 3)."),

    ("BKiSchG",
     "Bundeskinderschutzgesetz",
     "BUND",
     "BGBl. I 2011, S. 2975, zul. geänd. 2021",
     "§ 3 BKiSchG: Netzwerke Frühe Hilfen als Pflichtaufgabe des öffentlichen Trägers der Jugendhilfe. "
     "Bundesinitiative Frühe Hilfen finanziert Grundstruktur kofinanziert; "
     "kommunaler Eigenanteil über Jugendförderplan steuerbar."),

    ("BMG",
     "Bundesmeldegesetz",
     "BUND",
     "BGBl. I 2013, S. 1084, zul. geänd. 2023",
     "Pflicht zur Führung des Melderegisters als staatliche Pflichtaufgabe "
     "(übertragen vom Bund via Länder). Keine kommunale Gestaltungsfreiheit bei Kernaufgaben. "
     "Gebührenfinanzierung möglich (§ 55 BMG)."),

    ("PStG",
     "Personenstandsgesetz",
     "BUND",
     "BGBl. I 2007, S. 122, zul. geänd. 2023",
     "Pflicht zur Führung von Geburts-, Ehe- und Sterberegistern beim Standesamt. "
     "Übertragene Aufgabe; Handeln nach Bundesrecht ohne kommunalen Ermessensspielraum. "
     "Standesamtsgebühren nach § 72 PStG."),

    ("GewO",
     "Gewerbeordnung",
     "BUND",
     "RGBl. 1869, zul. geänd. 2024",
     "Pflicht zur Entgegennahme von Gewerbeanmeldungen (§ 14 GewO) und Überwachung "
     "erlaubnispflichtiger Gewerbe (§§ 34 ff. GewO). Übertragene Bundesaufgabe. "
     "Personalstärke im Ermessen; Untätigkeit begründet Amtshaftung."),

    ("KrWG",
     "Kreislaufwirtschaftsgesetz",
     "BUND",
     "BGBl. I 2012, S. 212, zul. geänd. 2023",
     "§ 20 KrWG i.V.m. ThürAbfG: Pflicht der kreisfreien Stadt zur Abfallentsorgung. "
     "Entsorgungspflicht besteht dem Grunde nach zwingend. "
     "Steuerung über Abfallgebührensatzung, Entsorgungskonzept und Ausschreibung Dritter möglich."),

    ("WHG",
     "Wasserhaushaltsgesetz",
     "BUND",
     "BGBl. I 2009, S. 2585, zul. geänd. 2023",
     "§ 38 WHG: Gewässerunterhaltung als Pflicht des Unterhaltungspflichtigen (für Gewässer 3. Ordnung: Gemeinde). "
     "§ 78 ff. WHG: Überschwemmungsgebiete und Hochwasserschutz. "
     "Ermessen bei Unterhaltungsstandard; fehlende Unterhaltung kann Amtshaftung begründen."),

    ("LFGB",
     "Lebensmittel-, Bedarfsgegenstände- und Futtermittelgesetzbuch",
     "BUND",
     "BGBl. I 2005, S. 945, zul. geänd. 2024",
     "Grundlage für amtliche Lebensmittelüberwachung durch das Veterinäramt. "
     "EU-Verordnung (EG) Nr. 882/2004 gibt Kontrollfrequenzen vor. "
     "Pflichtaufgabe des öffentlichen Gesundheitsdienstes; keine kommunale Gestaltungsfreiheit."),

    ("OZG",
     "Onlinezugangsgesetz",
     "BUND",
     "BGBl. I 2017, S. 3122, zul. geänd. 2023",
     "§ 1 OZG: Pflicht zur digitalen Zugänglichmachung von Verwaltungsleistungen. "
     "Frist mehrfach verlängert. ThürEGovG konkretisiert Landesverpflichtungen. "
     "Investitionshöhe und Umsetzungsgeschwindigkeit liegen im kommunalen Ermessen."),
]


# ─────────────────────────────────────────────────────────────────────────────
# 2. Rechtsgrundlagen je SK-Kategorie
# ─────────────────────────────────────────────────────────────────────────────

SK_RECHTSGRUNDLAGE = {
    "FREIWILLIG": (
        "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2 Abs. 1: "
        "Die kommunale Selbstverwaltungsgarantie schützt auch das Recht, freiwillige Aufgaben zu "
        "übernehmen und deren Umfang, Standard und Fortbestand frei zu bestimmen. "
        "Dritte haben keinen Rechtsanspruch auf Erbringung; der Stadtrat kann durch einfachen Beschluss "
        "kürzen oder einstellen. Kommunalaufsicht prüft nur Rechtmäßigkeit, nicht Zweckmäßigkeit. "
        "Haushaltssicherungskonzept (§ 92a ThürKO) verpflichtet zur bevorzugten Streichung freiwilliger "
        "Leistungen vor Pflichtaufgabenkürzungen."
    ),
    "PFLICHT_ERMESSEN": (
        "ThürKO § 3 Abs. 1 Satz 1 (Pflichtaufgaben ohne Weisungsunterworfenheit) i.V.m. jeweiligem "
        "Fachgesetz: Die Gemeinde ist zur Aufgabenerfüllung dem Grunde nach verpflichtet; Art, Umfang, "
        "Qualitätsstandard und Organisationsform unterliegen jedoch dem kommunalen Ermessen "
        "(§ 2 ThürKO). Kürzungen sind möglich, solange das gesetzlich gebotene Mindestmaß und die "
        "Verkehrssicherungspflicht gewahrt bleiben. Steuerungsinstrumente: Satzungen, Richtlinien, "
        "Stellenplan, Investitionsplanung. Kein individuell einklagbarer Rechtsanspruch Dritter "
        "(außer bei gesondert normierten Ansprüchen im Fachgesetz)."
    ),
    "PFLICHT_STRIKT": (
        "ThürKO § 3 Abs. 1 i.V.m. einschlägigem Bundesfachgesetz: Aufgabenerfüllung ist gebundene "
        "Entscheidung ohne kommunalen Ermessensspielraum. Leistungsberechtigte haben einen individuell "
        "einklagbaren Rechtsanspruch (z.B. § 27 SGB VIII: 'hat Anspruch'; §§ 41 ff. SGB XII: "
        "'haben Anspruch'; ThürKitaG § 7: Rechtsanspruch auf Betriebskostenzuschuss) oder die "
        "Nichterfüllung begründet Amtshaftung (§ 839 BGB i.V.m. Art. 34 GG) bzw. löst "
        "Kommunalaufsichtsmaßnahmen aus (§ 118 ThürKO). Das Budget folgt dem gesetzlichen Bedarf, "
        "nicht der Kassenlage. Steuerung nur über verfahrensrechtliche Instrumente "
        "(Schlüssiges Konzept, Hilfeplanqualität, Entgeltverhandlung), nicht über pauschale Kürzung."
    ),
    "UEBERTRAGEN": (
        "ThürKO § 3 Abs. 2 (Auftragsangelegenheiten / übertragene Aufgaben) i.V.m. Konnexitätsprinzip "
        "(Art. 93 Abs. 1 ThürVerf): Aufgabe wurde durch Bundes- oder Landesgesetz auf die kreisfreie "
        "Stadt übertragen; sie handelt als Erfüllungsgehilfin des Landes unter dessen Fach- und "
        "Rechtsaufsicht. Das Land erstattet die Mehrkosten aus der Aufgabenübertragung. "
        "Ermessen der Stadt nur im Rahmen der Übertragungsvorschriften; eigenständige Kürzungen "
        "nicht zulässig. Vollzugsbindung an Bundesrecht (z.B. PStG, BMG, GewO)."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Rechtsgrundlagen je Produkt-Gruppe (Prefix-Mapping)
# ─────────────────────────────────────────────────────────────────────────────
# Format: präzises Zitat + Kernverpflichtung + Kürzungshinweis
# Reihenfolge: längerer Schlüssel (spezifischer) geht vor kürzerem

PRODUKT_RG = {

    # ── TP01 / TP03: Verwaltungsführung, Personal, zentrale Dienste ──────────
    "111100": "ThürKO §§ 21 ff., 29 ff.: Stadtrat, politische Gremien und Bürgermeister. "
              "Pflicht zur Durchführung von Ratssitzungen und Ausschusssitzungen. "
              "Aufwandsentschädigungen nach Entschädigungssatzung (Ermessen des Stadtrats über Höhe).",
    "111110": "ThürKO §§ 21 ff.: Gemeindevertretung/Stadtrat. Pflichtgremium; "
              "Geschäftsordnung und Entschädigungssatzung im Ermessen des Rates.",
    "111120": "ThürKO §§ 21 ff.: Stadtrat/Gemeindevertretung – Sitzungsdurchführung. Wie 111110.",
    "111130": "ThürKO §§ 28 ff.: Ausschüsse des Stadtrats. Pflichtausschüsse gesetzlich vorgeschrieben; "
              "fakultative Ausschüsse im Ermessen.",
    "111140": "ThürKO §§ 28 ff.: Bürgermeister/Verwaltungsvorstand – Amtsführung.",
    "111150": "ThürKO §§ 28 ff.: Bürgermeister/Verwaltungsvorstand – Verwaltungsführung.",
    "111160": "ThürKO §§ 21 ff.: Stadtrat/politische Gremien – allgemeiner Betrieb.",
    "111600": "ThürKO § 2: Allgemeine Verwaltungsführung. Pflicht zur ordnungsgemäßen Verwaltung; "
              "Personalstärke und Prozessgestaltung im Ermessen.",
    "112":    "ThürKO § 5, ThürGemHV: Personal und Organisation. "
              "Pflicht zur ordnungsgemäßen Personalwirtschaft; Stellenplan als Beschluss des Stadtrats. "
              "Keine Unterschreitung des für gesetzliche Pflichtaufgaben erforderlichen Mindestpersonals.",
    "113":    "Onlinezugangsgesetz (OZG) i.V.m. Thüringer E-Government-Gesetz (ThürEGovG): "
              "Pflicht zur digitalen Zugänglichmachung von Verwaltungsleistungen. "
              "Investitionsumfang und Priorisierung im kommunalen Ermessen.",
    "114":    "ThürKO § 2, ThürArchivG §§ 2, 7: Zentrale Dienstleistungen und Archivwesen. "
              "Betrieb des Kommunalarchivs ist Pflichtaufgabe; Nutzungsgebühren und Digitalisierungsgrad "
              "im Ermessen (Archivsatzung).",
    "116":    "ThürGemHV-Doppik, ThürKO § 92 ff.: Finanzmanagement und Rechnungsprüfung. "
              "Ordnungsgemäße doppische Buchführung ist Pflicht; internes Prüfwesen im Ermessen.",
    "117":    "ThürKAG: Abgabenwesen, Steuerverwaltung und Gebührenkalkulation. "
              "Pflicht zur Festsetzung und Erhebung kommunaler Abgaben; Hebesätze autonom durch Stadtrat.",
    "118":    "ThürKO § 2: Sonstige allgemeine Verwaltung. Pflicht zum ordnungsgemäßen Betrieb; "
              "Standard und Umfang im Ermessen.",
    "511":    "ThürKO § 2: Interne Dienstleistung / zentrale Verwaltung.",
    "522100": "ThürKO § 2: Interne Dienstleistungen (Fuhrpark/Technik).",
    "523":    "ThürKO § 2: Interne Dienstleistungen.",
    "536":    "ThürKO § 2: Interne Verwaltung.",
    "571":    "ThürKO § 2: Interne Verwaltung / Gebäudemanagement.",
    "573110": "ThürKO § 2: Internes Gebäudemanagement.",
    "573120": "ThürKO § 2: Internes Gebäudemanagement.",
    "573130": "ThürKO § 2: Internes Gebäudemanagement.",
    "573140": "ThürKO § 2: Internes Gebäudemanagement.",

    # ── TP02: Kultur, Tourismus und Sport ─────────────────────────────────────
    "252110": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2 Abs. 1: "
              "Museum/Ausstellung – freiwillige Selbstverwaltungsaufgabe ohne Rechtsanspruch Dritter. "
              "Vollständige Kürzung oder Einstellung ohne rechtliche Folge möglich.",
    "252120": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2 Abs. 1: Museum. Wie 252110.",
    "252200": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2 Abs. 1: "
              "Museum/Kulturpflege – freiwillig.",
    "252400": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2 Abs. 1: "
              "Kulturpflege – freiwillig.",
    "262":    "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2 Abs. 1: "
              "Kulturförderung – freiwillige Selbstverwaltungsaufgabe.",
    "281000": "ThürSchulG §§ 13, 14: Bereitstellung von Schulsportanlagen. "
              "Pflicht als sächlicher Schulträger; Standard im Ermessen.",
    "281010": "ThürSchulG §§ 13, 14: Schulsportanlagen – Betrieb/Unterhaltung. Wie 281000.",
    "281020": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: "
              "Vereinssportförderung – freiwillig (kein gesetzlicher Anspruch der Vereine). "
              "Steuerung über Sportförderrichtlinie ohne individuelle Ansprüche.",
    "281030": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: "
              "Sport-/Freizeitanlagen (nicht Schulsport) – freiwillig.",
    "421":    "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: "
              "Theater/Musik – freiwillige Kulturaufgabe.",
    "424100": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: Sportförderung – freiwillig.",
    "424210": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: Sportförderung – freiwillig.",
    "424220": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: Sportförderung – freiwillig.",
    "424230": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: Sportförderung – freiwillig.",
    "424240": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: Sportförderung – freiwillig.",
    "424250": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: Sportförderung – freiwillig.",
    "424300": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: Sportförderung/Bäder – freiwillig.",
    "424400": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: Sportstätten – freiwillig "
              "(über Schulsport-Pflichtmaß hinaus).",
    "546100": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: "
              "Stadtmarketing/Tourismus – freiwillig.",
    "573300": "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: "
              "Grünanlagen/Sport-Infrastruktur – freiwillig.",
    "575":    "GG Art. 28 Abs. 2 Satz 1 i.V.m. ThürKO § 2: "
              "Stadtgrün/Grünanlagen (über Verkehrssicherungspflicht hinaus) – freiwillig.",

    # ── TP04: Finanzverwaltung ─────────────────────────────────────────────────
    "116000": "ThürGemHV-Doppik, ThürKO § 103 ff.: Rechnungsprüfung – Pflicht.",
    "117100": "ThürKAG: Abgabenwesen/Steuerverwaltung – Pflicht.",
    "117200": "ThürKAG: Gebührenwesen – Pflicht zur Kalkulation und Erhebung.",
    "2510":   "GG Art. 28 Abs. 2 i.V.m. ThürKO § 2: Wissenschaft und Forschung – freiwillig.",
    "2520":   "GG Art. 28 Abs. 2 i.V.m. ThürKO § 2: Museen, bildende Kunst – freiwillig.",
    "2610":   "GG Art. 28 Abs. 2 i.V.m. ThürKO § 2: Theater, Orchester, Musikschulen – freiwillig.",
    "2711":   "GG Art. 28 Abs. 2 i.V.m. ThürKO § 2: Sonstige Kulturpflege – freiwillig.",
    "2710":   "Thüringer Erwachsenenbildungsgesetz (ThürEBG) § 11 i.V.m. Art. 29 ThürVerf: "
              "VHS-Grundversorgung – Pflichtaufgabe, aber Angebotsstruktur und Gebühren im Ermessen.",
    "2811":   "GG Art. 28 Abs. 2 i.V.m. ThürKO § 2: Vereinssportförderung – freiwillig.",
    "2810":   "ThürSchulG §§ 13, 14: Schulsportanlagen – Pflicht als Schulträger.",
    "411200": "ThürKO § 2: Wirtschaftsförderung (TP04-Kontext) – im Ermessen.",
    "535":    "ThürGemHV-Doppik: Haushaltswirtschaft – Pflicht.",
    "547":    "ThürGemHV-Doppik: Finanzverwaltung/Kassenwesen – Pflicht.",

    # ── TP05: Öffentliche Flächen und Straßen ─────────────────────────────────
    "3100":   "SGB II § 16a: Kommunale Eingliederungsleistungen (Schuldner-, Suchtberatung) – "
              "Pflicht dem Grunde nach; Art und Umfang im Ermessen des Trägers der Grundsicherung.",
    "3180":   "SGB XII § 11 Abs. 4: Schuldner- und Verbraucherinsolvenzberatung – "
              "Pflicht zur Sicherstellung der Beratung; Trägerschaft und Umfang im Ermessen.",
    "541":    "Thüringer Straßengesetz (ThürStrG) §§ 10, 10a: Gemeindestraßen – Unterhaltungspflicht. "
              "Pflicht dem Grunde nach; Belagsqualität und Erneuerungsintervall im Ermessen. "
              "Verkehrssicherungspflicht (§ 10 Abs. 3 ThürStrG) ist strikt – Verletzung = Amtshaftung.",
    "542":    "ThürStrG § 10: Straßenunterhalt – wie 541.",
    "543":    "ThürStrG § 10: Gemeindestraßen/Wege – wie 541.",
    "551000": "Thüringer Naturschutzgesetz (ThürNatSchG): Naturschutz/Landschaftspflege "
              "als untere Naturschutzbehörde – Pflicht.",
    "553":    "WHG § 38 i.V.m. Thüringer Wassergesetz (ThürWG): Gewässerpflege – "
              "Unterhaltungspflicht für Gewässer 3. Ordnung. Pflicht dem Grunde nach; "
              "Umfang nach Risikoabwägung.",
    "366300": "ThürStrG: Gemeindestraßen (TP05-Kontext) – Pflicht.",

    # ── TP06: Allgemeine Finanzwirtschaft ─────────────────────────────────────
    "611":    "ThürKAG §§ 1 ff. i.V.m. ThürFAG: Steuern und allgemeine Deckungsmittel – "
              "Pflicht zur Festsetzung und Erhebung; Hebesätze autonom.",
    "612":    "ThürFAG § 7: Allgemeine Schlüsselzuweisungen – gesetzlich bestimmte Einnahme.",
    "622":    "ThürKO § 75: Kreditverwaltung/Schuldendienst – striktes Gebot. "
              "Kreditverbindlichkeiten sind vorrangig zu bedienen; Verzug = Aufsichtsintervention.",
    "625":    "ThürKO § 75: Kreditdienst/Finanzierungskosten – wie 622.",
    "3620":   "SGB VIII § 11: Jugendarbeit (Gesamtprodukt) – Pflicht mit Ermessen über Ausgestaltung.",
    "3630":   "SGB VIII §§ 27 ff.: Hilfen zur Erziehung (Gesamtprodukt) – "
              "individuell einklagbarer Rechtsanspruch (§ 27 Abs. 1 SGB VIII). "
              "Budget folgt dem Bedarf.",
    "3650":   "Thüringer Kindertagesbetreuungsgesetz (ThürKitaG) § 29 i.V.m. § 1 Abs. 3: "
              "Elternbeitragserhebung – Pflicht zur sozial gestaffelten Erhebung. "
              "Satzungsautonomie des Stadtrats über Staffelung und Höhe.",
    "3655":   "ThürKitaG § 7 Abs. 2: Betriebskostenförderung (Gesamtprodukt) – "
              "Rechtsanspruch der freien Träger auf Defizitausgleich; Höhe über Kita-Finanzierungs-"
              "richtlinie (Mietobergrenzen, Eigenleistungspflicht) begrenzbar.",

    # ── TP07: Ordnung und Sicherheit ───────────────────────────────────────────
    "119":    "ThürKO § 2, ThürOBG: Allgemeine Verwaltung Ordnungsbereich. Pflicht.",
    "121100": "Bundesmeldegesetz (BMG) i.V.m. Thüringer Meldegesetz (ThürMeldeG): "
              "Melde-/Einwohnerwesen – übertragene Pflichtaufgabe. Vollzug nach Bundesrecht "
              "ohne kommunalen Ermessensspielraum.",
    "121200": "Personenstandsgesetz (PStG): Personenstandswesen/Standesamt – "
              "übertragene Bundesaufgabe. Handeln ausschließlich nach Bundesrecht.",
    "121210": "PStG: Personenstandswesen. Wie 121200.",
    "121220": "PStG: Standesamt. Wie 121200.",
    "121230": "PStG: Personenstandswesen. Wie 121200.",
    "121240": "PStG: Personenstandswesen. Wie 121200.",
    "122100": "ThürOBG §§ 1 ff.: Ordnungsamt/allgemeine Gefahrenabwehr – Pflicht. "
              "Personalstärke im Ermessen soweit keine Bundesgesetze konkrete Kontrolldichte vorgeben.",
    "122200": "ThürOBG, Gewerbeordnung (GewO) §§ 14 ff.: Ordnungsamt/Gewerbeaufsicht – "
              "Pflicht zur Entgegennahme von Gewerbeanmeldungen und Überwachung erlaubnispflichtiger Gewerbe. "
              "Übertragene Aufgabe nach Bundesrecht.",
    "122300": "GewO §§ 34 ff.: Gewerberecht/Ordnung – wie 122200.",
    "122310": "GewO: Gewerberecht. Wie 122200.",
    "122320": "GewO: Gewerberecht. Wie 122200.",
    "122400": "ThürOBG: Sonstige Ordnungsangelegenheiten – Pflicht mit Ermessen.",
    "123100": "Thüringer Brand- und Katastrophenschutzgesetz (ThürBKG) § 2: "
              "Pflicht zur Aufstellung und Unterhaltung einer leistungsfähigen Feuerwehr. "
              "Soll-Stärken und Mindestausrüstung sind zwingend; Beschaffungszeitpunkt im Ermessen.",
    "123300": "Thüringer Rettungsdienstgesetz (ThürRettG) §§ 7, 14: "
              "Rettungsdienst – Pflicht zur Sicherstellung vorgegebener Hilfsfristen. "
              "Finanzierung über Krankenkassen-Gebühren; kommunaler Eigenanteil begrenzt.",
    "123400": "ThürBKG: Brand-/Katastrophenschutz. Wie 123100.",
    "123500": "ThürBKG: Katastrophenschutz – Pflicht.",
    "126010": "ThürBKG § 2: Feuerwehr/Brandschutz. Wie 123100.",
    "126020": "ThürBKG: Feuerwehr/Katastrophenschutz. Wie 123100.",
    "127":    "ThürBKG: Bevölkerungsschutz/Zivilschutz – Pflicht.",
    "128":    "Bundesmeldegesetz (BMG): Einwohnerwesen/Meldewesen. Wie 121100.",
    "573200": "ThürKO § 2: Fahrzeug-/Gebäudeunterhalt Ordnungsbereich – intern, Ermessen.",
    "1260":   "ThürBKG: Brandschutz/Katastrophenschutz (Querschnitt). Wie 123100.",

    # ── TP08: Umwelt ───────────────────────────────────────────────────────────
    "124200": "Lebensmittel-, Bedarfsgegenstände- und Futtermittelgesetzbuch (LFGB) i.V.m. "
              "EU-VO (EG) 882/2004, ThürVet-Gesetz: Veterinärwesen/Lebensmittelüberwachung – "
              "Pflichtaufgabe mit EU-rechtlich vorgegebener Kontrollfrequenz. Kein kommunaler Ermessensspielraum.",
    "537010": "Kreislaufwirtschaftsgesetz (KrWG) § 20 i.V.m. Thüringer Abfallgesetz (ThürAbfG): "
              "Abfallwirtschaft – Pflicht zur Entsorgung als Aufgabe der kreisfreien Stadt. "
              "Steuerung über Abfallgebührensatzung und Ausschreibung Dritter.",
    "537020": "KrWG i.V.m. ThürAbfG: Abfallwirtschaft. Wie 537010.",
    "537030": "KrWG i.V.m. ThürAbfG: Abfallwirtschaft. Wie 537010.",
    "537040": "KrWG i.V.m. ThürAbfG: Abfallwirtschaft. Wie 537010.",
    "253":    "ThürKO § 2: Stadtentwicklung/Umweltplanung – Pflicht mit erheblichem Ermessen.",
    "521":    "ThürStrG § 10: Straßen-/Wegeunterhalt (Umweltbereich). Wie 541.",
    "545110": "Thüringer Bestattungsgesetz (ThürBestG) § 12: Friedhöfe – "
              "Pflicht zur Bereithaltung ausreichender Bestattungseinrichtungen. "
              "Gebührenfinanziert; Gestaltung über Friedhofssatzung steuerbar.",
    "545120": "ThürBestG § 12: Friedhöfe. Wie 545110.",
    "551100": "ThürNatSchG: Naturschutz/Landschaftspflege. Pflicht als untere Behörde.",
    "552":    "WHG § 38 i.V.m. ThürWG: Gewässerpflege. Wie 553.",
    "554":    "WHG § 78 ff. i.V.m. ThürWG: Gewässerpflege/Hochwasserschutz – Pflicht.",
    "555":    "ThürNatSchG: Naturschutz/Landschaftspflege. Wie 551.",
    "561":    "GG Art. 28 Abs. 2 i.V.m. ThürKO § 2: Stadtgrün (über Pflichtmaß) – freiwillig "
              "soweit über Verkehrssicherungspflicht hinausgehend.",

    # ── TP09: Soziales und Gesundheit ─────────────────────────────────────────
    "111500": "ThürKO § 2: Allgemeine Verwaltung Sozialbereich – intern, Ermessen.",
    "122500": "ThürOBG: Sonstige Ordnungsangelegenheiten (TP09). Pflicht/Ermessen.",
    "124100": "LFGB i.V.m. ThürGDG: Veterinärwesen/Lebensmittelüberwachung (TP09). Wie 124200.",
    "311000": "SGB XII §§ 27 ff.: Sozialhilfe/SGB-II-Leistungen (Gesamtprodukt) – "
              "individuell einklagbarer Rechtsanspruch.",
    "311100": "SGB XII §§ 27 ff.: Hilfe zum Lebensunterhalt (SGB XII) und SGB-II-Leistungen – "
              "Pflichtleistungen ohne kommunalen Ermessensspielraum.",
    "311110": "SGB XII § 27 Abs. 1: Hilfe zum Lebensunterhalt – "
              "Rechtsanspruch der Berechtigten ('hat Anspruch'). Bedarfsdeckungsprinzip.",
    "311120": "SGB XII § 27: Hilfe zum Lebensunterhalt. Wie 311110.",
    "311130": "SGB XII § 27: Hilfe zum Lebensunterhalt. Wie 311110.",
    "311200": "SGB XII §§ 41 ff.: Grundsicherung im Alter und bei Erwerbsminderung – "
              "individuell einklagbarer Rechtsanspruch; Bundeserstattung zu 100 % (§ 46a SGB XII). "
              "Keine kommunale Haushaltslast durch Bundeserstattung.",
    "311201": "SGB XII §§ 41 ff.: Grundsicherung. Wie 311200.",
    "311210": "SGB XII §§ 41 ff.: Grundsicherung. Wie 311200.",
    "311220": "SGB XII §§ 41 ff.: Grundsicherung. Wie 311200.",
    "311230": "SGB XII §§ 41 ff.: Grundsicherung. Wie 311200.",
    "311240": "SGB XII §§ 41 ff.: Grundsicherung. Wie 311200.",
    "311260": "SGB XII §§ 41 ff.: Grundsicherung. Wie 311200.",
    "311270": "SGB XII §§ 41 ff.: Grundsicherung. Wie 311200.",
    "311280": "SGB XII §§ 41 ff.: Grundsicherung. Wie 311200.",
    "311290": "SGB XII §§ 41 ff., 47 ff.: Grundsicherung/sonstige SGB-XII-Leistungen. Wie 311200.",
    "311400": "SGB XII: Sonstige Sozialhilfeleistungen – Rechtsanspruch.",
    "311500": "SGB XII: Sozialhilfeleistungen – Rechtsanspruch.",
    "311510": "SGB XII: Sozialhilfeleistungen. Wie 311500.",
    "311520": "SGB XII: Sozialhilfeleistungen. Wie 311500.",
    "311550": "SGB XII: Sozialhilfeleistungen. Wie 311500.",
    "311600": "SGB IX §§ 90 ff.: Eingliederungshilfe für Menschen mit Behinderungen – "
              "individuell einklagbarer Rechtsanspruch (§ 99 SGB IX). "
              "Kosten steigen systemisch; Steuerung nur über Teilhabeplanung und Entgeltverhandlung (§§ 123 ff. SGB IX).",
    "311610": "SGB IX §§ 90 ff., § 112: Eingliederungshilfe. Wie 311600.",
    "311620": "SGB IX §§ 90 ff.: Eingliederungshilfe. Wie 311600.",
    "311630": "SGB IX §§ 90 ff.: Eingliederungshilfe. Wie 311600.",
    "311700": "SGB XII: Sonstige SGB-XII-Leistungen – Rechtsanspruch.",
    "311800": "SGB XII: Sozialhilfe/sonstige Sozialleistungen – Rechtsanspruch.",
    "312100": "SGB XII §§ 35, 42: Kosten der Unterkunft und Heizung (KdU) SGB XII – "
              "Rechtsanspruch; Höhe durch Schlüssiges Konzept begrenzbar.",
    "312200": "SGB XII §§ 35, 42: KdU SGB XII. Wie 312100.",
    "312300": "SGB XII: Hilfe in sonstigen Lebenslagen – Rechtsanspruch.",
    "312600": "SGB XII: Sozialhilfeleistungen – Rechtsanspruch.",
    "313":    "SGB XII §§ 61 ff.: Hilfe zur Pflege – Rechtsanspruch; subsidiär zur Pflegeversicherung "
              "(SGB XI). Kommunaler Restbetrag nach Pflegekassenleistung.",
    "314":    "SGB XII (Blindengeld/Landespflegegeld): sonstige Hilfen – Rechtsanspruch nach Landesrecht.",
    "315410": "SGB XII §§ 47 ff.: Hilfe in besonderen Lebenslagen – Rechtsanspruch.",
    "315500": "SGB XII: Sozialhilfeleistungen – Rechtsanspruch.",
    "315600": "SGB XII: Sozialhilfeleistungen – Rechtsanspruch.",
    "316000": "SGB IX (Eingliederungshilfe Gesamtprodukt). Wie 311600.",
    "316100": "SGB IX §§ 90 ff.: Eingliederungshilfe. Wie 311600.",
    "316210": "SGB IX §§ 90 ff.: Eingliederungshilfe/Teilhabe. Wie 311600.",
    "316300": "SGB IX §§ 90 ff.: Eingliederungshilfe/Teilhabe. Wie 311600.",
    "316400": "SGB IX §§ 90 ff.: Eingliederungshilfe/Teilhabe. Wie 311600.",
    "316411": "SGB IX §§ 90 ff.: Eingliederungshilfe/Teilhabe. Wie 311600.",
    "316412": "SGB IX §§ 90 ff.: Eingliederungshilfe/Teilhabe. Wie 311600.",
    "316421": "SGB IX §§ 90 ff.: Eingliederungshilfe/Teilhabe. Wie 311600.",
    "316422": "SGB IX §§ 90 ff.: Eingliederungshilfe/Teilhabe. Wie 311600.",
    "316430": "SGB IX §§ 90 ff.: Eingliederungshilfe/Teilhabe. Wie 311600.",
    "316440": "SGB IX §§ 90 ff.: Eingliederungshilfe/Teilhabe. Wie 311600.",
    "316462": "SGB IX §§ 90 ff.: Eingliederungshilfe/Teilhabe. Wie 311600.",
    "316470": "SGB IX §§ 90 ff.: Eingliederungshilfe/Teilhabe. Wie 311600.",
    "316480": "SGB IX §§ 90 ff.: Eingliederungshilfe/Teilhabe. Wie 311600.",
    "316500": "SGB IX §§ 90 ff.: Eingliederungshilfe/Teilhabe. Wie 311600.",
    "331":    "SGB XII § 11: Soziale Beratungsdienste – Gewährleistungspflicht; Umsetzung im Ermessen.",
    "343":    "SGB XII: Sonstige soziale Leistungen – Rechtsanspruch.",
    "345":    "Asylbewerberleistungsgesetz (AsylbLG) §§ 1 ff.: Pflichtleistungen für Asylsuchende. "
              "Kosten teilweise vom Land erstattet (ThürFlüAG).",
    "346":    "SGB XII: Sonstige soziale Leistungen – Rechtsanspruch.",
    "348":    "AsylbLG i.V.m. Thüringer Flüchtlingsaufnahmegesetz (ThürFlüAG): "
              "Flüchtlingsunterbringung/-betreuung – Pflicht; Kostenerstattung durch Land.",
    "351400": "Thüringer Gesundheitsdienstgesetz (ThürGDG) §§ 1 ff.: "
              "Gesundheitsamt/amtsärztlicher Dienst – Pflichtaufgabe.",
    "351700": "ThürGDG §§ 1 ff.: Öffentlicher Gesundheitsdienst. Wie 351400.",
    "351500": "ThürGDG §§ 1 ff.: Öffentlicher Gesundheitsdienst (TP11-Kontext). Wie 351400.",
    "412":    "ThürGDG: Gesundheitsförderung/Sport – Pflicht mit Ermessen.",
    "414":    "ThürGDG: Gesundheitsförderung/Prävention – Pflicht mit Ermessen.",
    "522200": "ThürKO § 2: Interne Dienstleistungen Sozialbereich – Ermessen.",
    "5410":   "ThürStrG: Gemeindestraßen (Gesamtprodukt). Wie 541.",
    "5450":   "ThürBestG: Friedhöfe (Gesamtprodukt). Wie 545110.",
    "5510":   "ThürNatSchG: Naturschutz (Gesamtprodukt). Wie 551.",
    "5520":   "WHG: Gewässerpflege (Gesamtprodukt). Wie 553.",
    "5530":   "ThürNatSchG/WHG: Umweltschutz (Gesamtprodukt).",
    "5610":   "GG Art. 28 Abs. 2 i.V.m. ThürKO § 2: Energie/Kommunale Wärmeplanung – "
              "Wärmeplanungspflicht nach Wärmeplanungsgesetz (WPG) ab 2026 für Gemeinden > 10.000 EW.",

    # ── TP10: Schulträgeraufgaben ──────────────────────────────────────────────
    "201":    "ThürSchulG § 13 Abs. 1: Allgemeine Schulverwaltung als sächlicher Schulträger – Pflicht.",
    "211100": "ThürSchulG § 40: Grundschulen – Pflicht zur Bereitstellung geeigneter Schulgebäude. "
              "Ausstattungsstandard und Sanierungsrhythmus im Ermessen; Schulnetzplan (§ 14 ThürSchulG) "
              "liegt in der Beschlusskompetenz des Stadtrats.",
    "211200": "ThürSchulG: Gemeinschaftsschulen Schulträger. Wie 211100.",
    "211300": "ThürSchulG: Regelschulen Schulträger. Wie 211100.",
    "211400": "ThürSchulG: Gymnasien Schulträger. Wie 211100.",
    "212000": "ThürSchulG: Gemeinschafts-/Berufsschulen Schulträger. Wie 211100.",
    "212010": "ThürSchulG: Schulen Schulträger. Wie 211100.",
    "212020": "ThürSchulG: Schulen Schulträger. Wie 211100.",
    "212100": "ThürSchulG: Berufsschulen Schulträger. Wie 211100.",
    "216100": "ThürSchulG: Regelschulen. Wie 211100.",
    "216300": "ThürSchulG: Regelschulen. Wie 211100.",
    "217010": "ThürSchulG: Gymnasien Schulträger. Wie 211100.",
    "217020": "ThürSchulG: Gymnasien Schulträger. Wie 211100.",
    "221100": "ThürSchulG § 44: Förderschulen – Pflicht als Schulträger.",
    "221200": "ThürSchulG § 44: Förderschulen. Wie 221100.",
    "231":    "ThürSchulG § 69 i.V.m. ThürSchFG § 4: Schülerbeförderung – "
              "Pflichtaufgabe; Zumutbarkeitsgrenzen und Eigenanteile (Sek II) per Satzung steuerbar.",
    "241":    "ThürSchulG § 19a ThürKJHAG: Schulsozialarbeit – Pflicht/Planungshoheit "
              "(§§ 79, 80 SGB VIII); kommunaler Kofinanzierungsanteil im Ermessen.",
    "243":    "ThürSchulG: Sonstige schulische Aufgaben – Pflicht mit Ermessen.",
    "252300": "Thüringer Archivgesetz (ThürArchivG) §§ 2, 7: Archivwesen – Pflicht.",

    # ── TP11: Kinder-, Jugend- und Familienhilfe ───────────────────────────────
    "360":    "SGB VIII § 2 Abs. 1: Jugendhilfe-Koordination – allgemeine Leistungen. "
              "Pflichtaufgabe des örtlichen Trägers der öffentlichen Jugendhilfe.",
    "361":    "SGB VIII § 11: Jugendarbeit – Pflicht; Ausgestaltung (Träger, Methoden, Umfang) "
              "im Ermessen des Jugendamts (§ 79 SGB VIII Gesamtverantwortung).",
    "362":    "SGB VIII § 11: Jugendarbeit/Jugendsozialarbeit – wie 361.",
    "363000": "SGB VIII § 27 Abs. 1: Hilfen zur Erziehung – individuell einklagbarer Rechtsanspruch: "
              "'Ein Personensorgeberechtigter hat Anspruch auf Hilfe zur Erziehung'. "
              "Fallverantwortung nach § 36a SGB VIII; Kostenlast liegt beim Jugendamt. "
              "Steuerung: Hilfeplanqualität (§ 36 SGB VIII), ambulant vor stationär, "
              "Sozialraumorientierung, Entgeltverhandlung (§§ 78a ff. SGB VIII).",
    "363100": "SGB VIII § 28: Erziehungsberatung – Rechtsanspruch.",
    "363120": "SGB VIII § 30: Erziehungsbeistandschaft – Rechtsanspruch.",
    "363130": "SGB VIII § 31: Sozialpädagogische Familienhilfe – Rechtsanspruch.",
    "363210": "SGB VIII § 32: Tagesgruppe (teilstationär) – Rechtsanspruch.",
    "363220": "SGB VIII §§ 32 ff.: HzE teilstationär – Rechtsanspruch.",
    "363230": "SGB VIII §§ 32 ff.: HzE teilstationär – Rechtsanspruch.",
    "363240": "SGB VIII §§ 32 ff.: HzE teilstationär – Rechtsanspruch.",
    "363300": "SGB VIII §§ 33 ff.: HzE stationär – Rechtsanspruch.",
    "363310": "SGB VIII §§ 33 ff.: HzE stationär. Wie 363300.",
    "363330": "SGB VIII § 33: Vollzeitpflege (Pflegefamilie) – Rechtsanspruch.",
    "363340": "SGB VIII §§ 33 ff.: HzE stationär. Wie 363300.",
    "363350": "SGB VIII §§ 33 ff.: HzE stationär. Wie 363300.",
    "363360": "SGB VIII §§ 33 ff.: HzE stationär. Wie 363300.",
    "363370": "SGB VIII § 34: Heimerziehung, sonstige betreute Wohnform – Rechtsanspruch. "
              "Teuerste HzE-Form; Vorrang ambulanter Settings (§ 36 SGB VIII).",
    "363380": "SGB VIII § 33: Vollzeitpflege – Rechtsanspruch.",
    "363410": "SGB VIII §§ 34 ff.: HzE stationär. Wie 363300.",
    "363420": "SGB VIII §§ 34 ff.: HzE stationär. Wie 363300.",
    "363500": "SGB VIII § 35: Intensive sozialpädagogische Einzelbetreuung (ISE) – Rechtsanspruch.",
    "363520": "SGB VIII § 35: ISE. Wie 363500.",
    "363530": "SGB VIII § 35: ISE. Wie 363500.",
    "363540": "SGB VIII § 35: ISE. Wie 363500.",
    "363700": "SGB VIII § 35: ISE. Wie 363500.",
    "364":    "SGB VIII §§ 35a, 42 ff.: Eingliederungshilfe seelische Behinderung und Inobhutnahme – "
              "Rechtsanspruch; Inobhutnahme ist sofortige Pflichtmaßnahme ohne Ermessen.",
    "365200": "Thüringer Kindertagesbetreuungsgesetz (ThürKitaG) § 7 Abs. 2 Satz 1: "
              "Betriebskostenzuschuss kommunale Kita – Pflicht zur bedarfsdeckenden Finanzierung. "
              "Rechtsanspruch der Eltern auf Betreuungsplatz ab 1 Jahr (§ 1 ThürKitaG). "
              "Personalschlüssel (§ 16 ThürKitaG) nicht unterschreitbar.",
    "365210": "ThürKitaG § 7 Abs. 2: Betriebskostenzuschuss kommunale Kita. Wie 365200.",
    "365500": "ThürKitaG § 7 Abs. 2: Betriebskostenförderung freier Träger (Hauptposition) – "
              "Rechtsanspruch der Träger auf Defizitausgleich. "
              "Steuerungshebel: Kita-Finanzierungsrichtlinie (Mietobergrenzen, Träger-Eigenleistungen, "
              "Personalkostenobergrenzen für nicht-pädagogisches Personal nach § 16 ThürKitaG). "
              "Verpflegungskosten nach § 29 Abs. 3 ThürKitaG zu 100 % von Eltern zu tragen.",
    "365510": "ThürKitaG § 7 Abs. 2: Kita Betriebskosten freier Träger "
              "(Ev. Kirchenkreis – Kiga 'Arche Noah') – Rechtsanspruch. Wie 365500.",
    "365520": "ThürKitaG § 7 Abs. 2: Kita Betriebskosten (Verein für Waldorfpädagogik). Wie 365500.",
    "365530": "ThürKitaG § 7 Abs. 2: Kita Betriebskosten (Verband der Behinderten – Kiga 'Auenknirpse'). Wie 365500.",
    "365540": "ThürKitaG § 7 Abs. 2: Kita Betriebskosten (DRK Kreisverband). Wie 365500.",
    "365550": "ThürKitaG § 7 Abs. 2: Kita Betriebskosten (Diakonisches Werk – Kita 'Heiligenland'). Wie 365500.",
    "365560": "ThürKitaG § 7 Abs. 2: Kita Betriebskosten (AWO Pflegedienste – Kita 'Döllbergzwerge'). Wie 365500.",
    "365570": "ThürKitaG § 7 Abs. 2: Kita Betriebskosten (Kinder- und Jugenddorf Regenbogen e.V. – Kita 'Fröbel'). Wie 365500.",
    "365580": "ThürKitaG § 7 Abs. 2: Kita Betriebskosten (THEPRA – Kitas 'Tausendfüßler', 'Tabaluga', "
              "'Waldstrolche', 'Waldwichtel', 'Auenknirpse'). Wie 365500.",
    "365590": "ThürKitaG § 7 Abs. 2: Kita Betriebskosten (Volkssolidarität Südthüringen – Kita 'Kinderland' Goldlauter). Wie 365500.",
    "366400": "SGB VIII § 2: Sonstige Jugendhilfe – Pflicht mit Ermessen.",
    "367100": "Bundeskinderschutzgesetz (BKiSchG) § 3: Frühe Hilfen/Kinderschutz – "
              "Pflicht des öffentlichen Trägers der Jugendhilfe zur Vorhaltung von Netzwerken Frühe Hilfen. "
              "Kofinanziert durch Bundesinitiative; kommunaler Eigenanteil über Jugendförderplan steuerbar.",
    "367500": "SGB VIII: Sonstige Familienunterstützung – Pflicht mit Ermessen.",
    "341":    "SGB VIII §§ 42a ff.: Pflegekinderdienst/Adoptionsvermittlung/Inobhutnahme – "
              "Rechtsanspruch; sofortige Pflichtreaktion bei Inobhutnahme.",
    "347200": "SGB VIII: Sonstige soziale Leistungen Jugendhilfe – Rechtsanspruch.",

    # ── TP12: Einrichtungen Sozialdezernat ────────────────────────────────────
    "263":    "ThürKO § 2: Einrichtungen Sozialdezernat – Pflicht/Ermessen.",
    "271":    "ThürEBG § 11: Volkshochschule/Bildungseinrichtungen – Pflichtaufgabe Grundversorgung; "
              "Angebot und Gebühren im Ermessen.",
    "272":    "ThürKO § 2: Einrichtungen Sozialdezernat – Ermessen.",
}


# ─────────────────────────────────────────────────────────────────────────────
# 4. Hilfsfunktion: passendes Mapping finden (longer prefix wins)
# ─────────────────────────────────────────────────────────────────────────────

def lookup_rg(prod_nr: str) -> str | None:
    """Longest-prefix match in PRODUKT_RG."""
    best_len = 0
    best_val = None
    for key, val in PRODUKT_RG.items():
        if prod_nr.startswith(key) and len(key) > best_len:
            best_len = len(key)
            best_val = val
    return best_val


# ─────────────────────────────────────────────────────────────────────────────
# 5. DB-Update
# ─────────────────────────────────────────────────────────────────────────────

def run():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")

    # ── 5a) steuerungs_kategorien: Spalte rechtsgrundlage hinzufügen ──────────
    cols = {r["name"] for r in con.execute("PRAGMA table_info(steuerungs_kategorien)")}
    if "rechtsgrundlage" not in cols:
        con.execute("ALTER TABLE steuerungs_kategorien ADD COLUMN rechtsgrundlage TEXT")
        print("  [ALTER] steuerungs_kategorien: Spalte 'rechtsgrundlage' hinzugefügt.")

    for code, text in SK_RECHTSGRUNDLAGE.items():
        con.execute(
            "UPDATE steuerungs_kategorien SET rechtsgrundlage = ? WHERE code = ?",
            (text, code),
        )
    affected = con.execute("SELECT changes()").fetchone()[0]
    print(f"  [UPDATE] steuerungs_kategorien: {affected} Zeilen (SK-Rechtsgrundlagen).")

    # ── 5b) gesetze_katalog anlegen ───────────────────────────────────────────
    con.execute("""
        CREATE TABLE IF NOT EXISTS gesetze_katalog (
            id              INTEGER PRIMARY KEY,
            kuerzel         TEXT NOT NULL UNIQUE,
            vollname        TEXT NOT NULL,
            rechtsebene     TEXT NOT NULL,  -- BUND / LAND
            fundstelle      TEXT,
            kernaussage     TEXT
        )
    """)
    ins_count = 0
    upd_count = 0
    for kuerzel, vollname, ebene, fundstelle, kern in GESETZE:
        existing = con.execute(
            "SELECT id FROM gesetze_katalog WHERE kuerzel = ?", (kuerzel,)
        ).fetchone()
        if existing:
            con.execute(
                "UPDATE gesetze_katalog SET vollname=?, rechtsebene=?, fundstelle=?, kernaussage=? "
                "WHERE kuerzel=?",
                (vollname, ebene, fundstelle, kern, kuerzel),
            )
            upd_count += 1
        else:
            con.execute(
                "INSERT INTO gesetze_katalog (kuerzel, vollname, rechtsebene, fundstelle, kernaussage) "
                "VALUES (?, ?, ?, ?, ?)",
                (kuerzel, vollname, ebene, fundstelle, kern),
            )
            ins_count += 1
    print(f"  [UPSERT] gesetze_katalog: {ins_count} neu, {upd_count} aktualisiert.")

    # ── 5c) produkte.rechtsgrundlage anreichern ───────────────────────────────
    produkte = con.execute("SELECT id, produkt_nummer FROM produkte").fetchall()
    updated = 0
    skipped = 0
    for p in produkte:
        rg = lookup_rg(p["produkt_nummer"])
        if rg:
            con.execute(
                "UPDATE produkte SET rechtsgrundlage = ? WHERE id = ?",
                (rg, p["id"]),
            )
            updated += 1
        else:
            skipped += 1
    print(f"  [UPDATE] produkte.rechtsgrundlage: {updated} angereichert, {skipped} ohne Mapping.")

    con.commit()
    con.close()

    # ── 5d) Nicht gematchte Produkte ausgeben ─────────────────────────────────
    con2 = sqlite3.connect(DB_PATH)
    con2.row_factory = sqlite3.Row
    no_rg = con2.execute("""
        SELECT p.produkt_nummer, p.bezeichnung, t.nummer AS tp_nr, sk.code AS sk_code
        FROM produkte p
        LEFT JOIN teilplaene t ON p.teilplan_id = t.id
        LEFT JOIN steuerungs_kategorien sk ON p.steuerungs_kategorie_id = sk.id
        WHERE (p.rechtsgrundlage IS NULL OR p.rechtsgrundlage = '')
          AND p.steuerungs_kategorie_id IS NOT NULL
        ORDER BY t.nummer, p.produkt_nummer
    """).fetchall()
    if no_rg:
        print(f"\n  HINWEIS: {len(no_rg)} kategorisierte Produkte ohne Rechtsgrundlage:")
        for r in no_rg:
            print(f"    [{r['sk_code']:16s}] TP{r['tp_nr']} {r['produkt_nummer']} {r['bezeichnung'][:50]}")
    else:
        print("  Alle kategorisierten Produkte haben eine Rechtsgrundlage.")
    con2.close()

    print("\nFertig.")


if __name__ == "__main__":
    run()
