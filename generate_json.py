"""
generate_json.py - Exportiert Haushaltsdaten aus suhl_haushalt_2025.db nach budget_data.json
fuer das statische GitHub-Pages-Dashboard.
"""
import sqlite3, json, os
from datetime import datetime
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "suhl_haushalt_2025.db")
OUT_PATH = os.path.join(BASE_DIR, "budget_data.json")

GT_BY_YEAR = {
    2023: {"ertraege": 129_315_250.00, "aufwendungen": 129_724_490.00, "ergebnis": -409_240.00},
    2024: {"ertraege": 130_353_020.00, "aufwendungen": 133_802_080.00, "ergebnis": -3_449_060.00},
    2025: {"ertraege": 136_395_290.00, "aufwendungen": 138_003_230.00, "ergebnis": -1_607_940.00,
           "einzahlungen": 136_365_830.00, "auszahlungen": 135_802_480.00},
}

# Lesbare Produktnamen nach Thueringer Produktrahmen
# Ueberschreibt generische ETL-Bezeichnungen "Produkt XXXXXX"
PRODUKT_NAMEN = {
    # ── TP01 Verwaltungsführung ──────────────────────────────────────────────
    "111100": "Stadtrat – Ratsmitglieder & Vergütungen",
    "111110": "Stadtrat – Ausschüsse allgemein",
    "111120": "Stadtrat – Fraktionen",
    "111130": "Stadtrat – sonstige Gremien",
    "111140": "Bürgermeister – Büro & Repräsentation",
    "111150": "Bürgermeister – Verwaltungsvorstand",
    "111160": "Stadtrat – besondere Aufgaben",
    "111500": "Verwaltungsführung – allgemeine Verwaltung",
    "111600": "Verwaltungsführung – interne Koordination",
    "118000": "Allgemeine Verwaltung – sonstige Aufgaben",
    "511100": "Allgemeine Personalaufwendungen (Querschnitt)",
    "511200": "Allgemeine Verwaltungsaufwendungen (Querschnitt)",
    "522100": "Fahrzeuge & Geräte – Unterhalt intern",
    "523000": "Interne Dienstleistungen – zentrale Querschnittskosten",
    "536000": "Fahrzeuge & Gerätschaften – Verwaltung",
    "571000": "Interne Verwaltungsleistungen (Querschnitt)",
    # ── TP02 Kultur, Tourismus & Sport ──────────────────────────────────────
    "252110": "Stadtmuseum – Ausstellungen & Sammlungen",
    "252120": "Stadtmuseum – weitere Angebote",
    "252200": "Stadtgalerie & Kunstausstellungen",
    "252400": "Kulturpflege – sonstige Angebote",
    "262000": "Kulturförderung – Vereine & Verbände",
    "421000": "Theater & Konzertveranstaltungen",
    "424100": "Hallenbad & Schwimmsport",
    "424210": "Sportförderung – Vereinsförderung",
    "424220": "Sportförderung – Veranstaltungen",
    "424230": "Sportförderung – Nachwuchssport",
    "424240": "Sportförderung – Bezirks- & Landesangebote",
    "424250": "Sportförderung – sonstige Maßnahmen",
    "424300": "Freibad & Außensportanlagen",
    "424400": "Sportanlagen – allgemeine Pflege & Betrieb",
    "546100": "Stadtmarketing & Tourismusförderung",
    "573300": "Gebäudebewirtschaftung – Sport & Freizeit",
    "575000": "Stadtpark & Grünanlagen (allgemein)",
    "575010": "Stadtpark – Pflege & Unterhalt",
    "575020": "Grünanlagen – weitere Flächen",
    "575030": "Stadtpark – Sonderanlagen",
    "575040": "Grünanlagen – Baumbestand",
    "575050": "Grünanlagen – Spielplätze",
    "575060": "Grünanlagen – sonstige Flächen",
    "281000": "Sportstätten (inkl. Schulsport)",
    "281010": "Sportstätten – Schulsport",
    "281020": "Sportstätten – Vereinssport",
    "281030": "Sportstätten – Freibad",
    # ── TP03 Personal / Zentrale Dienste ────────────────────────────────────
    "112100": "Personal – Beamte & Tarifbeschäftigte",
    "112110": "Personal – Personalentwicklung",
    "112120": "Personal – Aus- & Fortbildung",
    "112200": "Personal – Arbeitssicherheit & Gesundheitsschutz",
    "113000": "IT-Infrastruktur & Digitalisierung",
    "114100": "Zentrale Dienste – allgemeine Aufgaben",
    "114110": "Zentrale Dienste – Beschaffung & Vergabe",
    "114120": "Zentrale Dienste – Fuhrpark & Logistik",
    "114200": "Zentrale Dienste – Archiv & Poststelle",
    "114400": "Gebäudemanagement – Liegenschaften",
    "114510": "Gebäudemanagement – technischer Dienst",
    "114520": "Gebäudemanagement – kaufmännischer Dienst",
    "114530": "Gebäudemanagement – Facility Management",
    "114550": "Gebäudemanagement – Reinigung & Bewachung",
    "114600": "Zentrale Dienste – sonstige Aufgaben",
    "252300": "Archiv & Dokumentation",
    "522200": "Interne Dienstleistungen – sonstige",
    "546000": "Zentrale Beschaffung & interne Dienste",
    "573110": "Gebäudebewirtschaftung – Rat & Verwaltung",
    "573120": "Gebäudebewirtschaftung – Schulen",
    "573130": "Gebäudebewirtschaftung – Kultur & Sport",
    "573140": "Gebäudebewirtschaftung – Soziales & Gesundheit",
    # ── TP04 Finanzverwaltung ────────────────────────────────────────────────
    "116000": "Finanz- & Abgabenverwaltung",
    "117100": "Abgabenwesen – Grundsteuer & Gewerbesteuer",
    "117200": "Abgabenwesen – sonstige Abgaben & Gebühren",
    "411200": "Wirtschaftsförderung & Tourismusmarketing",
    "547000": "Kassen- & Finanzverwaltung",
    "535000": "Haushaltswirtschaft & Rechnungswesen",
    # ── TP05 Öffentliche Flächen & Straßen ──────────────────────────────────
    "541000": "Gemeindestraßen – Gesamtnetz",
    "541010": "Gemeindestraßen – Hauptstraßen",
    "541020": "Gemeindestraßen – Sondermaßnahmen",
    "541030": "Gemeindestraßen – Nebenarbeiten & Winterdienst",
    "541050": "Straßen – Brücken & Ingenieurbauten",
    "541060": "Straßen – Gehwege & Radwege",
    "541070": "Straßenbeleuchtung",
    "542010": "Kreisstraßen – sächliche Unterhaltung",
    "542070": "Kreisstraßen – Nebenarbeiten",
    "543010": "Gemeindestraßen – Sondermaßnahmen II",
    "543070": "Wege & Plätze – allgemeine Unterhaltung",
    "551000": "Öffentliches Grün & Landschaftspflege",
    "551100": "Naturschutz – Schutzgebiete & Ausgleichsflächen",
    "553010": "Friedhofs- & Bestattungswesen",
    "553020": "Friedhof – Erweiterungsmaßnahmen",
    "366300": "Sonstige Flächenmaßnahmen",
    # ── TP06 Allgemeine Finanzwirtschaft ────────────────────────────────────
    "611000": "Steuern, Schlüsselzuweisungen & allg. Deckungsmittel",
    "612000": "Allgemeine Schlüsselzuweisungen (ThürFAG)",
    "622010": "Kreditverwaltung & Zinsdienst",
    "625000": "Kreditfinanzierung & Schuldendienst",
    # ── TP07 Ordnung & Sicherheit ────────────────────────────────────────────
    "119000": "Allgemeine Verwaltung – Ordnung",
    "121100": "Meldewesen – Einwohnerregistrierung",
    "121200": "Standesamt – allgemeine Aufgaben",
    "121210": "Standesamt – Eheschließungen",
    "121220": "Standesamt – Sterbefälle & Beurkundungen",
    "121230": "Standesamt – Personenstandsurkunden",
    "121240": "Standesamt – besondere Aufgaben",
    "122100": "Ordnungsamt – öffentliche Ordnung & Sicherheit",
    "122200": "Ordnungsamt – Gewerbeaufsicht",
    "122300": "Gewerberecht – Erlaubnisverfahren",
    "122310": "Gewerberecht – Anmeldungen & Abmeldungen",
    "122320": "Gewerberecht – Kontrolle & Vollzug",
    "122400": "Ordnungsamt – sonstige Aufgaben",
    "122500": "Ordnungsamt – besondere Ordnungsaufgaben",
    "123100": "Feuerwehr – vorbeugender Brandschutz",
    "123300": "Rettungsdienst",
    "123400": "Abwehrender Brandschutz & Katastrophenschutz",
    "123500": "Katastrophenschutz – besondere Aufgaben",
    "124100": "Veterinäramt – Lebensmittelüberwachung",
    "124200": "Veterinäramt – Tierschutz & Tiergesundheit",
    "126010": "Feuerwehr – Berufsfeuerwehr",
    "126020": "Ordnungsdienst & öffentliche Sicherheit",
    "127000": "Bevölkerungsschutz – Zivilschutz",
    "128000": "Einwohnerwesen – Meldewesen & Passrecht",
    "573200": "Fahrzeuge & Gerätschaften – Ordnung & Sicherheit",
    # ── TP08 Umwelt ──────────────────────────────────────────────────────────
    "253000": "Stadtplanung & Umweltplanung",
    "521000": "Straßen & Wege – interner Unterhalt",
    "537010": "Abfallentsorgung – Haushaltsmüll",
    "537020": "Abfallentsorgung – Sonderabfall",
    "537030": "Abfallentsorgung – weitere Aufgaben",
    "537040": "Abfallentsorgung – Grünschnitt & Kompost",
    "545110": "Friedhöfe – Bewirtschaftung",
    "545120": "Friedhöfe – Sondermaßnahmen",
    "552000": "Natur- & Klimaschutz",
    "554000": "Gewässerunterhaltung",
    "554100": "Gewässerpflege & Ökologie",
    "555000": "Naturschutz & Landschaftspflege",
    "561000": "Kommunale Wärmeplanung (WPG-Pflicht)",
    # ── TP09 Soziales & Gesundheit ───────────────────────────────────────────
    "111500": "Allgemeine Verwaltung (Sozialbereich)",
    "311000": "Kosten der Unterkunft & Heizung (SGB II/XII)",
    "311100": "Hilfe zum Lebensunterhalt (SGB XII § 27)",
    "311110": "Hilfe zum Lebensunterhalt – laufende Hilfen",
    "311120": "Hilfe zum Lebensunterhalt – einmalige Hilfen",
    "311130": "Hilfe zum Lebensunterhalt – Sonderfälle",
    "311200": "Grundsicherung im Alter & bei Erwerbsminderung",
    "311201": "Grundsicherung im Alter – stationär",
    "311210": "Grundsicherung im Alter – ambulant",
    "311220": "Grundsicherung – Einrichtungen",
    "311230": "Grundsicherung bei Erwerbsminderung",
    "311240": "Grundsicherung – weitere Leistungen",
    "311260": "Grundsicherung – Sonderleistungen",
    "311270": "Grundsicherung – Wohnen",
    "311280": "Grundsicherung – Bedarfsermittlung",
    "311290": "Grundsicherung – sonstige Leistungen",
    "311400": "SGB XII – Hilfe in besonderen Lebenslagen",
    "311500": "Eingliederungshilfe – Wohnen (SGB IX)",
    "311510": "Eingliederungshilfe – Tagesstruktur",
    "311520": "Eingliederungshilfe – Teilhabe am Leben",
    "311550": "Eingliederungshilfe – sonstige Leistungen",
    "311600": "Eingliederungshilfe – allgemein (SGB IX)",
    "311610": "Eingliederungshilfe – vollstationär",
    "311620": "Eingliederungshilfe – teilstationär",
    "311630": "Eingliederungshilfe – ambulant",
    "311700": "SGB XII – sonstige Hilfen",
    "311800": "SGB XII – Hilfen in Notlagen",
    "312100": "Kosten der Unterkunft SGB XII",
    "312200": "Kosten der Unterkunft SGB XII – Sonderfälle",
    "312300": "SGB XII – besondere Lebenslagen",
    "312600": "SGB XII – weitere Leistungen",
    "313000": "Hilfe zur Pflege (SGB XII §§ 61 ff.)",
    "314000": "Sonstige SGB XII-Hilfen (Blindengeld, Landesrecht)",
    "315410": "Grundsicherung – Lebensunterhalt in Einrichtungen",
    "315500": "SGB XII – stationäre Hilfen",
    "315600": "SGB XII – ambulante Hilfen",
    "316000": "Eingliederungshilfe & Schulbegleitung (SGB IX)",
    "316100": "Eingliederungshilfe – Wohnen vollstationär",
    "316210": "Eingliederungshilfe – Tagesstruktur",
    "316300": "Eingliederungshilfe – ambulante Leistungen",
    "316400": "Schulbegleitung – allgemein (SGB IX)",
    "316411": "Schulbegleitung – Primarstufe",
    "316412": "Schulbegleitung – Sekundarstufe I",
    "316421": "Schulbegleitung – Gymnasium",
    "316422": "Schulbegleitung – Förderschule",
    "316430": "Schulbegleitung – Berufsschule",
    "316440": "Schulbegleitung – Pool-Modelle",
    "316462": "Eingliederungshilfe – Freizeitangebote",
    "316470": "Eingliederungshilfe – Bildung & Qualifikation",
    "316480": "Eingliederungshilfe – sonstige Teilhabe",
    "316500": "Eingliederungshilfe – weitere Leistungen",
    "331000": "Soziale Beratungsdienste & Schuldnerberatung",
    "343000": "Sonstige soziale Hilfen (SGB XII)",
    "345000": "Asylbewerberleistungen (AsylbLG)",
    "346000": "Soziale Leistungen – Flüchtlingsbetreuung",
    "347200": "Sonstige Jugendhilfeleistungen",
    "348000": "Flüchtlingsunterbringung & -integration",
    "351400": "Gesundheitsamt – Amtsärztlicher Dienst",
    "351700": "Gesundheitsamt – öffentlicher Gesundheitsdienst",
    "412000": "Gesundheitsförderung & Prävention",
    "414000": "Gesundheitsförderung – Sport & Bewegungsangebote",
    "522200": "Interne Dienste Sozialbereich",
    # ── TP10 Schulträgeraufgaben ─────────────────────────────────────────────
    "201000": "Schulverwaltung – allgemeine Aufgaben",
    "211100": "Grundschulen – sächliche Schulträgerschaft",
    "211200": "Gemeinschaftsschulen – sächliche Schulträgerschaft",
    "211300": "Regelschulen – sächliche Schulträgerschaft",
    "211400": "Gymnasien – sächliche Schulträgerschaft",
    "212000": "Berufliche Schulen – sächliche Schulträgerschaft",
    "212010": "Berufliche Schulen – Ausstattung & Unterhalt",
    "212020": "Berufliche Schulen – Verwaltung",
    "212100": "Berufsschulen – sächliche Schulträgerschaft",
    "216100": "Regelschulen – sächliche Schulträgerschaft II",
    "216300": "Regelschulen – Ausstattung & Möblierung",
    "217010": "Berufliche Schulen – sächliche Trägerschaft",
    "217020": "Berufliche Schulen – Ausstattung",
    "221100": "Förderschulen – sächliche Schulträgerschaft",
    "221200": "Förderschulen – Ausstattung & Unterhalt",
    "231000": "Schülerbeförderung & Schulträgerschaft",
    "241000": "Schülerförderung & Beförderung",
    "243000": "Schulsozialarbeit",
    "243010": "Schulsozialarbeit – Beratung",
    "243020": "Schulsozialarbeit – Ausbau",
    # ── TP11 Kinder-, Jugend- & Familienhilfe ───────────────────────────────
    "341000": "Pflegekinderdienst & Adoptionsvermittlung",
    "351500": "Gesundheitsdienst Kinder & Jugend",
    "360000": "Kinder-, Jugend- & Familienhilfe – allgemein",
    "361000": "Jugendarbeit – allgemeine Angebote",
    "361010": "Jugendarbeit – offene Jugendarbeit",
    "361020": "Jugendarbeit – mobile Jugendarbeit",
    "362000": "Jugendarbeit / Jugendsozialarbeit",
    "362010": "Jugendarbeit – Jugendzentren",
    "362020": "Jugendarbeit – offene Angebote",
    "362030": "Jugendarbeit – Ferienangebote",
    "362040": "Jugendarbeit – Ehrenamtsförderung",
    "362080": "Jugendarbeit – Prävention",
    "362090": "Jugendarbeit – weitere Maßnahmen",
    "363000": "Hilfen zur Erziehung (HzE – SGB VIII)",
    "363100": "HzE – Erziehungsberatung (§ 28 SGB VIII)",
    "363120": "HzE – Erziehungsbeistandschaft (§ 30 SGB VIII)",
    "363130": "HzE – Sozialpäd. Familienhilfe (§ 31 SGB VIII)",
    "363210": "HzE – Tagesgruppe (§ 32 SGB VIII)",
    "363220": "HzE – Tagesgruppe II",
    "363230": "HzE – teilstationäre Angebote",
    "363240": "HzE – teilstationäre Maßnahmen",
    "363300": "HzE – Vollzeitpflege allgemein (§ 33 SGB VIII)",
    "363310": "HzE – Vollzeitpflege Pflegefamilien",
    "363330": "HzE – Vollzeitpflege (regulär, § 33 SGB VIII)",
    "363340": "HzE – Vollzeitpflege sonderpädagogisch",
    "363350": "HzE – Heimunterbringung I (§ 34 SGB VIII)",
    "363360": "HzE – Heimunterbringung II",
    "363370": "HzE – Heimunterbringung (§ 34 SGB VIII)",
    "363380": "HzE – Vollzeitpflege & Familienpflege (§ 33)",
    "363410": "HzE – Heimunterbringung besonderer Bedarf",
    "363420": "HzE – stationäre Hilfen (§ 34 SGB VIII)",
    "363500": "HzE – Intensive Einzelbetreuung ISE (§ 35)",
    "363520": "HzE – Intensive Einzelbetreuung II",
    "363530": "HzE – Intensive Einzelbetreuung III",
    "363540": "HzE – Intensive Einzelbetreuung IV",
    "363700": "HzE – Intensive pädagogische Einzelbetreuung",
    "364000": "HzE – Inobhutnahme & § 35a SGB VIII",
    "365200": "Kindertagesbetreuung – Betriebskostenförderung",
    "365210": "Kindertagesbetreuung – weitere Träger",
    "365500": "Kita – Betriebskostenförderung freier Träger",
    "365510": "Kita – Städtische Einrichtungen",
    "365520": "Kita – Integrationsangebote",
    "365530": "Kita – Bedarfsplanung",
    "365540": "Kita – Förderung freier Träger I",
    "365550": "Kita – Förderung freier Träger II",
    "365560": "Kita – Förderung freier Träger III",
    "365570": "Kita – weitere Einrichtungen",
    "365580": "Kita – Inklusive Angebote",
    "365590": "Kita – sonstige Einrichtungen",
    "366400": "Sonstige Jugendhilfeleistungen",
    "367100": "Frühe Hilfen & Kinderschutz (BKiSchG)",
    "367500": "Familienunterstützende Leistungen",
    # ── TP12 Einrichtungen Sozialdezernat ────────────────────────────────────
    "263000": "Bildungs- & Beratungseinrichtungen (Sozialdezernat)",
    "271000": "Volkshochschule (Grundversorgung)",
    "272000": "Sonstige Bildungseinrichtungen (Sozialdezernat)",
}

TP_NAMEN_SCHOEN = {
    "01": "Verwaltungsführung",
    "02": "Kultur, Tourismus & Sport",
    "03": "Personal / Zentrale Dienste",
    "04": "Finanzverwaltung",
    "05": "Öffentliche Flächen & Straßen",
    "06": "Allgemeine Finanzwirtschaft",
    "07": "Ordnung & Sicherheit",
    "08": "Umwelt",
    "09": "Soziales & Gesundheit",
    "10": "Schulträgeraufgaben",
    "11": "Kinder-, Jugend- & Familienhilfe",
    "12": "Einrichtungen Sozialdezernat",
}


def kk4_gruppe(konto_nr: str) -> str:
    if not konto_nr or not konto_nr.startswith("4"):
        return "Sonstige Erträge"
    p2 = konto_nr[:2]
    p3 = konto_nr[:3]
    if p2 == "40":
        return "Steuern & Steueranteile"
    if p3 in ("411","412","413","414","415"):
        return "Schlüsselzuweisungen & FAG-Ausgleich"
    if p2 in ("43","44"):
        return "Gebühren & Entgelte"
    if p2 == "42":
        return "Soziale Erstattungen (SGB)"
    if p2 == "47":
        return "Finanzertrag & Beteiligungen"
    return "Sonstige Erträge"


def kk_sum_y(con, kk_nr, jahr, typ):
    # For FINANZPLANUNG: use only the most recent HH-Plan document per daten_jahr
    # (each document contains multi-year projections; without this filter we'd sum all)
    if typ == "FINANZPLANUNG":
        return con.execute("""
            SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h
            JOIN konten k ON h.konto_id=k.id
            JOIN kontenklassen kk ON k.kontenklasse_id=kk.id
            WHERE h.daten_jahr=? AND h.wert_typ=? AND kk.nummer=?
              AND h.haushaltsplan_jahr = (
                  SELECT MAX(h2.haushaltsplan_jahr) FROM haushaltswerte h2
                  WHERE h2.daten_jahr=? AND h2.wert_typ='FINANZPLANUNG'
              )
        """, (jahr, typ, kk_nr, jahr)).fetchone()[0]
    return con.execute("""
        SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h
        JOIN konten k ON h.konto_id=k.id
        JOIN kontenklassen kk ON k.kontenklasse_id=kk.id
        WHERE h.daten_jahr=? AND h.wert_typ=? AND kk.nummer=?
    """, (jahr, typ, kk_nr)).fetchone()[0]


def make_meta(con, jahr):
    gt = GT_BY_YEAR[jahr]
    meta = {
        "titel":               f"Haushaltsplan Stadt Suhl {jahr}",
        "ertraege_soll":       gt["ertraege"],
        "aufwendungen_soll":   gt["aufwendungen"],
        "jahresergebnis_soll": gt["ergebnis"],
        "ertraege_etl":        round(kk_sum_y(con, 4, jahr, "PLAN_ANSATZ"), 2),
        "aufwendungen_etl":    round(kk_sum_y(con, 5, jahr, "PLAN_ANSATZ"), 2),
        "einzahlungen_etl":    round(kk_sum_y(con, 6, jahr, "PLAN_ANSATZ"), 2),
        "auszahlungen_etl":    round(kk_sum_y(con, 7, jahr, "PLAN_ANSATZ"), 2),
        "generiert_am":        datetime.now().isoformat(),
    }
    if "einzahlungen" in gt:
        meta["einzahlungen_soll"]   = gt["einzahlungen"]
        meta["auszahlungen_soll"]   = gt["auszahlungen"]
        meta["finanzergebnis_soll"] = round(gt["einzahlungen"] - gt["auszahlungen"], 2)
    return meta


def make_teilplaene(con, jahr):
    tps = []
    for tp in con.execute("SELECT id, nummer, bezeichnung FROM teilplaene ORDER BY nummer"):
        tid, tp_nr = tp["id"], tp["nummer"]

        def tp_kk(kk_nr, _tid=tid, _jahr=jahr):
            return round(con.execute("""
                SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h
                JOIN konten k ON h.konto_id=k.id
                JOIN kontenklassen kk ON k.kontenklasse_id=kk.id
                JOIN produkte p ON h.produkt_id=p.id
                WHERE p.teilplan_id=? AND h.daten_jahr=?
                  AND h.wert_typ='PLAN_ANSATZ' AND kk.nummer=?
            """, (_tid, _jahr, kk_nr)).fetchone()[0], 2)

        nach_sk = {}
        for code in ("FREIWILLIG", "PFLICHT_ERMESSEN", "PFLICHT_STRIKT", "UEBERTRAGEN"):
            nach_sk[code] = round(con.execute("""
                SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h
                JOIN konten k ON h.konto_id=k.id
                JOIN kontenklassen kk ON k.kontenklasse_id=kk.id
                JOIN produkte p ON h.produkt_id=p.id
                LEFT JOIN steuerungs_kategorien sk ON p.steuerungs_kategorie_id=sk.id
                WHERE p.teilplan_id=? AND h.daten_jahr=?
                  AND h.wert_typ='PLAN_ANSATZ' AND kk.nummer=5 AND sk.code=?
            """, (tid, jahr, code)).fetchone()[0], 2)

        nach_sk["unbekannt"] = round(con.execute("""
            SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h
            JOIN konten k ON h.konto_id=k.id
            JOIN kontenklassen kk ON k.kontenklasse_id=kk.id
            JOIN produkte p ON h.produkt_id=p.id
            WHERE p.teilplan_id=? AND h.daten_jahr=?
              AND h.wert_typ='PLAN_ANSATZ' AND kk.nummer=5
              AND p.steuerungs_kategorie_id IS NULL
        """, (tid, jahr)).fetchone()[0], 2)

        tps.append({
            "tp_nr":   tp_nr,
            "tp_name": TP_NAMEN_SCHOEN.get(tp_nr, tp["bezeichnung"]),
            "ertraege":     tp_kk(4),
            "aufwendungen": tp_kk(5),
            "aufwendungen_nach_steuerung": nach_sk,
        })
    return tps


def make_ertragsquellen(con, jahr):
    gruppen = defaultdict(float)
    for r in con.execute("""
        SELECT k.konto_nummer, SUM(h.betrag) AS betrag FROM haushaltswerte h
        JOIN konten k ON h.konto_id=k.id
        JOIN kontenklassen kk ON k.kontenklasse_id=kk.id
        WHERE h.daten_jahr=? AND h.wert_typ='PLAN_ANSATZ' AND kk.nummer=4
        GROUP BY k.konto_nummer
    """, (jahr,)):
        gruppen[kk4_gruppe(r["konto_nummer"])] += r["betrag"]

    return [
        {"gruppe": g, "betrag": round(v, 2)}
        for g, v in sorted(gruppen.items(), key=lambda x: -x[1])
    ]


def make_details_tp(con):
    """Pro TP → Produkte → Konten (KK4+5, PLAN_ANSATZ, 2023/24/25)."""
    result = {}
    for tp in con.execute("SELECT id, nummer FROM teilplaene ORDER BY nummer"):
        tid, tp_nr = tp["id"], tp["nummer"]
        produkte = []
        for p in con.execute("""
            SELECT p.id, p.produkt_nummer, p.bezeichnung, sk.code AS sk_code
            FROM produkte p
            LEFT JOIN steuerungs_kategorien sk ON p.steuerungs_kategorie_id = sk.id
            WHERE p.teilplan_id = ?
            ORDER BY p.produkt_nummer
        """, (tid,)):
            pid, pnr = p["id"], p["produkt_nummer"]
            konten_by_nr = {}
            for k in con.execute("""
                SELECT k.konto_nummer, k.bezeichnung, kk.nummer AS kk_nr,
                       h.daten_jahr, SUM(h.betrag) AS betrag
                FROM haushaltswerte h
                JOIN konten k ON h.konto_id = k.id
                JOIN kontenklassen kk ON k.kontenklasse_id = kk.id
                WHERE h.produkt_id = ? AND h.daten_jahr IN (2023, 2024, 2025)
                  AND h.wert_typ = 'PLAN_ANSATZ' AND kk.nummer IN (4, 5)
                GROUP BY k.konto_nummer, h.daten_jahr
                ORDER BY kk.nummer, k.konto_nummer
            """, (pid,)):
                knr = k["konto_nummer"]
                yr_key = f"b{str(k['daten_jahr'])[2:]}"
                if knr not in konten_by_nr:
                    konten_by_nr[knr] = {
                        "knr": knr, "bez": k["bezeichnung"],
                        "kk": k["kk_nr"],
                        "b23": 0.0, "b24": 0.0, "b25": 0.0,
                    }
                konten_by_nr[knr][yr_key] = round(k["betrag"], 2)
            konten = [v for v in konten_by_nr.values()
                      if v["b23"] or v["b24"] or v["b25"]]
            if not konten:
                continue
            produkte.append({
                "pnr":    pnr,
                "name":   PRODUKT_NAMEN.get(pnr, p["bezeichnung"]),
                "sk":     p["sk_code"] or "unbekannt",
                "konten": konten,
            })
        result[tp_nr] = {
            "tp_name":  TP_NAMEN_SCHOEN.get(tp_nr, tp_nr),
            "produkte": produkte,
        }
    return result


def make_personal(con):
    """
    Exportiert Personalkosten-Daten für den Personal-Tab.
    Kontengruppen:
      bez_beamte  : 5021xxx  – Dienstbezüge Beamte
      bez_tarif   : 5022xxx + 5023xxx + 5024xxx + 5029xxx – Dienstbezüge Tarif/Sonstige
      vers_beamte : 5031xxx  – Versorgungskasse Beamte
      vers_tarif  : 5032xxx + 5039xxx – Versorgungskasse Tarif
      sv          : 5042xxx + 5043xxx + 5049xxx – Sozialversicherung
      beihilfen   : 5051xxx + 5052xxx – Beihilfen & Unterstützungen
      sonstiges   : 5062xxx + 5071xxx + 5013xxx + 5019xxx – Nebenkosten & Rückstellungen
    """
    YEARS = [2023, 2024, 2025]
    WERT_TYP = "PLAN_ANSATZ"

    def konto_gruppe(konto_nr):
        p = konto_nr[:4]
        if p == "5021":                           return "bez_beamte"
        if p in ("5022","5023","5024","5029"):    return "bez_tarif"
        if p == "5031":                           return "vers_beamte"
        if p in ("5032","5039"):                  return "vers_tarif"
        if p in ("5042","5043","5049"):           return "sv"
        if p in ("5051","5052"):                  return "beihilfen"
        if p in ("5062","5071","5013","5019"):    return "sonstiges"
        return None

    GRUPPEN_LABELS = {
        "bez_beamte":  "Dienstbezüge Beamte",
        "bez_tarif":   "Dienstbezüge Tarifbeschäftigte",
        "vers_beamte": "Versorgungskasse Beamte",
        "vers_tarif":  "Versorgungskasse Tarif",
        "sv":          "Sozialversicherung",
        "beihilfen":   "Beihilfen & Unterstützungen",
        "sonstiges":   "Nebenkosten & Rückstellungen",
    }

    by_year = {}
    for yr in YEARS:
        rows = con.execute("""
            SELECT t.nummer AS tp_nr, t.bezeichnung AS tp_name,
                   k.konto_nummer, SUM(h.betrag) AS betrag
            FROM haushaltswerte h
            JOIN produkte p   ON h.produkt_id = p.id
            JOIN teilplaene t ON p.teilplan_id = t.id
            JOIN konten k     ON h.konto_id    = k.id
            WHERE h.daten_jahr = ? AND h.wert_typ = ?
              AND (k.konto_nummer LIKE '501%'
                OR k.konto_nummer LIKE '502%'
                OR k.konto_nummer LIKE '503%'
                OR k.konto_nummer LIKE '504%'
                OR k.konto_nummer LIKE '505%'
                OR k.konto_nummer LIKE '506%'
                OR k.konto_nummer LIKE '507%')
            GROUP BY t.nummer, k.konto_nummer
        """, (yr, WERT_TYP)).fetchall()

        gesamt_gruppen = {g: 0.0 for g in GRUPPEN_LABELS}
        nach_tp = {}

        for r in rows:
            gr = konto_gruppe(r["konto_nummer"])
            if gr is None:
                continue
            tp = r["tp_nr"]
            if tp not in nach_tp:
                nach_tp[tp] = {
                    "name": TP_NAMEN_SCHOEN.get(tp, r["tp_name"]),
                    **{g: 0.0 for g in GRUPPEN_LABELS},
                }
            nach_tp[tp][gr]  = nach_tp[tp].get(gr, 0.0) + (r["betrag"] or 0.0)
            gesamt_gruppen[gr] += (r["betrag"] or 0.0)

        # Gesamtsummen und TP-Totals
        for tp_data in nach_tp.values():
            tp_data["gesamt"] = sum(tp_data[g] for g in GRUPPEN_LABELS)

        gesamt = sum(gesamt_gruppen.values())

        total_kk5 = con.execute(
            "SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h "
            "JOIN konten k ON h.konto_id=k.id "
            "JOIN kontenklassen kk ON k.kontenklasse_id=kk.id "
            "WHERE kk.nummer=5 AND h.daten_jahr=? AND h.wert_typ=?",
            (yr, WERT_TYP)
        ).fetchone()[0]
        personalquote_pct = round(gesamt / total_kk5 * 100, 1) if total_kk5 > 0 else None

        by_year[str(yr)] = {
            "gesamt":             round(gesamt, 2),
            "personalquote_pct":  personalquote_pct,
            **{g: round(v, 2) for g, v in gesamt_gruppen.items()},
            "nach_tp": {
                tp: {k: round(v, 2) if isinstance(v, float) else v
                     for k, v in data.items()}
                for tp, data in sorted(nach_tp.items())
            },
        }

    # Personalquote-Zeitreihe 2021-2025 (IST für 2021-2023, Plan für 2024/2025)
    FULL_YEARS = [
        (2021, "IST_ERGEBNIS", "Ist 2021",  False),
        (2022, "IST_ERGEBNIS", "Ist 2022",  False),
        (2023, "IST_ERGEBNIS", "Ist 2023",  False),
        (2024, "PLAN_ANSATZ",  "Plan 2024", True),
        (2025, "PLAN_ANSATZ",  "Plan 2025", True),
    ]
    personalquote_zeitreihe = []
    for yr_f, wt_f, lbl_f, prog_f in FULL_YEARS:
        personal_sum = con.execute(
            "SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h "
            "JOIN konten k ON h.konto_id=k.id "
            "WHERE k.konto_nummer LIKE '50%' AND h.daten_jahr=? AND h.wert_typ=?",
            (yr_f, wt_f)
        ).fetchone()[0]
        kk5_sum = con.execute(
            "SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h "
            "JOIN konten k ON h.konto_id=k.id "
            "JOIN kontenklassen kk ON k.kontenklasse_id=kk.id "
            "WHERE kk.nummer=5 AND h.daten_jahr=? AND h.wert_typ=?",
            (yr_f, wt_f)
        ).fetchone()[0]
        personalquote_zeitreihe.append({
            "jahr":          yr_f,
            "label":         lbl_f,
            "ist_prognose":  prog_f,
            "personal_teur": round(personal_sum / 1000),
            "kk5_teur":      round(kk5_sum / 1000),
            "quote_pct":     round(personal_sum / kk5_sum * 100, 1) if kk5_sum > 0 else None,
        })

    return {
        "gruppen_labels":           GRUPPEN_LABELS,
        "by_year":                  by_year,
        "personalquote_zeitreihe":  personalquote_zeitreihe,
    }


def make_stellenplan(con):
    """
    Exportiert Stellenplan-Daten (besoldungsgruppen + stellenplan) je Jahr.
    Gibt None zurück, falls die Tabellen noch leer sind.
    """
    count = con.execute("SELECT COUNT(*) FROM stellenplan").fetchone()[0]
    if count == 0:
        return None

    rows_all = con.execute("""
        SELECT bg.kuerzel, bg.typ,
               t.nummer AS tp_nr,
               s.daten_jahr, s.wert_typ, s.planstellen
        FROM stellenplan s
        JOIN besoldungsgruppen bg ON s.besoldungsgruppe_id = bg.id
        JOIN teilplaene t         ON s.teilplan_id         = t.id
        ORDER BY s.daten_jahr, s.wert_typ, bg.typ, bg.kuerzel
    """).fetchall()

    # Alle bekannten Jahre + wert_typen
    jahre = sorted({r["daten_jahr"] for r in rows_all})
    by_year = {}

    for yr in jahre:
        for wt in ["PLAN_ANSATZ", "IST"]:
            rows = [r for r in rows_all if r["daten_jahr"] == yr and r["wert_typ"] == wt]
            if not rows:
                continue

            # Aggregation je typ
            beamte = sum(r["planstellen"] for r in rows if r["typ"] == "BEAMTE")
            tarif  = sum(r["planstellen"] for r in rows if r["typ"] == "TARIF")

            # nach TP
            nach_tp: dict[str, dict] = {}
            for r in rows:
                tp = r["tp_nr"]
                if tp not in nach_tp:
                    nach_tp[tp] = {"beamte": 0.0, "tarif": 0.0}
                nach_tp[tp][r["typ"].lower()] += r["planstellen"]
            for td in nach_tp.values():
                td["gesamt"] = round(td["beamte"] + td["tarif"], 3)
                td["beamte"] = round(td["beamte"], 3)
                td["tarif"]  = round(td["tarif"],  3)

            # nach Besoldungsgruppe (gesamt über alle TPs)
            nach_gruppe: dict[str, dict] = {}
            for r in rows:
                kg = r["kuerzel"]
                if kg not in nach_gruppe:
                    nach_gruppe[kg] = {"typ": r["typ"], "planstellen": 0.0}
                nach_gruppe[kg]["planstellen"] += r["planstellen"]
            nach_gruppe = {
                kg: {"typ": v["typ"], "planstellen": round(v["planstellen"], 3)}
                for kg, v in sorted(nach_gruppe.items())
            }

            # nach TP + Besoldungsgruppe (für aufklappbare Detailansicht)
            nach_tp_detail: dict[str, dict] = {}
            for r in rows:
                tp = r["tp_nr"]
                if tp not in nach_tp_detail:
                    nach_tp_detail[tp] = {
                        "name": TP_NAMEN_SCHOEN.get(tp, f"TP {tp}"),
                        "beamte": {}, "tarif": {}
                    }
                kg = r["kuerzel"]
                bucket = "beamte" if r["typ"] == "BEAMTE" else "tarif"
                nach_tp_detail[tp][bucket][kg] = (
                    nach_tp_detail[tp][bucket].get(kg, 0.0) + r["planstellen"]
                )
            # Auf Listen umformen, 0-Einträge filtern, sortieren
            for tp_d in nach_tp_detail.values():
                tp_d["beamte"] = sorted(
                    [{"kuerzel": k, "planstellen": round(v, 3)}
                     for k, v in tp_d["beamte"].items() if v > 0],
                    key=lambda x: x["kuerzel"]
                )
                tp_d["tarif"] = sorted(
                    [{"kuerzel": k, "planstellen": round(v, 3)}
                     for k, v in tp_d["tarif"].items() if v > 0],
                    key=lambda x: x["kuerzel"]
                )

            key = f"{yr}_{wt}"
            by_year[key] = {
                "daten_jahr":    yr,
                "wert_typ":      wt,
                "gesamt":        round(beamte + tarif, 3),
                "beamte":        round(beamte, 3),
                "tarif":         round(tarif,  3),
                "nach_tp":       {tp: v for tp, v in sorted(nach_tp.items())},
                "nach_gruppe":   nach_gruppe,
                "nach_tp_detail": {tp: v for tp, v in sorted(nach_tp_detail.items())},
            }

    return {"by_year": by_year} if by_year else None


def main():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    result = {}

    # ── by_year: pro Jahr meta + teilplaene + ertragsquellen ─────────────────
    by_year = {}
    for yr in [2023, 2024, 2025]:
        by_year[str(yr)] = {
            "meta":          make_meta(con, yr),
            "teilplaene":    make_teilplaene(con, yr),
            "ertragsquellen": make_ertragsquellen(con, yr),
        }
    result["by_year"] = by_year

    # Root-level zeigt auf 2025-Daten (rueckwaertskompatibel fuer Simulator etc.)
    result["meta"]          = by_year["2025"]["meta"]
    result["teilplaene"]    = by_year["2025"]["teilplaene"]
    result["ertragsquellen"] = by_year["2025"]["ertragsquellen"]

    # ── Zeitreihe: 2023 PLAN aus 2023-ETL; IST-Werte aus 2025-ETL-Perspektive
    jahre_zt = [
        (2021, "IST_ERGEBNIS",   "Ist 2021",     False),
        (2022, "IST_ERGEBNIS",   "Ist 2022",     False),
        (2023, "PLAN_ANSATZ",    "Ansatz 2023",  False),
        (2023, "IST_ERGEBNIS",   "Ist 2023",     False),
        (2024, "ANSATZ_VORJAHR", "Ansatz 2024",  False),
        (2025, "PLAN_ANSATZ",    "Ansatz 2025",  False),
        (2026, "FINANZPLANUNG",  "Planung 2026", True),
        (2027, "FINANZPLANUNG",  "Planung 2027", True),
        (2028, "FINANZPLANUNG",  "Planung 2028", True),
    ]
    result["zeitreihe"] = [
        {
            "jahr": j, "typ": t, "label": lbl, "ist_prognose": prog,
            "ertraege":     round(kk_sum_y(con, 4, j, t), 2),
            "aufwendungen": round(kk_sum_y(con, 5, j, t), 2),
            "einzahlungen": round(kk_sum_y(con, 6, j, t), 2),
            "auszahlungen": round(kk_sum_y(con, 7, j, t), 2),
        }
        for j, t, lbl, prog in jahre_zt
    ]

    # ── Simulator-Produkte (immer 2025-Basis) ────────────────────────────────
    max_kuerz = {
        "FREIWILLIG":    100,
        "PFLICHT_ERMESSEN": 15,
        "PFLICHT_STRIKT":    0,
        "UEBERTRAGEN":       0,
    }
    sim = []
    for r in con.execute("""
        SELECT p.produkt_nummer, p.bezeichnung, p.rechtsgrundlage,
               sk.code, sk.bezeichnung AS sk_bez, sk.beschreibung AS sk_desc,
               t.nummer AS tp_nr, t.bezeichnung AS tp_bez,
               (SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h
                JOIN konten k ON h.konto_id=k.id
                JOIN kontenklassen kk ON k.kontenklasse_id=kk.id
                WHERE h.produkt_id=p.id AND h.daten_jahr=2025
                  AND h.wert_typ='PLAN_ANSATZ' AND kk.nummer=5) AS kk5,
               (SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h
                JOIN konten k ON h.konto_id=k.id
                JOIN kontenklassen kk ON k.kontenklasse_id=kk.id
                WHERE h.produkt_id=p.id AND h.daten_jahr=2024
                  AND h.wert_typ='PLAN_ANSATZ' AND kk.nummer=5) AS kk5_2024,
               (SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h
                JOIN konten k ON h.konto_id=k.id
                JOIN kontenklassen kk ON k.kontenklasse_id=kk.id
                WHERE h.produkt_id=p.id AND h.daten_jahr=2023
                  AND h.wert_typ='PLAN_ANSATZ' AND kk.nummer=5) AS kk5_2023
        FROM produkte p
        JOIN steuerungs_kategorien sk ON p.steuerungs_kategorie_id=sk.id
        JOIN teilplaene t ON p.teilplan_id=t.id
        ORDER BY kk5 DESC, p.produkt_nummer
    """):
        sim.append({
            "produkt_nummer":        r["produkt_nummer"],
            "bezeichnung":           PRODUKT_NAMEN.get(r["produkt_nummer"], r["bezeichnung"]),
            "rechtsgrundlage":       r["rechtsgrundlage"],
            "steuerungs_code":       r["code"],
            "steuerungs_bezeichnung": r["sk_bez"],
            "steuerungs_beschreibung": r["sk_desc"],
            "max_kuerzung_pct":      max_kuerz.get(r["code"], 0),
            "tp_nr":                 r["tp_nr"],
            "tp_name":               TP_NAMEN_SCHOEN.get(r["tp_nr"], r["tp_bez"]),
            "kk5_2025":              round(r["kk5"], 2),
            "kk5_2024":              round(r["kk5_2024"], 2),
            "kk5_2023":              round(r["kk5_2023"], 2),
        })
    result["simulator_produkte"] = sim

    # ── Gesetze-Katalog ───────────────────────────────────────────────────────
    gesetze = []
    for r in con.execute(
        "SELECT kuerzel, vollname, rechtsebene, fundstelle, kernaussage FROM gesetze_katalog ORDER BY rechtsebene, kuerzel"
    ):
        gesetze.append({
            "kuerzel":     r["kuerzel"],
            "vollname":    r["vollname"],
            "rechtsebene": r["rechtsebene"],
            "fundstelle":  r["fundstelle"],
            "kernaussage": r["kernaussage"],
        })
    result["gesetze_katalog"] = gesetze

    # ── Steuerungs-Kategorien mit Rechtsgrundlage ──────────────────────────────
    sk_list = []
    for r in con.execute(
        "SELECT code, bezeichnung, beschreibung, rechtsgrundlage FROM steuerungs_kategorien ORDER BY code"
    ):
        sk_list.append({
            "code":          r["code"],
            "bezeichnung":   r["bezeichnung"],
            "beschreibung":  r["beschreibung"],
            "rechtsgrundlage": r["rechtsgrundlage"],
        })
    result["steuerungs_kategorien"] = sk_list

    # ── Wechselwirkungen ──────────────────────────────────────────────────────
    result["wechselwirkungen"] = [
        {
            "id": "praevention_kosten_spirale",
            "trigger_produkte": ["362000","362010","362020","362030","362040","362080","362090"],
            "trigger_schwelle_pct": 20,
            "ziel_produkt": "363000",
            "risiko_aufschlag_pct": 5,
            "beschreibung": (
                "Präventions-Kosten-Spirale: Kürzungen der freiwilligen Jugendarbeit "
                "um >20 % erhöhen das statistische Risiko steigender Fallzahlen "
                "bei Hilfen zur Erziehung (HzE) nach SGB VIII §§27."
            ),
        }
    ]

    # ── HSK bereits hier als Funktion (wird später in result geschrieben) ────
    # (make_hsk defined below main, called after all other sections)

    # ── Details-Drill-Down (TP → Produkte → Konten) ──────────────────────────
    result["details_tp"] = make_details_tp(con)

    # ── Personal-Tab ──────────────────────────────────────────────────────────
    result["personal"] = make_personal(con)

    # ── Stellenplan ───────────────────────────────────────────────────────────
    sp = make_stellenplan(con)
    if sp:
        result["personal"]["stellenplan"] = sp

    # ── HSK-Maßnahmen ─────────────────────────────────────────────────────────
    result["hsk"] = make_hsk(con)

    # ── Bilanz + EB KDS ───────────────────────────────────────────────────────
    result["bilanz"] = make_bilanz(con)
    result["eb_kds"] = make_eb_kds(con)

    # ── Beteiligungen ─────────────────────────────────────────────────────────
    result["beteiligungen"] = make_beteiligungen(con)

    # ── Investitionen & Substanzerhalt ────────────────────────────────────────
    result["investitionen"] = make_investitionen(con)

    # ── Schuldenentwicklung ───────────────────────────────────────────────────
    result["schulden"] = make_schulden(con)

    # ── Zweckverbände ─────────────────────────────────────────────────────────
    result["zweckverbände"] = make_zweckverbände(con)

    # ── Ausgabe ───────────────────────────────────────────────────────────────
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(OUT_PATH) // 1024
    print(f"[OK] {OUT_PATH}  ({size_kb} KB)")
    dtl_total = sum(len(tp["produkte"]) for tp in result["details_tp"].values())
    for k, v in [
        ("Zeitreihe",          len(result["zeitreihe"])),
        ("Teilplaene 2025",    len(by_year["2025"]["teilplaene"])),
        ("Teilplaene 2024",    len(by_year["2024"]["teilplaene"])),
        ("Ertragsquellen",     len(result["ertragsquellen"])),
        ("Simulator-Produkte", len(sim)),
        ("Details-Produkte",   dtl_total),
        ("Personal-Gruppen",   len(result["personal"]["gruppen_labels"])),
        ("Stellenplan-Keys",   len(result["personal"].get("stellenplan", {}).get("by_year", {}))),
        ("HSK-Massnahmen",     len(result.get("hsk", {}).get("massnahmen", []))),
        ("Beteiligungen",      len((result.get("beteiligungen") or {}).get("entities", []))),
        ("Finanzstroeme 2024", len((result.get("beteiligungen") or {}).get("stroeme", {}).get("2024", []))),
        ("Investitionen",      len(result.get("investitionen") or [])),
        ("Schulden",           len(result.get("schulden") or [])),
        ("Zweckverbände",      len(result.get("zweckverbände") or [])),
    ]:
        print(f"     {k+':':25s} {v}")
    for yr in [2023, 2024, 2025]:
        m = by_year[str(yr)]["meta"]
        gt = GT_BY_YEAR[yr]
        print(f"     {f'ETL KK4 {yr}:':25s} {m['ertraege_etl']:>15,.2f}  (GT {gt['ertraege']:>15,.2f})")
        print(f"     {f'ETL KK5 {yr}:':25s} {m['aufwendungen_etl']:>15,.2f}  (GT {gt['aufwendungen']:>15,.2f})")
        gt_kk6 = f"GT {gt['einzahlungen']:>15,.2f}" if 'einzahlungen' in gt else "kein GT"
        gt_kk7 = f"GT {gt['auszahlungen']:>15,.2f}" if 'auszahlungen' in gt else "kein GT"
        print(f"     {f'ETL KK6 {yr}:':25s} {m['einzahlungen_etl']:>15,.2f}  ({gt_kk6})")
        print(f"     {f'ETL KK7 {yr}:':25s} {m['auszahlungen_etl']:>15,.2f}  ({gt_kk7})")


def make_hsk(con) -> dict:
    """
    Exportiert HSK-Maßnahmen für das Dashboard.
    Gibt None zurück, wenn die Tabellen noch nicht existieren oder leer sind.
    """
    try:
        count = con.execute("SELECT COUNT(*) FROM hsk_massnahmen").fetchone()[0]
        if count == 0:
            return None
    except Exception:
        return None

    YEARS = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

    # Jahreswerte pro Maßnahme
    jahreswerte_map: dict[int, dict[int, float]] = {}
    for r in con.execute("SELECT massnahme_id, jahr, umgesetzter_betrag FROM hsk_jahreswerte"):
        jahreswerte_map.setdefault(r[0], {})[r[1]] = r[2]

    # Abgleich-Daten aus VIEW hsk_abgleich
    abgleich_map: dict[int, dict] = {}
    try:
        for r in con.execute("""
            SELECT massnahme_id, produkt_nummer, produkt_bez, tp_nr, tp_bez,
                   jahr, hsk_ziel, haushalt_kk4, haushalt_kk5
            FROM hsk_abgleich
        """):
            mid, prod, pbez, tp_nr, tp_bez, jahr, hsk_z, kk4, kk5 = r
            pd = abgleich_map.setdefault(mid, {}).setdefault(prod, {
                "bezeichnung": pbez or "",
                "tp_nr": tp_nr or "",
                "tp_bez": tp_bez or "",
                "jahre": {},
            })
            pd["jahre"][str(jahr)] = {
                "hsk_ziel": round(hsk_z or 0),
                "kk4": round(kk4 or 0),
                "kk5": round(kk5 or 0),
                "wert_typ": "IST" if jahr <= 2023 else "PLAN",
            }
    except Exception:
        pass  # VIEW noch nicht vorhanden

    massnahmen = []
    for m in con.execute("""
        SELECT id, nr, bezeichnung, produkte, verantwortlich, rechtsform,
               betrag_kumulativ, betrag_2023, betrag_2024, betrag_2025,
               betrag_gesamt, umsetzungsstatus, kategorie, beschreibung
        FROM hsk_massnahmen ORDER BY CAST(nr AS INTEGER), nr
    """):
        jw = jahreswerte_map.get(m[0], {})
        ab = abgleich_map.get(m[0], {})
        wirksam_ab = min((y for y, v in jw.items() if v != 0), default=None)
        # Primärer TP aus abgleich ableiten (erster Eintrag mit tp_nr)
        primary_tp = next((pd["tp_nr"] for pd in ab.values() if pd.get("tp_nr")), None)

        # Tendenz: bewegt sich Haushalt in Richtung HSK-Ziel?
        tendenz = None
        if ab:
            kat = m[12]
            for pd in ab.values():
                j = pd["jahre"]
                v23 = j.get("2023", {})
                v25 = j.get("2025", {})
                if not v23 or not v25:
                    continue
                if kat == "ERTRAG":
                    tendenz = "positiv" if v25["kk4"] > v23["kk4"] else "negativ"
                else:
                    tendenz = "positiv" if v25["kk5"] < v23["kk5"] else "negativ"
                break

        massnahmen.append({
            "id":          m[0],
            "nr":          m[1],
            "bezeichnung": m[2],
            "produkte":    [p.strip() for p in (m[3] or "").split(",") if p.strip()],
            "verantwortlich": m[4],
            "rechtsform":  m[5],
            "betrag_kumulativ": round(m[6] or 0),
            "betrag_2023":      round(m[7] or 0),
            "betrag_2024":      round(m[8] or 0),
            "betrag_2025":      round(m[9] or 0),
            "betrag_gesamt":    round(m[10] or 0),
            "status":      m[11],
            "kategorie":   m[12],
            "beschreibung": m[13] or "",
            "jahreswerte": {str(y): round(jw.get(y, 0)) for y in YEARS},
            "wirksam_ab":  wirksam_ab,
            "tp_nr":       primary_tp,
            "abgleich":    ab,
            "tendenz":     tendenz,
        })

    # Meta-Kennzahlen
    tot = con.execute("""
        SELECT
          SUM(CASE WHEN umsetzungsstatus='aktiv' THEN 1 ELSE 0 END) AS n_aktiv,
          SUM(CASE WHEN umsetzungsstatus='erledigt' THEN 1 ELSE 0 END) AS n_erledigt,
          SUM(CASE WHEN umsetzungsstatus='entfallen' THEN 1 ELSE 0 END) AS n_entfallen,
          SUM(betrag_kumulativ) AS gesamt_kumulativ,
          SUM(betrag_2024) AS gesamt_2024,
          SUM(betrag_2025) AS gesamt_2025,
          SUM(betrag_gesamt) AS gesamt_total
        FROM hsk_massnahmen
    """).fetchone()

    # Kumulativverlauf je Jahr (für Timeline-Chart)
    kumulativ_timeline = {}
    for r in con.execute("""
        SELECT j.jahr, SUM(j.umgesetzter_betrag) AS summe
        FROM hsk_jahreswerte j
        GROUP BY j.jahr ORDER BY j.jahr
    """):
        kumulativ_timeline[str(r[0])] = round(r[1] or 0)

    return {
        "meta": {
            "fortschreibung": 9,
            "beschluss_datum": "2023-09-07",
            "n_massnahmen": count,
            "n_aktiv": tot[0] or 0,
            "n_erledigt": tot[1] or 0,
            "n_entfallen": tot[2] or 0,
            "gesamt_kumulativ_2013_2022": round(tot[3] or 0),
            "gesamt_2024": round(tot[4] or 0),
            "gesamt_2025": round(tot[5] or 0),
            "gesamt_total": round(tot[6] or 0),
            "n_mit_abgleich": sum(1 for m in massnahmen if m["abgleich"]),
            "n_tendenz_positiv": sum(1 for m in massnahmen if m["tendenz"] == "positiv"),
            "n_tendenz_negativ": sum(1 for m in massnahmen if m["tendenz"] == "negativ"),
        },
        "kumulativ_timeline": kumulativ_timeline,
        "massnahmen": massnahmen,
    }


def make_bilanz(con) -> dict | None:
    """Exportiert Bilanz-Positionen (Stadt Suhl) für den Vermögen-Tab."""
    try:
        count = con.execute("SELECT COUNT(*) FROM bilanz_positionen").fetchone()[0]
    except Exception:
        return None
    if count == 0:
        return None

    jahre = sorted({r[0] for r in con.execute(
        "SELECT DISTINCT daten_jahr FROM bilanz_positionen")})
    by_year = {}
    for yr in jahre:
        aktiva, passiva = [], []
        for r in con.execute("""
            SELECT position_code, bezeichnung, ebene, betrag, seite
            FROM bilanz_positionen WHERE daten_jahr = ?
            ORDER BY seite, position_code
        """, (yr,)):
            entry = {"code": r["position_code"], "bez": r["bezeichnung"],
                     "ebene": r["ebene"], "betrag": round(r["betrag"], 2)}
            (aktiva if r["seite"] == "AKTIVA" else passiva).append(entry)
        by_year[str(yr)] = {"aktiva": aktiva, "passiva": passiva}

    entwicklung = {
        "bilanzsumme_2021_teur": 279_459,
        "veraenderung_seit_2013_teur": 38_365,
        "quelle_seite": 153,
        "aktivseite": [
            {"position": "Immaterielle VG", "code": "A1.1", "delta_teur": 3_867,
             "anmerkung": "Anstieg immaterieller VG (Konzessionen, Zuwendungen)"},
            {"position": "Sachanlagen", "code": "A1.2", "delta_teur": 16_318,
             "davon_eingemeindung_teur": 16_959,
             "anmerkung": "Eingemeindung +16.959 T€; saldiert Werteverzehr beim Sachanlagevermögen"},
            {"position": "Finanzanlagevermögen", "code": "A1.3", "delta_teur": 3_873,
             "davon_eingemeindung_teur": 2_220, "davon_eb_kds_ek_teur": 1_037,
             "anmerkung": "Eingemeindung +2.220 T€, EB KDS Eigenkapitalerhöhung +1.037 T€"},
            {"position": "Kassenbestand", "code": "A2.4", "delta_teur": 10_153,
             "anmerkung": "Verbliebene Mittel aus Verkauf der E.ON-Aktien"},
        ],
        "passivseite": [
            {"position": "Allgemeine Rücklage", "code": "P1.1", "delta_teur": 3_280,
             "davon_eingemeindung_teur": 7_303,
             "anmerkung": "Eingemeindung +7.303 T€, saldiert mit Korrekturen Eröffnungsbilanz"},
            {"position": "Jahresergebnis + Ergebnisvortrag", "code": "P1.4+P1.5",
             "delta_teur": 78_371,
             "anmerkung": "Positive Jahresergebnisse; Großteil aus E.ON-Aktienverkauf"},
            {"position": "Sonderposten", "code": "P2", "delta_teur": 17_714,
             "davon_eingemeindung_teur": 9_829,
             "anmerkung": "Erhöhung durch Fördermittel und Eingemeindung (+9.829 T€)"},
            {"position": "Investitionskredite", "code": "P4.2", "delta_teur": -58_596,
             "anmerkung": "Schuldenabbau: Rückgang der Investitionskredite um 58,6 Mio €"},
        ]
    }

    return {"jahre": jahre, "by_year": by_year, "entwicklung": entwicklung}


def make_eb_kds(con) -> dict | None:
    """Exportiert EB-KDS-Kennzahlen (Beteiligungsbericht) für den Vermögen-Tab."""
    try:
        count = con.execute("SELECT COUNT(*) FROM eb_kds_kennzahlen").fetchone()[0]
    except Exception:
        return None
    if count == 0:
        return None

    result: dict = {}
    for r in con.execute("""
        SELECT daten_jahr, bereich, position, betrag_teur
        FROM eb_kds_kennzahlen ORDER BY daten_jahr, bereich, position
    """):
        yr = str(r["daten_jahr"])
        b  = r["bereich"]
        if yr not in result:
            result[yr] = {}
        if b not in result[yr]:
            result[yr][b] = {}
        result[yr][b][r["position"]] = r["betrag_teur"]

    return result or None


def make_beteiligungen(con) -> dict | None:
    """Exportiert Beteiligungen + Kennzahlen + Finanzströme für den Beteiligungen-Subtab."""
    try:
        count = con.execute("SELECT COUNT(*) FROM beteiligungen").fetchone()[0]
    except Exception:
        return None
    if count == 0:
        return None

    # Stammdaten
    entities = []
    for r in con.execute("""
        SELECT id, kuerzel, name, typ, beteiligung_direkt, beteiligung_indirekt,
               via_kuerzel, stammkapital_eur, gruendungsjahr, sektor, status,
               oeffentlicher_zweck
        FROM beteiligungen ORDER BY id
    """):
        entities.append({
            "id":                  r["id"],
            "kuerzel":             r["kuerzel"],
            "name":                r["name"],
            "typ":                 r["typ"],
            "beteiligung_direkt":  r["beteiligung_direkt"],
            "beteiligung_indirekt": r["beteiligung_indirekt"],
            "via":                 r["via_kuerzel"],
            "stammkapital_eur":    r["stammkapital_eur"],
            "gruendungsjahr":      r["gruendungsjahr"],
            "sektor":              r["sektor"],
            "status":              r["status"],
            "zweck":               r["oeffentlicher_zweck"],
        })

    # Kennzahlen je Beteiligung × Jahr
    kennzahlen: dict[str, dict[str, dict]] = {}
    for r in con.execute("""
        SELECT b.kuerzel, bk.jahr,
               bk.umsatz_teur, bk.jahresergebnis_teur, bk.jahresergebnis_nach_eav_teur,
               bk.bilanzsumme_teur, bk.eigenkapital_teur, bk.verbindlichkeiten_teur,
               bk.investitionen_teur, bk.mitarbeiter
        FROM beteiligungen_kennzahlen bk
        JOIN beteiligungen b ON bk.beteiligung_id = b.id
        ORDER BY b.kuerzel, bk.jahr
    """):
        kuerzel = r["kuerzel"]
        if kuerzel not in kennzahlen:
            kennzahlen[kuerzel] = {}
        ek = r["eigenkapital_teur"]
        bs = r["bilanzsumme_teur"]
        kennzahlen[kuerzel][str(r["jahr"])] = {
            "umsatz":     r["umsatz_teur"],
            "je":         r["jahresergebnis_teur"],
            "je_eav":     r["jahresergebnis_nach_eav_teur"],
            "bilanzsumme": bs,
            "eigenkapital": ek,
            "verbindlichkeiten": r["verbindlichkeiten_teur"],
            "investitionen": r["investitionen_teur"],
            "mitarbeiter":  r["mitarbeiter"],
            "ek_quote":     round(ek / bs * 100, 1) if bs and bs > 0 else None,
        }

    # Finanzströme je Jahr
    stroeme: dict[str, list] = {}
    for r in con.execute("""
        SELECT jahr, von_kuerzel, nach_kuerzel, betrag_teur, typ, bezeichnung
        FROM finanzstroeme ORDER BY jahr, typ, betrag_teur DESC
    """):
        yr = str(r["jahr"])
        if yr not in stroeme:
            stroeme[yr] = []
        stroeme[yr].append({
            "von":      r["von_kuerzel"],
            "nach":     r["nach_kuerzel"],
            "betrag":   r["betrag_teur"],
            "typ":      r["typ"],
            "bez":      r["bezeichnung"],
        })

    return {
        "entities":   entities,
        "kennzahlen": kennzahlen,
        "stroeme":    stroeme,
    }


def make_investitionen(con) -> list:
    """Abschreibungen (AfA, Konten 53xx) vs. Investitions-Auszahlungen (KK7 Konten 78xx) je Jahr."""
    YEARS = [
        (2021, "IST_ERGEBNIS", "Ist 2021",  False),
        (2022, "IST_ERGEBNIS", "Ist 2022",  False),
        (2023, "IST_ERGEBNIS", "Ist 2023",  False),
        (2024, "PLAN_ANSATZ",  "Plan 2024", False),
        (2025, "PLAN_ANSATZ",  "Plan 2025", False),
    ]
    result = []
    for jahr, wert_typ, label, ist_prognose in YEARS:
        afa = con.execute(
            "SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h "
            "JOIN konten k ON h.konto_id=k.id "
            "WHERE k.konto_nummer LIKE '53%' AND h.daten_jahr=? AND h.wert_typ=?",
            (jahr, wert_typ)
        ).fetchone()[0]
        invest = con.execute(
            "SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h "
            "JOIN konten k ON h.konto_id=k.id "
            "WHERE k.konto_nummer LIKE '78%' AND h.daten_jahr=? AND h.wert_typ=?",
            (jahr, wert_typ)
        ).fetchone()[0]
        afa_t    = round(afa    / 1000)
        invest_t = round(invest / 1000)
        quote = round(invest_t / afa_t * 100, 1) if afa_t > 0 and invest_t > 0 else None
        result.append({
            "jahr":         jahr,
            "label":        label,
            "ist_prognose": ist_prognose,
            "afa_teur":     afa_t,
            "invest_teur":  invest_t if invest_t > 0 else None,
            "quote":        quote,
        })
    return result


def make_zweckverbände(con) -> list:
    rows = con.execute(
        "SELECT nr, kuerzel, name, kategorie, adresse, anmerkung "
        "FROM zweckverbände ORDER BY nr"
    ).fetchall()
    return [
        {
            "nr":        r[0],
            "kuerzel":   r[1],
            "name":      r[2],
            "kategorie": r[3],
            "adresse":   r[4],
            "anmerkung": r[5],
        }
        for r in rows
    ]


def make_schulden(con) -> list:
    rows = con.execute(
        "SELECT jahr, schuldenstand_teur, einwohner, prokopf_eur, ist_prognose "
        "FROM schulden_entwicklung ORDER BY jahr"
    ).fetchall()
    return [
        {
            "jahr": r[0],
            "schuldenstand_teur": r[1],
            "einwohner": r[2],
            "prokopf_eur": r[3],
            "ist_prognose": bool(r[4]),
        }
        for r in rows
    ]


if __name__ == "__main__":
    main()
