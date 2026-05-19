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
    2024: {"ertraege": 130_353_020.00, "aufwendungen": 133_802_080.00, "ergebnis": -3_449_060.00},
    2025: {"ertraege": 136_395_290.00, "aufwendungen": 138_003_230.00, "ergebnis": -1_607_940.00},
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
    return con.execute("""
        SELECT COALESCE(SUM(h.betrag),0) FROM haushaltswerte h
        JOIN konten k ON h.konto_id=k.id
        JOIN kontenklassen kk ON k.kontenklasse_id=kk.id
        WHERE h.daten_jahr=? AND h.wert_typ=? AND kk.nummer=?
    """, (jahr, typ, kk_nr)).fetchone()[0]


def make_meta(con, jahr):
    gt = GT_BY_YEAR[jahr]
    return {
        "titel":               f"Haushaltsplan Stadt Suhl {jahr}",
        "ertraege_soll":       gt["ertraege"],
        "aufwendungen_soll":   gt["aufwendungen"],
        "jahresergebnis_soll": gt["ergebnis"],
        "ertraege_etl":        round(kk_sum_y(con, 4, jahr, "PLAN_ANSATZ"), 2),
        "aufwendungen_etl":    round(kk_sum_y(con, 5, jahr, "PLAN_ANSATZ"), 2),
        "generiert_am":        datetime.now().isoformat(),
    }


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


def main():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    result = {}

    # ── by_year: pro Jahr meta + teilplaene + ertragsquellen ─────────────────
    by_year = {}
    for yr in [2024, 2025]:
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

    # ── Zeitreihe (IST 2022 aus 2024-ETL + 2025-ETL-Sicht)
    jahre_zt = [
        (2022, "IST_ERGEBNIS",   "Ist 2022",     False),
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
                  AND h.wert_typ='PLAN_ANSATZ' AND kk.nummer=5) AS kk5_2024
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

    # ── Ausgabe ───────────────────────────────────────────────────────────────
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(OUT_PATH) // 1024
    print(f"[OK] {OUT_PATH}  ({size_kb} KB)")
    for k, v in [
        ("Zeitreihe",          len(result["zeitreihe"])),
        ("Teilplaene 2025",    len(by_year["2025"]["teilplaene"])),
        ("Teilplaene 2024",    len(by_year["2024"]["teilplaene"])),
        ("Ertragsquellen",     len(result["ertragsquellen"])),
        ("Simulator-Produkte", len(sim)),
    ]:
        print(f"     {k+':':25s} {v}")
    for yr in [2024, 2025]:
        m = by_year[str(yr)]["meta"]
        print(f"     {f'ETL KK4 {yr}:':25s} {m['ertraege_etl']:>15,.2f}  (GT {GT_BY_YEAR[yr]['ertraege']:>15,.2f})")
        print(f"     {f'ETL KK5 {yr}:':25s} {m['aufwendungen_etl']:>15,.2f}  (GT {GT_BY_YEAR[yr]['aufwendungen']:>15,.2f})")


if __name__ == "__main__":
    main()
