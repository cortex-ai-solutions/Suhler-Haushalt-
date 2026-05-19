"""
Kategorisierung aller unkategorisierten Produkte.
Basis: Thüringer Produktrahmen + Wissensdateien (haushalt_sozialrechtliche_details.md)

SK-IDs: 1=FREIWILLIG, 2=PFLICHT_ERMESSEN, 3=PFLICHT_STRIKT, 4=UEBERTRAGEN
"""
import sqlite3

# SK_ID -> Code Mapping zur Lesbarkeit
SK = {"F": 1, "E": 2, "S": 3, "U": 4}

# Produktnummer -> (sk_typ, kurze Begründung)
# Methodisch: erste 3-4 Ziffern = Produktgruppe laut Thüringer Produktrahmen
KATEGORIEN = {
    # ─── TP01 Verwaltungsführung ─────────────────────────────────────────────
    # 51xxxx im TP01-Kontext = interne Verwaltungsquerschnittsprodukte (Personal/IT-nahe)
    "511100": ("E", "Zentrale Verwaltungsdienstleistung, ThürKO § 2"),
    "511200": ("E", "Zentrale Verwaltungsdienstleistung, ThürKO § 2"),
    "571000": ("E", "Interne Verwaltung, ThürKO § 2"),
    "536000": ("E", "Interne Verwaltung, ThürKO § 2"),
    "111160": ("E", "Stadtrat/politische Gremien, ThürKO §§ 21 ff."),
    "111100": ("E", "Stadtrat/politische Gremien, ThürKO §§ 21 ff."),

    # ─── TP02 Kultur, Tourismus und Sport ───────────────────────────────────
    # 4244xx = Sportanlagen, 4243xx = Bäder, 4241xx = Sportförderung = FREIWILLIG
    # 252xxx = Museen = FREIWILLIG; 575xxx = Stadtgrün = FREIWILLIG
    "424400": ("F", "Sportstätten/-förderung, freiwillige Selbstverwaltungsaufgabe"),
    "424240": ("F", "Sportförderung, freiwillig"),
    "424300": ("F", "Sportförderung (Bäder), freiwillig"),
    "424220": ("F", "Sportförderung, freiwillig"),
    "424230": ("F", "Sportförderung, freiwillig"),
    "424100": ("F", "Sportförderung, freiwillig"),
    "421000": ("F", "Theater/Musik, freiwillig"),
    "252110": ("F", "Museum/Ausstellung, freiwillig"),
    "252120": ("F", "Museum/Ausstellung, freiwillig"),
    "573300": ("F", "Grünanlagen/Sport-Infrastruktur, freiwillig"),
    "575030": ("F", "Stadtpark/Grünflächen, freiwillig"),
    "575040": ("F", "Stadtpark/Grünflächen, freiwillig"),
    "575050": ("F", "Stadtpark/Grünflächen, freiwillig"),
    "575060": ("F", "Stadtpark/Grünflächen, freiwillig"),
    "546100": ("F", "Stadtmarketing/Tourismus, freiwillig"),

    # ─── TP03 Personal / Zentrale Dienste ───────────────────────────────────
    # 1141xx/1142xx = Zentrale Dienste; 1121xx/1122xx = Personal/Organisation
    # 573xxx in TP03 = Gebäudeunterhaltung intern; 546xxx = Beschaffung
    "114110": ("E", "Zentrale Dienstleistungen, ThürKO § 2"),
    "114200": ("E", "Zentrale Dienstleistungen, ThürKO § 2"),
    "114400": ("E", "Zentrale Dienstleistungen, ThürKO § 2"),
    "114520": ("E", "Zentrale Dienstleistungen, ThürKO § 2"),
    "112100": ("E", "Personal/Organisation, ThürKO § 5 ThürGemHV-Doppik"),
    "112110": ("E", "Personal/Organisation, ThürKO § 5"),
    "112120": ("E", "Personal/Organisation, ThürKO § 5"),
    "112200": ("E", "Personal/Organisation, ThürKO § 5"),
    "573110": ("E", "Gebäudemanagement intern, ThürKO § 2"),
    "573130": ("E", "Gebäudemanagement intern, ThürKO § 2"),
    "573140": ("E", "Gebäudemanagement intern, ThürKO § 2"),
    "546000": ("E", "Zentrale Beschaffung, ThürKO § 2"),
    "252300": ("E", "Archivwesen, ThürArchivG"),

    # ─── TP04 Finanzverwaltung ───────────────────────────────────────────────
    # 547xxx = Finanzwirtschaft/Kassenwesen; 535xxx = Haushaltswirtschaft
    "547000": ("E", "Finanzverwaltung/Kassenwesen, ThürGemHV-Doppik"),
    "535000": ("E", "Haushaltswirtschaft, ThürGemHV-Doppik"),

    # ─── TP05 Öffentliche Flächen und Straßen ───────────────────────────────
    # 543xxx = Gemeindestraßen; 542xxx = Kreisstraßen; 366xxx hier fehlgeordnet
    "543010": ("E", "Gemeindestraßen, ThürStrG"),
    "543070": ("E", "Gemeindestraßen/Wege, ThürStrG"),
    "542010": ("E", "Straßenunterhaltung, ThürStrG"),
    "366300": ("E", "Gemeindestraßen/Wege (TP05-Kontext), ThürStrG"),

    # ─── TP06 Allgemeine Finanzwirtschaft ───────────────────────────────────
    # 611xxx = Steuern/Allgemeine Deckungsmittel → gesetzlich geregelt = PFLICHT_STRIKT
    # 612xxx = Allgemeine Zuweisungen (ThürFAG) = PFLICHT_STRIKT
    # 625xxx = Kreditaufnahme/Zinsdienst = PFLICHT_STRIKT (Schuldendienst gesetzl. vorrangig)
    "611000": ("S", "Steuern/Allg. Deckungsmittel, §§ 1 ff. KAG TH, ThürFAG"),
    "612000": ("S", "Allg. Schlüsselzuweisungen, § 7 ThürFAG"),
    "625000": ("S", "Kreditdienst/Finanzierungskosten, § 75 ThürKO"),

    # ─── TP07 Ordnung und Sicherheit ────────────────────────────────────────
    # 1221xx/1222xx/1223xx = Ordnungsamt/Gewerberecht = PFLICHT_STRIKT
    # 1231xx = Feuerwehr; 1233xx = Rettungsdienst; 1234xx = Brandschutz = PFLICHT_STRIKT
    # 1212xx = Standesamt = PFLICHT_STRIKT; 1270xx = Bevölkerungsschutz = PFLICHT_STRIKT
    "122100": ("S", "Ordnungsamt, ThürOBG"),
    "122200": ("S", "Ordnungsamt/Gewerbeaufsicht, GewO, ThürOBG"),
    "122310": ("S", "Gewerberecht, GewO"),
    "122320": ("S", "Gewerberecht, GewO"),
    "122400": ("E", "Sonstige Ordnungsangelegenheiten, ThürOBG"),
    "122500": ("E", "Sonstige Ordnungsangelegenheiten (TP09-Kontext)"),
    "123100": ("S", "Feuerwehr, ThürBKG § 2"),
    "123300": ("S", "Rettungsdienst, ThürRettG"),
    "123400": ("S", "Brand-/Katastrophenschutz, ThürBKG"),
    "121220": ("S", "Standesamt, PStG"),
    "119000": ("E", "Allgemeine Verwaltung Ordnungsbereich, ThürKO § 2"),
    "127000": ("S", "Bevölkerungsschutz/Zivilschutz, ThürBKG"),
    "128000": ("S", "Einwohnerwesen/Meldewesen, BMG"),
    "573200": ("E", "Fahrzeug-/Gebäudeunterhalt Ordnungsbereich (intern)"),

    # ─── TP08 Umwelt ─────────────────────────────────────────────────────────
    # 537xxx = Abfallwirtschaft → Pflicht (KrWG, ThürAbfG) = PFLICHT_STRIKT
    # 554xxx = Gewässerpflege → PFLICHT_ERMESSEN (Kooperationspflicht Bund/Land)
    # 555xxx = Naturschutz → PFLICHT_ERMESSEN; 521xxx = Straßen/Infrastruktur
    # 545xxx = Friedhof = PFLICHT_ERMESSEN; 124xxx in TP08 = Veterinär → PFLICHT_STRIKT
    "537010": ("S", "Abfallwirtschaft, KrWG, ThürAbfG"),
    "537020": ("S", "Abfallwirtschaft, KrWG, ThürAbfG"),
    "537040": ("S", "Abfallwirtschaft, KrWG, ThürAbfG"),
    "555000": ("E", "Naturschutz/Landschaftspflege, ThürNatSchG"),
    "554000": ("E", "Gewässerpflege, WHG, ThürWG"),
    "554100": ("E", "Gewässerpflege/Hochwasserschutz, WHG, ThürWG"),
    "545110": ("E", "Friedhöfe, ThürBestG"),
    "521000": ("E", "Straßen-/Wegeunterhalt (Umweltbereich), ThürStrG"),
    "253000": ("E", "Stadtentwicklung/Umweltplanung (TP08-Kontext)"),
    "124200": ("S", "Veterinärwesen/Lebensmittelüberwachung, LFGB, ThürVet"),
    "551100": ("E", "Sonstiger Umweltschutz, ThürNatSchG"),

    # ─── TP09 Soziales und Gesundheit ───────────────────────────────────────
    # Fast alle SGB-gebunden = PFLICHT_STRIKT
    # 311xxx = SGB II/XII Leistungen; 312xxx = SGB XII; 313xxx = Hilfe zur Pflege
    # 314xxx = Sonstige SGB XII; 315xxx/316xxx = Weitere SGB XII/IX Leistungen
    # 345xxx = Asylbewerberleistungsgesetz; 348xxx = Flüchtlinge
    # 351xxx = Gesundheitsamt; 331xxx = Soziale Beratungsdienste
    # 414xxx in TP09 = Gesundheitsförderung
    "311110": ("S", "Hilfe zum Lebensunterhalt, SGB XII § 27"),
    "311120": ("S", "Hilfe zum Lebensunterhalt, SGB XII § 27"),
    "311200": ("S", "Grundsicherung im Alter, SGB XII §§ 41 ff."),
    "311290": ("S", "Grundsicherung/Sonstige SGB XII-Leistungen"),
    "311400": ("S", "SGB XII-Leistungen"),
    "311610": ("S", "Eingliederungshilfe SGB IX, §§ 90 u. 112 SGB IX"),
    "311620": ("S", "Eingliederungshilfe SGB IX, §§ 90 u. 112 SGB IX"),
    "311630": ("S", "Eingliederungshilfe SGB IX, §§ 90 u. 112 SGB IX"),
    "311800": ("S", "SGB XII-Leistungen/Sonstige Sozialhilfe"),
    "312100": ("S", "KdU SGB XII, §§ 35 u. 42 SGB XII"),
    "312200": ("S", "KdU SGB XII, §§ 35 u. 42 SGB XII"),
    "313000": ("S", "Hilfe zur Pflege, SGB XII §§ 61 ff."),
    "314000": ("S", "Sonstige Hilfen SGB XII (Blindengeld/Landespflege)"),
    "315410": ("S", "SGB XII-Leistungen §§ 47 ff."),
    "315500": ("S", "SGB XII-Leistungen"),
    "315600": ("S", "SGB XII-Leistungen"),
    "316400": ("S", "Eingliederungshilfe/Teilhabe, SGB IX"),
    "316500": ("S", "Eingliederungshilfe/Teilhabe, SGB IX"),
    "331000": ("E", "Soziale Beratungsdienste, § 11 SGB XII (Gewährleistungspflicht)"),
    "345000": ("S", "Asylbewerberleistungen, AsylbLG"),
    "348000": ("S", "Flüchtlingsunterbringung/-betreuung, AsylbLG, ThürFlüAG"),
    "351400": ("S", "Gesundheitsamt/Amtsärztl. Dienst, ThürGDG"),
    "351700": ("S", "Gesundheitsamt/Öffentl. Gesundheitsdienst, ThürGDG"),
    "414000": ("E", "Gesundheitsförderung/Prävention, ThürGDG (Ermessen)"),
    "124100": ("S", "Veterinärwesen/Lebensmittelüberwachung, LFGB"),

    # ─── TP10 Schulträgeraufgaben ────────────────────────────────────────────
    # Schulträgerschaft = Pflichtaufgabe, aber Ausgestaltung mit Ermessen
    "211100": ("E", "Grundschulen Schulträger, ThürSchulG § 40"),
    "211200": ("E", "Gemeinschaftsschulen Schulträger, ThürSchulG"),
    "211300": ("E", "Regelschulen Schulträger, ThürSchulG"),
    "211400": ("E", "Gymnasien Schulträger, ThürSchulG"),
    "212100": ("E", "Berufsschulen Schulträger, ThürSchulG"),
    "216100": ("E", "Regelschulen Schulträger, ThürSchulG"),
    "221100": ("E", "Förderschulen Schulträger, ThürSchulG § 44"),
    "221200": ("E", "Förderschulen Schulträger, ThürSchulG § 44"),

    # ─── TP11 Kinder-, Jugend- und Familienhilfe ─────────────────────────────
    # HzE-Produkte (363xxx) = PFLICHT_STRIKT (§ 27 ff. SGB VIII, § 36a SGB VIII)
    # Kindertagesbetreuung (365xxx) = PFLICHT_STRIKT (ThürKitaG)
    # Pflegekinderdienst/Adoption (341xxx) = PFLICHT_STRIKT (SGB VIII)
    # Jugendarbeit (361xxx) = PFLICHT_ERMESSEN (§ 11 SGB VIII)
    # Frühe Hilfen (367xxx) = PFLICHT_STRIKT (BKiSchG)
    "341000": ("S", "Pflegekinderdienst/Adoptionsvermittlung, SGB VIII §§ 42a ff."),
    "361000": ("E", "Jugendarbeit, SGB VIII § 11 (Ausgestaltung Ermessen)"),
    "363120": ("S", "HzE ambulant (Erziehungsbeistandschaft), SGB VIII § 30"),
    "363130": ("S", "HzE ambulant (Sozialpädagogische Familienhilfe), SGB VIII § 31"),
    "363210": ("S", "HzE teilstationär (Tagesgruppe), SGB VIII § 32"),
    "363230": ("S", "HzE teilstationär, SGB VIII §§ 32 ff."),
    "363370": ("S", "HzE stationär (Heimunterbringung), SGB VIII § 34"),
    "363380": ("S", "HzE stationär (Vollzeitpflege), SGB VIII § 33"),
    "363420": ("S", "HzE stationär, SGB VIII §§ 34 ff."),
    "363700": ("S", "HzE intensiv (ISE), SGB VIII § 35"),
    "365200": ("S", "Kindertagesbetreuung, ThürKitaG § 7"),
    "365210": ("S", "Kindertagesbetreuung, ThürKitaG § 7"),
    "366400": ("E", "Sonstige Jugendhilfe, SGB VIII § 2 (Ermessen)"),
    "367100": ("S", "Frühe Hilfen/Kinderschutz, BKiSchG § 3"),
    "367500": ("E", "Sonstige Familienunterstützung, SGB VIII (Ermessen)"),

    # ─── TP12 Einrichtungen Sozialdezernat ──────────────────────────────────
    # 263xxx, 272xxx = VHS-nahe Einrichtungen / Bildungseinrichtungen im Sozialdezernat
    "263000": ("E", "Einrichtungen Sozialdezernat (VHS-Kontext), ThürKO § 2"),
    "272000": ("E", "Einrichtungen Sozialdezernat, ThürKO § 2"),
}

def main():
    conn = sqlite3.connect("suhl_haushalt_2025.db")
    cur = conn.cursor()

    updates = 0
    skipped = []
    for pnr, (sk_typ, grund) in KATEGORIEN.items():
        sk_id = SK[sk_typ]
        cur.execute(
            "UPDATE produkte SET steuerungs_kategorie_id=?, rechtsgrundlage=? "
            "WHERE produkt_nummer=? AND steuerungs_kategorie_id IS NULL",
            (sk_id, grund, pnr)
        )
        if cur.rowcount > 0:
            updates += cur.rowcount
        else:
            # Prüfen ob das Produkt überhaupt existiert
            cur.execute("SELECT steuerungs_kategorie_id FROM produkte WHERE produkt_nummer=?", (pnr,))
            row = cur.fetchone()
            if row is None:
                skipped.append(f"NICHT IN DB: {pnr}")
            else:
                skipped.append(f"BEREITS KATEGORISIERT: {pnr} → SK_ID {row[0]}")

    conn.commit()
    print(f"Aktualisiert: {updates} Produkte")
    if skipped:
        print(f"\nübersprungen ({len(skipped)}):")
        for s in skipped:
            print(f"  {s}")

    # Abschlusskontrolle
    cur.execute("""
        SELECT sk.code, COUNT(*) as n, ROUND(SUM(
            CASE WHEN k.kontenklasse_id=5 AND hv.wert_typ='PLAN_ANSATZ' THEN hv.betrag ELSE 0 END
        )/1000000.0, 2) as kk5_mio
        FROM produkte p
        JOIN steuerungs_kategorien sk ON p.steuerungs_kategorie_id = sk.id
        LEFT JOIN haushaltswerte hv ON p.id = hv.produkt_id
        LEFT JOIN konten k ON hv.konto_id = k.id
        WHERE p.produkt_nummer != '000000'
        GROUP BY sk.code
        ORDER BY kk5_mio DESC
    """)
    print("\n=== Nach Kategorisierung (kategorisierte Produkte) ===")
    for r in cur.fetchall():
        print(f"  {r[0]:<20} {r[1]:>3} Produkte  {r[2]:>8.2f} Mio. €")

    cur.execute("""
        SELECT COUNT(*), ROUND(SUM(
            CASE WHEN k.kontenklasse_id=5 AND hv.wert_typ='PLAN_ANSATZ' THEN hv.betrag ELSE 0 END
        )/1000000.0, 2)
        FROM produkte p
        LEFT JOIN haushaltswerte hv ON p.id = hv.produkt_id
        LEFT JOIN konten k ON hv.konto_id = k.id
        WHERE p.steuerungs_kategorie_id IS NULL AND p.produkt_nummer != '000000'
    """)
    r = cur.fetchone()
    print(f"\n  Noch unkategorisiert: {r[0]} Produkte, {r[1]} Mio. €")
    conn.close()

if __name__ == "__main__":
    main()
