"""
pipeline_bilanz.py
Befuellt bilanz_positionen und eb_kds_kennzahlen in suhl_haushalt_2025.db.
Quellen:
  Bilanz (Stadt Suhl): Jahresabschluss 31.12.2021 (Seite 69) + 31.12.2020 als Vorjahreszahlen
  EB KDS:              Beteiligungsbericht 2024, Seiten 33-35 (Angaben in TEUR)
"""
import sqlite3, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "suhl_haushalt_2025.db")


def setup_tables(con):
    con.executescript("""
    CREATE TABLE IF NOT EXISTS bilanz_positionen (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        daten_jahr       INTEGER NOT NULL,
        seite            TEXT    NOT NULL,
        position_code    TEXT    NOT NULL,
        bezeichnung      TEXT    NOT NULL,
        ebene            INTEGER NOT NULL,
        betrag           REAL    NOT NULL,
        UNIQUE(daten_jahr, seite, position_code)
    );

    CREATE TABLE IF NOT EXISTS eb_kds_kennzahlen (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        daten_jahr   INTEGER NOT NULL,
        bereich      TEXT    NOT NULL,
        position     TEXT    NOT NULL,
        betrag_teur  REAL    NOT NULL,
        UNIQUE(daten_jahr, bereich, position)
    );
    """)


# ── Stadt-Suhl-Bilanz (Werte in EUR exakt aus Jahresabschluss) ─────────────
# Quelle: Jahresabschluss 31.12.2021 (2021 = aktuell, 2020 = Vorjahreszahlen)
# Ebenen: 1=Hauptgruppe (A1/A2/A3 bzw. P1-P5), 2=Untergruppe, 3=Detail
BILANZ = {
    2021: {
        "AKTIVA": [
            ("A1",     "Anlagevermögen",                                  1,  257_609_775.55),
            ("A1.1",   "Immaterielle Vermögensgegenstände",               2,    5_073_041.87),
            ("A1.2",   "Sachanlagen",                                     2,  191_312_988.57),
            ("A1.3",   "Finanzanlagevermögen",                            2,   61_223_745.11),
            ("A1.3.1", "Anteile verbundene Unternehmen (u.a. EB KDS)",    3,   48_240_934.65),
            ("A2",     "Umlaufvermögen",                                  1,   20_907_422.32),
            ("A2.1",   "Forderungen & sonstige Vermögensgegenstände",     2,    9_607_037.50),
            ("A2.2",   "Liquide Mittel (Kasse & Bank)",                   2,   10_215_526.82),
            ("A2.3",   "Sonstiges Umlaufvermögen (Vorräte u.a.)",         2,    1_084_858.00),
            ("A3",     "Rechnungsabgrenzungsposten (Aktiva)",             1,      942_264.45),
        ],
        "PASSIVA": [
            ("P1",     "Eigenkapital",                                    1,  150_744_687.18),
            ("P1.1",   "Allgemeine Rücklage",                             2,   72_373_935.76),
            ("P1.2",   "Ergebnisvortrag",                                 2,   81_456_466.81),
            ("P1.3",   "Jahresergebnis",                                  2,   -3_085_715.39),
            ("P2",     "Sonderposten (Zuwendungen & Ausgleichsabgaben)",  1,   89_921_644.67),
            ("P2.1",   "Sonderposten aus Zuwendungen",                    2,   79_063_965.21),
            ("P2.2",   "Sonstige Sonderposten",                           2,   10_857_679.46),
            ("P3",     "Rückstellungen",                                  1,   21_439_654.10),
            ("P3.1",   "Pensions- & Beihilfeverpflichtungen",             2,    3_729_344.00),
            ("P3.2",   "Sonstige Rückstellungen",                         2,   17_710_310.10),
            ("P4",     "Verbindlichkeiten",                               1,   16_552_854.32),
            ("P4.1",   "Investitionskredite",                             2,    9_948_960.17),
            ("P4.2",   "Liquiditätskredite",                              2,            0.00),
            ("P4.3",   "Sonstige Verbindlichkeiten",                      2,    6_603_894.15),
            ("P5",     "Rechnungsabgrenzungsposten (Passiva)",            1,      800_622.05),
        ],
    },
    2020: {
        "AKTIVA": [
            ("A1",     "Anlagevermögen",                                  1,  253_127_808.27),
            ("A1.1",   "Immaterielle Vermögensgegenstände",               2,    5_296_610.37),
            ("A1.2",   "Sachanlagen",                                     2,  186_468_004.91),
            ("A1.3",   "Finanzanlagevermögen",                            2,   61_363_192.99),
            ("A1.3.1", "Anteile verbundene Unternehmen (u.a. EB KDS)",    3,   48_195_169.77),
            ("A2",     "Umlaufvermögen",                                  1,   27_039_303.85),
            ("A2.1",   "Forderungen & sonstige Vermögensgegenstände",     2,    6_275_144.23),
            ("A2.2",   "Liquide Mittel (Kasse & Bank)",                   2,   19_478_529.11),
            ("A2.3",   "Sonstiges Umlaufvermögen (Vorräte u.a.)",         2,    1_285_630.51),
            ("A3",     "Rechnungsabgrenzungsposten (Aktiva)",             1,      951_400.66),
        ],
        "PASSIVA": [
            ("P1",     "Eigenkapital",                                    1,  153_831_943.84),
            ("P1.1",   "Allgemeine Rücklage",                             2,   72_375_477.03),
            ("P1.2",   "Ergebnisvortrag",                                 2,   76_900_451.13),
            ("P1.3",   "Jahresergebnis",                                  2,    4_556_015.68),
            ("P2",     "Sonderposten (Zuwendungen & Ausgleichsabgaben)",  1,   86_927_529.26),
            ("P2.1",   "Sonderposten aus Zuwendungen",                    2,   71_096_482.42),
            ("P2.2",   "Sonstige Sonderposten",                           2,   15_831_046.84),
            ("P3",     "Rückstellungen",                                  1,   20_140_051.08),
            ("P3.1",   "Pensions- & Beihilfeverpflichtungen",             2,    3_644_644.00),
            ("P3.2",   "Sonstige Rückstellungen",                         2,   16_495_407.08),
            ("P4",     "Verbindlichkeiten",                               1,   19_325_299.95),
            ("P4.1",   "Investitionskredite",                             2,   12_059_942.16),
            ("P4.2",   "Liquiditätskredite",                              2,            0.00),
            ("P4.3",   "Sonstige Verbindlichkeiten",                      2,    7_265_357.79),
            ("P5",     "Rechnungsabgrenzungsposten (Passiva)",            1,      893_688.65),
        ],
    },
}


# ── EB KDS Kennzahlen (alle Werte in TEUR) ─────────────────────────────────
# Quelle: Beteiligungsbericht Suhl GJ 2024, Seiten 33-35
EB_KDS = [
    # Unternehmenskennzahlen (Tabelle Seite 33)
    (2021, "KENNZAHLEN", "jahresergebnis",    -313.0),
    (2021, "KENNZAHLEN", "vermogen_gesamt",   5997.0),
    (2021, "KENNZAHLEN", "eigenkapital",      1045.0),
    (2021, "KENNZAHLEN", "ek_quote_pct",        17.4),
    (2021, "KENNZAHLEN", "cashflow_laufend",   716.0),
    (2022, "KENNZAHLEN", "jahresergebnis",    -500.0),
    (2022, "KENNZAHLEN", "vermogen_gesamt",   5527.0),
    (2022, "KENNZAHLEN", "eigenkapital",       901.0),
    (2022, "KENNZAHLEN", "ek_quote_pct",        16.3),
    (2022, "KENNZAHLEN", "cashflow_laufend", -1298.0),
    (2023, "KENNZAHLEN", "jahresergebnis",    -382.0),
    (2023, "KENNZAHLEN", "vermogen_gesamt",   6096.0),
    (2023, "KENNZAHLEN", "eigenkapital",       893.0),
    (2023, "KENNZAHLEN", "ek_quote_pct",        14.6),
    (2023, "KENNZAHLEN", "cashflow_laufend",   501.0),
    (2023, "KENNZAHLEN", "zuschuss_stadt",   14267.0),
    (2023, "KENNZAHLEN", "investitionen",      277.0),
    (2023, "KENNZAHLEN", "mitarbeiter",        113.0),
    (2024, "KENNZAHLEN", "jahresergebnis",    -409.0),
    (2024, "KENNZAHLEN", "vermogen_gesamt",   5590.0),
    (2024, "KENNZAHLEN", "eigenkapital",       711.0),
    (2024, "KENNZAHLEN", "ek_quote_pct",        12.3),
    (2024, "KENNZAHLEN", "cashflow_laufend",  -677.0),
    (2024, "KENNZAHLEN", "zuschuss_stadt",   11529.0),
    (2024, "KENNZAHLEN", "investitionen",     1157.0),
    (2024, "KENNZAHLEN", "mitarbeiter",        110.0),
    # Bilanzdaten Aktiva (Seite 34)
    (2022, "BILANZ_AKTIVA", "anlagevermoegen",  1373.0),
    (2022, "BILANZ_AKTIVA", "umlaufvermoegen",  4148.0),
    (2022, "BILANZ_AKTIVA", "bilanzsumme",      5527.0),
    (2023, "BILANZ_AKTIVA", "anlagevermoegen",  1540.0),
    (2023, "BILANZ_AKTIVA", "umlaufvermoegen",  4551.0),
    (2023, "BILANZ_AKTIVA", "bilanzsumme",      6096.0),
    (2024, "BILANZ_AKTIVA", "anlagevermoegen",  2578.0),
    (2024, "BILANZ_AKTIVA", "umlaufvermoegen",  3006.0),
    (2024, "BILANZ_AKTIVA", "bilanzsumme",      5590.0),
    # Bilanzdaten Passiva (Seite 34)
    (2022, "BILANZ_PASSIVA", "eigenkapital",      894.0),
    (2022, "BILANZ_PASSIVA", "sonderposten",        7.0),
    (2022, "BILANZ_PASSIVA", "rueckstellungen",   510.0),
    (2022, "BILANZ_PASSIVA", "verbindlichkeiten", 1521.0),
    (2022, "BILANZ_PASSIVA", "rap",              2595.0),
    (2022, "BILANZ_PASSIVA", "bilanzsumme",      5527.0),
    (2023, "BILANZ_PASSIVA", "eigenkapital",      884.0),
    (2023, "BILANZ_PASSIVA", "sonderposten",        9.0),
    (2023, "BILANZ_PASSIVA", "rueckstellungen",   539.0),
    (2023, "BILANZ_PASSIVA", "verbindlichkeiten", 1973.0),
    (2023, "BILANZ_PASSIVA", "rap",              2691.0),
    (2023, "BILANZ_PASSIVA", "bilanzsumme",      6096.0),
    (2024, "BILANZ_PASSIVA", "eigenkapital",      690.0),
    (2024, "BILANZ_PASSIVA", "sonderposten",       21.0),
    (2024, "BILANZ_PASSIVA", "rueckstellungen",   500.0),
    (2024, "BILANZ_PASSIVA", "verbindlichkeiten", 1636.0),
    (2024, "BILANZ_PASSIVA", "rap",              2743.0),
    (2024, "BILANZ_PASSIVA", "bilanzsumme",      5590.0),
    # GuV (Seite 35)
    (2022, "GUV", "umsatzerloese",    16412.0),
    (2022, "GUV", "ertraege_gesamt",  16460.0),
    (2022, "GUV", "materialaufwand",  -5615.0),
    (2022, "GUV", "personalaufwand",  -6167.0),
    (2022, "GUV", "abschreibungen",     -98.0),
    (2022, "GUV", "jahresergebnis",    -500.0),
    (2023, "GUV", "umsatzerloese",    16170.0),
    (2023, "GUV", "ertraege_gesamt",  16263.0),
    (2023, "GUV", "materialaufwand",  -4847.0),
    (2023, "GUV", "personalaufwand",  -6467.0),
    (2023, "GUV", "abschreibungen",    -113.0),
    (2023, "GUV", "jahresergebnis",    -382.0),
    (2024, "GUV", "umsatzerloese",    17496.0),
    (2024, "GUV", "ertraege_gesamt",  17568.0),
    (2024, "GUV", "materialaufwand",  -5662.0),
    (2024, "GUV", "personalaufwand",  -6891.0),
    (2024, "GUV", "abschreibungen",    -119.0),
    (2024, "GUV", "jahresergebnis",    -409.0),
]


def main():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    setup_tables(con)

    # Bilanz einfügen
    n_bilanz = 0
    for jahr, seiten in BILANZ.items():
        for seite, positionen in seiten.items():
            for code, bez, ebene, betrag in positionen:
                con.execute("""
                    INSERT OR REPLACE INTO bilanz_positionen
                        (daten_jahr, seite, position_code, bezeichnung, ebene, betrag)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (jahr, seite, code, bez, ebene, betrag))
                n_bilanz += 1

    # EB KDS einfügen
    n_kds = 0
    for (jahr, bereich, position, betrag) in EB_KDS:
        con.execute("""
            INSERT OR REPLACE INTO eb_kds_kennzahlen
                (daten_jahr, bereich, position, betrag_teur)
            VALUES (?, ?, ?, ?)
        """, (jahr, bereich, position, betrag))
        n_kds += 1

    con.commit()
    con.close()
    print(f"[OK] bilanz_positionen: {n_bilanz} Eintraege (2020+2021)")
    print(f"[OK] eb_kds_kennzahlen: {n_kds} Eintraege (2021-2024)")


if __name__ == "__main__":
    main()
