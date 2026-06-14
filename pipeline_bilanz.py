"""
pipeline_bilanz.py
Befuellt bilanz_positionen und eb_kds_kennzahlen in suhl_haushalt_2025.db.
Quellen:
  Bilanz (Stadt Suhl): Jahresabschluss 31.12.2021, Seite 69 (Originalwerte in EUR)
                       Vorjahreszahlen 31.12.2020 aus der selben Quelle
  EB KDS:              Beteiligungsbericht 2024, Seiten 33-35 (Angaben in TEUR)
  Bilanzentwicklung:   Jahresabschluss 2021, Seite 153 (Veraenderungen seit 2013)

Ebenen in bilanz_positionen:
  1 = Hauptgruppe (A1 Anlageverm., A2 Umlaufverm., A3 RAP; P1 EK, P2 SP, P3 RST, P4 VB, P5 RAP)
  2 = Untergruppe  (A1.1 Immateriell, A1.2 Sachanlagen, P3.1 Pensionen ...)
  3 = Detail       (A1.2.1 Wald, A1.2.2 Unbebaut, P4.5 LuL-Verb. ...)
"""
import sqlite3, os, json

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


# ── Stadt-Suhl-Bilanz (Werte in EUR exakt aus Seite 69 Jahresabschluss) ───────
# Alle Summen geprüft und mit Elternsummen verifiziert.
# 2021 = aktuelles Jahr, 2020 = Vorjahreszahlen (gleiche Seite)
BILANZ = {
    2021: {
        "AKTIVA": [
            # ── Ebene 1: Hauptgruppen ──────────────────────────────────────────
            ("A1",      "Anlagevermögen",                                         1, 257_609_775.55),
            ("A2",      "Umlaufvermögen",                                         1,  20_907_422.32),
            ("A3",      "Rechnungsabgrenzungsposten (Aktiva)",                    1,     942_264.45),
            # ── Ebene 2: A1-Untergruppen ───────────────────────────────────────
            ("A1.1",    "Immaterielle Vermögensgegenstände",                      2,   5_073_041.87),
            ("A1.2",    "Sachanlagen",                                            2, 191_312_988.57),
            ("A1.3",    "Finanzanlagevermögen",                                   2,  61_223_745.11),
            # ── Ebene 2: A2-Untergruppen ───────────────────────────────────────
            ("A2.1",    "Vorräte",                                                2,   1_084_858.00),
            ("A2.2",    "Forderungen u. sonstige Vermögensgegenstände",           2,   9_607_037.50),
            ("A2.3",    "Wertpapiere des Umlaufvermögens",                        2,           0.00),
            ("A2.4",    "Kassenbestand, Guthaben bei Kreditinstituten",           2,  10_215_526.82),
            # ── Ebene 2: A3-Untergruppen ───────────────────────────────────────
            ("A3.1",    "Disagio",                                                2,           0.00),
            ("A3.2",    "Sonstige Rechnungsabgrenzungsposten",                    2,     942_264.45),
            # ── Ebene 3: A1.1 Immaterielle Vermögensgegenstände ───────────────
            ("A1.1.1",  "Entgeltlich erworbene Konzessionen, Rechte und Lizenzen",3,     371_556.61),
            ("A1.1.2",  "Geleistete Zuwendungen",                                 3,   4_652_463.58),
            ("A1.1.3",  "Geleistete Investitionszuschüsse",                       3,           0.00),
            ("A1.1.4",  "Geschäfts- oder Firmenwert",                             3,           0.00),
            ("A1.1.5",  "Geleistete Anzahlungen auf immaterielle VG, Anlagen i.B.",3,     49_021.68),
            # ── Ebene 3: A1.2 Sachanlagen (10 Positionen) ────────────────────
            ("A1.2.1",  "Wald, Forsten",                                          3,   5_682_118.30),
            ("A1.2.2",  "Unbebaute Grundstücke und grundstücksgleiche Rechte",    3,   9_785_867.77),
            ("A1.2.3",  "Bebaute Grundstücke und grundstücksgleiche Rechte",      3,  73_324_951.32),
            ("A1.2.4",  "Infrastrukturvermögen",                                  3,  78_959_766.80),
            ("A1.2.5",  "Bauten auf fremdem Grund und Boden",                     3,     390_101.37),
            ("A1.2.6",  "Kunstgegenstände, Denkmäler",                            3,   2_345_639.29),
            ("A1.2.7",  "Maschinen, technische Anlagen, Fahrzeuge",               3,   5_119_106.62),
            ("A1.2.8",  "Betriebs- und Geschäftsausstattung",                     3,   2_857_768.12),
            ("A1.2.9",  "Pflanzen und Tiere",                                     3,   4_156_963.04),
            ("A1.2.10", "Geleistete Anzahlungen auf Sachanlagen, Anlagen im Bau", 3,   8_690_705.94),
            # ── Ebene 3: A1.3 Finanzanlagevermögen (8 Positionen) ────────────
            ("A1.3.1",  "Anteile an verbundenen Unternehmen (u.a. EB KDS)",       3,  48_240_934.65),
            ("A1.3.2",  "Ausleihungen an verbundene Unternehmen",                 3,           0.00),
            ("A1.3.3",  "Beteiligungen",                                          3,       6_275.00),
            ("A1.3.4",  "Ausleihungen an Beteiligungsunternehmen",                3,           0.00),
            ("A1.3.5",  "Sondervermögen, Zweckverbände, kommunale Stiftungen",    3,  12_969_443.04),
            ("A1.3.6",  "Ausleihungen an Sondervermögen und Zweckverbände",       3,           0.00),
            ("A1.3.7",  "Sonstige Wertpapiere des Anlagevermögens",               3,       7_092.42),
            ("A1.3.8",  "Sonstige Ausleihungen",                                  3,           0.00),
            # ── Ebene 3: A2.1 Vorräte ─────────────────────────────────────────
            ("A2.1.1",  "Roh-, Hilfs- und Betriebsstoffe",                        3,           0.00),
            ("A2.1.2",  "Unfertige Erzeugnisse und Leistungen",                   3,           0.00),
            ("A2.1.3",  "Fertige Erzeugnisse und Waren",                          3,   1_084_858.00),
            ("A2.1.4",  "Geleistete Anzahlungen auf Vorräte",                     3,           0.00),
            # ── Ebene 3: A2.2 Forderungen (7 Positionen) ─────────────────────
            ("A2.2.1",  "Öffentlich-rechtliche Forderungen und Transferleistungen",3,  5_076_802.20),
            ("A2.2.2",  "Privatrechtliche Forderungen aus Lieferungen und Leistungen",3, 453_666.47),
            ("A2.2.3",  "Forderungen gegen verbundene Unternehmen",               3,     735_488.38),
            ("A2.2.4",  "Forderungen gegen Beteiligungsunternehmen",              3,      45_021.90),
            ("A2.2.5",  "Forderungen gegen Sondervermögen und Zweckverbände",     3,   1_083_864.73),
            ("A2.2.6",  "Forderungen gegen den sonstigen öffentlichen Bereich",   3,   2_142_911.80),
            ("A2.2.7",  "Sonstige Vermögensgegenstände",                          3,      69_282.02),
        ],
        "PASSIVA": [
            # ── Ebene 1: Hauptgruppen ──────────────────────────────────────────
            ("P1",      "Eigenkapital",                                           1, 150_744_687.18),
            ("P2",      "Sonderposten",                                           1,  89_921_644.67),
            ("P3",      "Rückstellungen",                                         1,  21_439_654.10),
            ("P4",      "Verbindlichkeiten",                                      1,  16_552_854.32),
            ("P5",      "Rechnungsabgrenzungsposten (Passiva)",                   1,     800_622.05),
            # ── Ebene 2: P1 Eigenkapital (5 Positionen) ───────────────────────
            ("P1.1",    "Allgemeine Rücklage",                                    2,  72_373_935.76),
            ("P1.2",    "Zweckgebundene Kapitalrücklage",                         2,           0.00),
            ("P1.3",    "Zweckgebundene Ergebnisrücklage",                        2,           0.00),
            ("P1.4",    "Ergebnisvortrag",                                        2,  81_456_466.81),
            ("P1.5",    "Jahresergebnis (Überschuss / Fehlbetrag)",               2,  -3_085_715.39),
            # ── Ebene 2: P2 Sonderposten (7 Positionen) ───────────────────────
            ("P2.1",    "SP für Belastungen aus dem kommunalen Finanzausgleich",  2,           0.00),
            ("P2.2",    "SP aus Zuwendungen (Bund, Land, EU)",                    2,  79_063_965.21),
            ("P2.3",    "SP aus Beiträgen und ähnlichen Entgelten",               2,   2_413_590.58),
            ("P2.4",    "SP aus Anzahlungen",                                     2,   6_574_871.29),
            ("P2.5",    "SP für den Gebührenausgleich",                           2,           0.00),
            ("P2.6",    "SP mit Rücklagenanteil",                                 2,           0.00),
            ("P2.7",    "Sonstige Sonderposten",                                  2,   1_869_217.59),
            # ── Ebene 2: P3 Rückstellungen (3 Positionen) ─────────────────────
            ("P3.1",    "Rückstellungen für Pensionen und ähnliche Verpflichtungen",2, 3_729_344.00),
            ("P3.2",    "Steuerrückstellungen",                                   2,     102_291.00),
            ("P3.3",    "Sonstige Rückstellungen",                                2,  17_608_019.10),
            # ── Ebene 2: P4 Verbindlichkeiten (11 Positionen) ─────────────────
            ("P4.1",    "Anleihen",                                               2,           0.00),
            ("P4.2",    "Verbindlichkeiten aus Kreditaufnahmen (Investitionskredite)",2, 9_948_960.17),
            ("P4.3",    "Verbindlichkeiten wirtschaftlich gleich Kreditaufnahmen", 2,           0.00),
            ("P4.4",    "Erhaltene Anzahlungen auf Bestellungen",                 2,           0.00),
            ("P4.5",    "Verbindlichkeiten aus Lieferungen und Leistungen",       2,   1_779_868.41),
            ("P4.6",    "Verbindlichkeiten aus Transferleistungen",               2,   2_159_020.32),
            ("P4.7",    "Verbindlichkeiten gegenüber verbundenen Unternehmen",    2,     382_993.42),
            ("P4.8",    "Verbindlichkeiten gegenüber Beteiligungsunternehmen",    2,     324_976.39),
            ("P4.9",    "Verbindlichkeiten gegenüber Sondervermögen und Zweckverbänden",2,684_644.31),
            ("P4.10",   "Verbindlichkeiten gegenüber dem sonstigen öff. Bereich", 2,     562_344.55),
            ("P4.11",   "Sonstige Verbindlichkeiten",                             2,     710_046.75),
            # ── Ebene 2: P5 RAP (3 Positionen) ───────────────────────────────
            ("P5.1",    "Grabnutzungsentgelte",                                   2,           0.00),
            ("P5.2",    "Anzahlungen auf Grabnutzungsentgelte",                   2,           0.00),
            ("P5.3",    "Sonstige Rechnungsabgrenzungsposten",                    2,     800_622.05),
        ],
    },
    2020: {
        "AKTIVA": [
            # ── Ebene 1 ────────────────────────────────────────────────────────
            ("A1",      "Anlagevermögen",                                         1, 253_127_808.27),
            ("A2",      "Umlaufvermögen",                                         1,  27_039_303.85),
            ("A3",      "Rechnungsabgrenzungsposten (Aktiva)",                    1,     951_400.66),
            # ── Ebene 2: A1 ────────────────────────────────────────────────────
            ("A1.1",    "Immaterielle Vermögensgegenstände",                      2,   5_296_610.37),
            ("A1.2",    "Sachanlagen",                                            2, 186_468_004.91),
            ("A1.3",    "Finanzanlagevermögen",                                   2,  61_363_192.99),
            # ── Ebene 2: A2 ────────────────────────────────────────────────────
            ("A2.1",    "Vorräte",                                                2,   1_285_630.46),
            ("A2.2",    "Forderungen u. sonstige Vermögensgegenstände",           2,   6_275_144.28),
            ("A2.3",    "Wertpapiere des Umlaufvermögens",                        2,           0.00),
            ("A2.4",    "Kassenbestand, Guthaben bei Kreditinstituten",           2,  19_478_529.11),
            # ── Ebene 2: A3 ────────────────────────────────────────────────────
            ("A3.1",    "Disagio",                                                2,           0.00),
            ("A3.2",    "Sonstige Rechnungsabgrenzungsposten",                    2,     951_400.66),
            # ── Ebene 3: A1.1 ──────────────────────────────────────────────────
            ("A1.1.1",  "Entgeltlich erworbene Konzessionen, Rechte und Lizenzen",3,     316_446.44),
            ("A1.1.2",  "Geleistete Zuwendungen",                                 3,   4_804_114.95),
            ("A1.1.3",  "Geleistete Investitionszuschüsse",                       3,           0.00),
            ("A1.1.4",  "Geschäfts- oder Firmenwert",                             3,           0.00),
            ("A1.1.5",  "Geleistete Anzahlungen auf immaterielle VG, Anlagen i.B.",3,    176_048.98),
            # ── Ebene 3: A1.2 ──────────────────────────────────────────────────
            ("A1.2.1",  "Wald, Forsten",                                          3,   5_683_548.06),
            ("A1.2.2",  "Unbebaute Grundstücke und grundstücksgleiche Rechte",    3,   9_672_931.46),
            ("A1.2.3",  "Bebaute Grundstücke und grundstücksgleiche Rechte",      3,  64_879_476.51),
            ("A1.2.4",  "Infrastrukturvermögen",                                  3,  78_440_250.69),
            ("A1.2.5",  "Bauten auf fremdem Grund und Boden",                     3,     402_302.65),
            ("A1.2.6",  "Kunstgegenstände, Denkmäler",                            3,   2_344_039.29),
            ("A1.2.7",  "Maschinen, technische Anlagen, Fahrzeuge",               3,   5_282_083.00),
            ("A1.2.8",  "Betriebs- und Geschäftsausstattung",                     3,   2_281_508.35),
            ("A1.2.9",  "Pflanzen und Tiere",                                     3,   4_129_166.27),
            ("A1.2.10", "Geleistete Anzahlungen auf Sachanlagen, Anlagen im Bau", 3,  13_352_698.63),
            # ── Ebene 3: A1.3 ──────────────────────────────────────────────────
            ("A1.3.1",  "Anteile an verbundenen Unternehmen (u.a. EB KDS)",       3,  48_199_169.77),
            ("A1.3.2",  "Ausleihungen an verbundene Unternehmen",                 3,           0.00),
            ("A1.3.3",  "Beteiligungen",                                          3,      48_039.88),
            ("A1.3.4",  "Ausleihungen an Beteiligungsunternehmen",                3,           0.00),
            ("A1.3.5",  "Sondervermögen, Zweckverbände, kommunale Stiftungen",    3,  13_108_976.19),
            ("A1.3.6",  "Ausleihungen an Sondervermögen und Zweckverbände",       3,           0.00),
            ("A1.3.7",  "Sonstige Wertpapiere des Anlagevermögens",               3,       7_007.15),
            ("A1.3.8",  "Sonstige Ausleihungen",                                  3,           0.00),
            # ── Ebene 3: A2.1 ──────────────────────────────────────────────────
            ("A2.1.1",  "Roh-, Hilfs- und Betriebsstoffe",                        3,           0.00),
            ("A2.1.2",  "Unfertige Erzeugnisse und Leistungen",                   3,           0.00),
            ("A2.1.3",  "Fertige Erzeugnisse und Waren",                          3,   1_285_630.46),
            ("A2.1.4",  "Geleistete Anzahlungen auf Vorräte",                     3,           0.00),
            # ── Ebene 3: A2.2 ──────────────────────────────────────────────────
            ("A2.2.1",  "Öffentlich-rechtliche Forderungen und Transferleistungen",3,  2_730_763.30),
            ("A2.2.2",  "Privatrechtliche Forderungen aus Lieferungen und Leistungen",3, 307_498.11),
            ("A2.2.3",  "Forderungen gegen verbundene Unternehmen",               3,      29_517.40),
            ("A2.2.4",  "Forderungen gegen Beteiligungsunternehmen",              3,       3_673.12),
            ("A2.2.5",  "Forderungen gegen Sondervermögen und Zweckverbände",     3,   1_078_460.13),
            ("A2.2.6",  "Forderungen gegen den sonstigen öffentlichen Bereich",   3,   1_939_549.10),
            ("A2.2.7",  "Sonstige Vermögensgegenstände",                          3,     185_683.12),
        ],
        "PASSIVA": [
            # ── Ebene 1 ────────────────────────────────────────────────────────
            ("P1",      "Eigenkapital",                                           1, 153_831_943.84),
            ("P2",      "Sonderposten",                                           1,  86_927_529.26),
            ("P3",      "Rückstellungen",                                         1,  20_140_051.08),
            ("P4",      "Verbindlichkeiten",                                      1,  19_325_299.95),
            ("P5",      "Rechnungsabgrenzungsposten (Passiva)",                   1,     893_688.65),
            # ── Ebene 2: P1 ────────────────────────────────────────────────────
            ("P1.1",    "Allgemeine Rücklage",                                    2,  72_375_477.03),
            ("P1.2",    "Zweckgebundene Kapitalrücklage",                         2,           0.00),
            ("P1.3",    "Zweckgebundene Ergebnisrücklage",                        2,           0.00),
            ("P1.4",    "Ergebnisvortrag",                                        2,  76_900_451.13),
            ("P1.5",    "Jahresergebnis (Überschuss / Fehlbetrag)",               2,   4_556_015.68),
            # ── Ebene 2: P2 ────────────────────────────────────────────────────
            ("P2.1",    "SP für Belastungen aus dem kommunalen Finanzausgleich",  2,           0.00),
            ("P2.2",    "SP aus Zuwendungen (Bund, Land, EU)",                    2,  71_096_482.42),
            ("P2.3",    "SP aus Beiträgen und ähnlichen Entgelten",               2,   2_563_385.30),
            ("P2.4",    "SP aus Anzahlungen",                                     2,  11_086_312.41),
            ("P2.5",    "SP für den Gebührenausgleich",                           2,           0.00),
            ("P2.6",    "SP mit Rücklagenanteil",                                 2,           0.00),
            ("P2.7",    "Sonstige Sonderposten",                                  2,   2_181_349.13),
            # ── Ebene 2: P3 ────────────────────────────────────────────────────
            ("P3.1",    "Rückstellungen für Pensionen und ähnliche Verpflichtungen",2, 3_644_644.00),
            ("P3.2",    "Steuerrückstellungen",                                   2,     172_800.00),
            ("P3.3",    "Sonstige Rückstellungen",                                2,  16_322_607.08),
            # ── Ebene 2: P4 ────────────────────────────────────────────────────
            ("P4.1",    "Anleihen",                                               2,           0.00),
            ("P4.2",    "Verbindlichkeiten aus Kreditaufnahmen (Investitionskredite)",2,12_059_942.16),
            ("P4.3",    "Verbindlichkeiten wirtschaftlich gleich Kreditaufnahmen", 2,           0.00),
            ("P4.4",    "Erhaltene Anzahlungen auf Bestellungen",                 2,           0.00),
            ("P4.5",    "Verbindlichkeiten aus Lieferungen und Leistungen",       2,   1_902_532.56),
            ("P4.6",    "Verbindlichkeiten aus Transferleistungen",               2,   1_914_535.79),
            ("P4.7",    "Verbindlichkeiten gegenüber verbundenen Unternehmen",    2,     227_903.81),
            ("P4.8",    "Verbindlichkeiten gegenüber Beteiligungsunternehmen",    2,     331_126.58),
            ("P4.9",    "Verbindlichkeiten gegenüber Sondervermögen und Zweckverbänden",2,1_074_088.23),
            ("P4.10",   "Verbindlichkeiten gegenüber dem sonstigen öff. Bereich", 2,   1_181_503.79),
            ("P4.11",   "Sonstige Verbindlichkeiten",                             2,     633_667.03),
            # ── Ebene 2: P5 ────────────────────────────────────────────────────
            ("P5.1",    "Grabnutzungsentgelte",                                   2,           0.00),
            ("P5.2",    "Anzahlungen auf Grabnutzungsentgelte",                   2,           0.00),
            ("P5.3",    "Sonstige Rechnungsabgrenzungsposten",                    2,     893_688.65),
        ],
    },
}


# ── Bilanzentwicklung seit 2013 (Seite 153 Jahresabschluss 2021) ──────────────
# Veraenderung der Bilanzsumme vom 01.01.2013 bis 31.12.2021: +38.365 TEUR
BILANZ_ENTWICKLUNG = {
    "bilanzsumme_2021_teur":  279_459,
    "veraenderung_seit_2013_teur": 38_365,
    "quelle_seite": 153,
    "aktivseite": [
        {
            "position": "Immaterielle Vermögensgegenstände",
            "position_code": "A1.1",
            "delta_teur": 3_867,
            "anmerkung": "Anstieg immaterieller VG (Konzessionen, Zuwendungen)"
        },
        {
            "position": "Sachanlagen",
            "position_code": "A1.2",
            "delta_teur": 16_318,
            "davon_eingemeindung_teur": 16_959,
            "anmerkung": "Davon Eingemeindung +16.959 TEUR; per Saldo Werteverzehr beim Sachanlagevermögen"
        },
        {
            "position": "Finanzanlagevermögen",
            "position_code": "A1.3",
            "delta_teur": 3_873,
            "davon_eingemeindung_teur": 2_220,
            "davon_eb_kds_ek_teur": 1_037,
            "anmerkung": "Eingemeindung +2.220 TEUR, EB KDS Eigenkapitalerhöhung +1.037 TEUR"
        },
        {
            "position": "Kassenbestand / Bankguthaben",
            "position_code": "A2.4",
            "delta_teur": 10_153,
            "anmerkung": "Im Wesentlichen verbliebene Mittel aus Verkauf der E.ON-Aktien"
        },
    ],
    "passivseite": [
        {
            "position": "Allgemeine Rücklage",
            "position_code": "P1.1",
            "delta_teur": 3_280,
            "davon_eingemeindung_teur": 7_303,
            "anmerkung": "Eingemeindung +7.303 TEUR, saldiert mit Korrekturen Eröffnungsbilanz"
        },
        {
            "position": "Jahresergebnis + Ergebnisvortrag",
            "position_code": "P1.4+P1.5",
            "delta_teur": 78_371,
            "anmerkung": "Positive Jahresergebnisse, Großteil aus E.ON-Aktienverkauf"
        },
        {
            "position": "Sonderposten zum Anlagevermögen",
            "position_code": "P2",
            "delta_teur": 17_714,
            "davon_eingemeindung_teur": 9_829,
            "anmerkung": "Erhöhung durch Fördermittel und Eingemeindung (+9.829 TEUR)"
        },
        {
            "position": "Verbindlichkeiten aus Kreditaufnahmen",
            "position_code": "P4.2",
            "delta_teur": -58_596,
            "anmerkung": "Schuldenabbau: Rückgang der Investitionskredite um 58,6 Mio EUR"
        },
    ]
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


def verify_sums():
    """Prueft ob Untergruppen korrekt zu Hauptgruppen aufaddieren."""
    errors = []
    for yr, seiten in BILANZ.items():
        for seite, positionen in seiten.items():
            by_code = {code: betrag for code, _bez, _ebene, betrag in positionen}
            # Ebene-2 vs Ebene-1
            for e1, e2_prefix in [("A1", "A1."), ("A2", "A2."), ("A3", "A3."),
                                   ("P1", "P1."), ("P2", "P2."), ("P3", "P3."),
                                   ("P4", "P4."), ("P5", "P5.")]:
                if e1 not in by_code:
                    continue
                children = [b for c, b in by_code.items()
                            if c.startswith(e2_prefix) and c.count(".") == e2_prefix.count(".")]
                if not children:
                    continue
                s = round(sum(children), 2)
                expected = round(by_code[e1], 2)
                if abs(s - expected) > 0.02:
                    errors.append(f"{yr}/{seite}/{e1}: Summe {s} != {expected} (Diff {s-expected:.2f})")
    if errors:
        for e in errors:
            print(f"[WARN] {e}")
    else:
        print("[OK] Alle Summen verifiziert")
    return len(errors) == 0


def main():
    verify_sums()

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    setup_tables(con)

    # Bilanz einfügen (INSERT OR REPLACE ersetzt veraltete vereinfachte Eintraege)
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
    print(f"[OK] bilanz_positionen: {n_bilanz} Eintraege (2020+2021, Ebenen 1-3)")
    print(f"[OK] eb_kds_kennzahlen: {n_kds} Eintraege (2021-2024)")


if __name__ == "__main__":
    main()
