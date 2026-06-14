#!/usr/bin/env python3
"""
pipeline_beteiligungen.py
Befüllt DB-Tabellen für Beteiligungen + Finanzströme aus dem Beteiligungsbericht 2024.
Quelle: Beteiligungsbericht der Stadt Suhl für das Geschäftsjahr 2024
"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "suhl_haushalt_2025.db")

# ---------------------------------------------------------------------------
# Beteiligungen Stammdaten
# ---------------------------------------------------------------------------
BETEILIGUNGEN = [
    # (kuerzel, name, typ, bet_direkt, bet_indirekt, via_kuerzel, stammkapital_eur,
    #  gruendungsjahr, sektor, status, oeffentlicher_zweck)
    ("STADT", "Stadt Suhl", "KOMMUNE", 100.0, 100.0, None, 0, None,
     "KOMMUNE", "aktiv", "Kommunale Selbstverwaltung"),

    # Unmittelbare Beteiligungen
    ("CCS", "Congress Centrum Suhl – Touristik und Congress GmbH", "GMBH",
     100.0, 100.0, "STADT", 260500, 1991,
     "HOLDING", "aktiv",
     "Betrieb des Sammelkanals, Wärme-/Strom-/Gasversorgung durch Beteiligungsgesellschaften; Kongress-/Tourismusbetrieb"),
    ("SSB", "Suhler Stadtbetrieb GmbH", "GMBH",
     100.0, 100.0, "STADT", 1025000, 1990,
     "ENTSORGUNG", "aktiv",
     "Aufrechterhaltung öffentlicher Sauberkeit und Ordnung"),
    ("GEWO", "GeWo Städtische Wohnungsgesellschaft mbH Suhl", "GMBH",
     100.0, 100.0, "STADT", 5112919, 1990,
     "WOHNEN", "aktiv",
     "Sicherung des Wohnungsbestandes für die Einwohnerschaft"),
    ("SFG", "Sport- und Freizeit GmbH Schmiedefeld am Rennsteig i. L.", "GMBH",
     100.0, 100.0, "STADT", 25000, 1999,
     "SPORT", "liquidation",
     "In Liquidation seit 2022"),
    ("EBKDS", "Eigenbetrieb Kommunalwirtschaftliche Dienstleistungen Suhl", "EIGENBETRIEB",
     100.0, 100.0, "STADT", 25000, 2012,
     "INFRASTRUKTUR", "aktiv",
     "Kommunale Daseinsvorsorge: Straßen, Grünflächen, Abfallentsorgung, Friedhöfe"),
    ("ITM", "Institut für Transfusionsmedizin Suhl gGmbH", "GGMBH",
     50.93, 50.93, "STADT", 27000, 1994,
     "GESUNDHEIT", "aktiv",
     "Blutversorgung und Labormedizin – kein öffentlicher Zweck (§66 ThürKO)"),
    ("SW", "Suhler Werkstätten gGmbH", "GGMBH",
     37.0, 37.0, "STADT", 25565, 1992,
     "SOZIAL", "aktiv",
     "Werkstätten für Menschen mit Behinderung, Bildung und Rehabilitation"),
    ("SSZ", "Schießsportzentrum Suhl GmbH", "GMBH",
     25.1, 25.1, "STADT", 25000, 2016,
     "SPORT", "aktiv",
     "Nationales/internationales Leistungszentrum Schießsport, Olympiastützpunkt"),
    ("KIV", "KIV Kommunale Informationsverarbeitung Thüringen GmbH", "GMBH",
     0.004, 0.004, "STADT", 25800, 1993,
     "IT", "aktiv",
     "Technikunterstützte Informationsverarbeitung für Kommunen"),

    # Mittelbare Beteiligungen
    ("BAF", "Bestattungsinstitut Am Friedhof GmbH Suhl", "GMBH",
     0.0, 100.0, "SSB", 26000, 1997,
     "SONSTIGES", "fiskalisiert",
     "Bestattungen und Grabpflege (fiskalisiert § 66 Abs. 2 ThürKO)"),
    ("KLEIDER", "Kleider & Co. Recycling GmbH", "GMBH",
     0.0, 100.0, "SSB", 26000, 1998,
     "ENTSORGUNG", "fiskalisiert",
     "Containerdienst und Recyclinghof (fiskalisiert § 66 Abs. 2 ThürKO)"),
    ("SNG", "Städtische Nahverkehrsgesellschaft mbH Suhl/Zella-Mehlis", "GMBH",
     0.0, 86.96, "CCS", 29900, 1991,
     "NAHVERKEHR", "aktiv",
     "ÖPNV im Stadtgebiet Suhl (öffentlicher Dienstleistungsauftrag bis 31.12.2027)"),
    ("SWB", "Stadtwerke Suhl/Zella-Mehlis Beteiligungs GmbH", "GMBH",
     0.0, 61.92, "CCS", 250000, 2002,
     "HOLDING", "aktiv",
     "Halten und Verwalten von Beteiligungen (Zwischenholding Stadtwerke)"),
    ("SWSZ", "Stadtwerke Suhl/Zella-Mehlis GmbH", "GMBH",
     0.0, 34.42, "SWB", 10000000, 1992,
     "ENERGIE", "aktiv",
     "Versorgung mit Elektrizität, Gas und Fernwärme"),
    ("SWSZ_NETZ", "Stadtwerke Suhl/Zella-Mehlis Netz GmbH", "GMBH",
     0.0, 34.42, "SWSZ", 3374735, 2007,
     "ENERGIE", "aktiv",
     "Netzbetrieb Strom und Gas (Verteilungsanlagen)"),
]

# ---------------------------------------------------------------------------
# Kennzahlen je Unternehmen und Jahr (TEUR)
# Felder: kuerzel, jahr, umsatz, jahresergebnis, jahresergebnis_nach_eav,
#         bilanzsumme, eigenkapital, verbindlichkeiten, investitionen, mitarbeiter
# ---------------------------------------------------------------------------
KENNZAHLEN = [
    # CCS (ab 2024 nach Verschmelzung SBB+CCS, Vorjahr nicht vergleichbar)
    ("CCS", 2024, 3538, -1644, -1644, 45486, 35518, 2613, 685, 48),
    # SSB
    ("SSB", 2024, 5320, 83, 83, 6343, 2302, 3852, 879, 20),
    ("SSB", 2023, 4885, 112, 112, 5868, 2220, 3540, 327, 20),
    ("SSB", 2022, 4617, -168, -168, 6070, 2108, 3885, None, None),
    ("SSB", 2021, None, 34, 34, 5884, 2275, 2828, None, None),
    # GeWo
    ("GEWO", 2024, 22379, 2276, 2276, 123534, 58265, 63869, 1529, 28),
    ("GEWO", 2023, 21822, 1437, 1437, 127204, 56239, 69305, 1737, 29),
    ("GEWO", 2022, 21838, 948, 948, 129976, 55052, 73344, 1328, None),
    ("GEWO", 2021, None, 1814, 1814, 134449, 54354, 70040, None, None),
    # EBKDS
    ("EBKDS", 2024, 17496, -409, -409, 5590, 690, 1636, 1157, 110),
    ("EBKDS", 2023, 16170, -382, -382, 6096, 884, 1973, 277, 113),
    ("EBKDS", 2022, 16412, -500, -500, 5527, 894, 1521, None, None),
    ("EBKDS", 2021, None, -313, -313, 5997, 1045, 2743, None, None),
    # ITM
    ("ITM", 2024, 24215, 920, 920, 27462, 23584, 560, 5371, 258),
    ("ITM", 2023, 23677, 721, 721, 26411, 22664, 858, 1066, 258),
    ("ITM", 2022, 20673, 1302, 1302, 25242, 22268, 526, None, None),
    ("ITM", 2021, None, 1020, 1020, 24980, 21221, 277, None, None),
    # SW (Suhler Werkstätten)
    ("SW", 2024, 6072, 69, 69, 6418, 5780, 345, 209, 220),
    ("SW", 2023, 5932, 33, 33, 6338, 5711, 384, 761, 234),
    ("SW", 2022, 5774, 151, 151, 6355, 5678, 411, None, None),
    ("SW", 2021, None, 96, 96, 6332, 5527, None, None, None),
    # SSZ
    ("SSZ", 2024, 371, 7, 7, 717, 205, 171, 56, 12),
    ("SSZ", 2023, 387, -11, -11, 696, 198, 215, 84, 12),
    ("SSZ", 2022, 338, 149, 149, 831, 209, 181, None, None),
    ("SSZ", 2021, None, -63, -63, 618, 68, None, None, None),
    # KIV
    ("KIV", 2024, 20329, 1460, 1460, 6152, 3530, 1465, 192, 53),
    ("KIV", 2023, 12108, 614, 614, 3827, 2377, 782, 275, 48),
    # BAF
    ("BAF", 2024, 610, 13, 13, 470, 358, 95, None, 11),
    ("BAF", 2023, 629, 44, 44, 458, 346, 83, None, 9),
    ("BAF", 2022, 691, 29, 29, 430, 301, 70, None, None),
    # KLEIDER
    ("KLEIDER", 2024, 741, 8, 8, 171, 101, 56, 0, 5),
    ("KLEIDER", 2023, 648, -16, -16, 196, 92, 91, 0, 5),
    # SNG
    ("SNG", 2024, 3707, -2852, 0, 5121, 1045, 3444, 653, 87),
    ("SNG", 2023, 3411, -2747, 0, 4803, 1045, 3202, 516, 85),
    ("SNG", 2022, 3008, -2433, 0, 4718, 1045, 3186, None, None),
    ("SNG", 2021, None, -2268, 0, 4739, 1045, None, None, None),
    # SWB (Jahresergebnis vor EAV = 2.865 TEUR, nach EAV = 0)
    ("SWB", 2024, 0, 2865, 0, 10366, 4016, 6344, 0, 0),
    ("SWB", 2023, 0, 3217, 0, 13215, 4016, 9193, 0, 0),
    # SWSZ
    ("SWSZ", 2024, 59004, 5155, 0, 32776, 16291, 10769, 1300, 51),
    ("SWSZ", 2023, 64623, 7899, 0, 34430, 16291, 12126, 1019, 50),
    ("SWSZ", 2022, 42196, 6225, 0, 30459, 14191, 11585, None, None),
    ("SWSZ", 2021, None, 5552, 0, 26885, 14191, None, None, None),
    # SWSZ_NETZ
    ("SWSZ_NETZ", 2024, 26416, 336, 0, 21838, 8438, 8361, 1657, 39),
    ("SWSZ_NETZ", 2023, 25361, 1384, 0, 22018, 8438, 8076, 1819, 41),
    ("SWSZ_NETZ", 2022, 24323, 1644, 0, 20679, 8438, 6250, None, None),
    ("SWSZ_NETZ", 2021, None, 1542, 0, 20265, 8438, None, None, None),
]

# ---------------------------------------------------------------------------
# Finanzströme 2023 + 2024 (TEUR)
# Felder: jahr, von_kuerzel, nach_kuerzel, betrag_teur, typ, bezeichnung
# ---------------------------------------------------------------------------
FINANZSTROEME = [
    # --- 2024 ---
    # Energie-Kette (EAV = Ergebnisabführungsvertrag)
    (2024, "SWSZ_NETZ", "SWSZ", 336, "EAV_GEWINN",
     "Gewinnabführung SWSZ-Netz an SWSZ"),
    (2024, "SWSZ", "SWB", 6548, "EAV_GEWINN",
     "Ergebnisabführung SWSZ an SWB (inkl. Steuerumlage)"),
    (2024, "SWB", "CCS", 4052, "EAV_GEWINN",
     "Gewinnabführung SWB an CCS (brutto vor Minderheitsausgleich)"),
    # Minderheitsbeteiligung LSIM (38,08% SWB → Ausgleich aus CCS)
    (2024, "CCS", "LSIM_EXTERN", 1087, "AUSGLEICH_MINDERHEIT",
     "Ausgleichszahlung an LSIM (38,08% SWB-Anteil Stadt Zella-Mehlis)"),
    # CCS übernimmt SNG-Verlust
    (2024, "CCS", "SNG", 2852, "VERLUSTUEBERNAHME",
     "Verlustübernahme CCS für SNG (EAV, ÖPNV-Quersubvention)"),
    # Staatliche Beihilfen an SNG
    (2024, "THUERINGEN", "SNG", 763, "BEIHILFE",
     "Betriebskostenzuschuss Freistaat Thüringen"),
    (2024, "BUND", "SNG", 152, "BEIHILFE",
     "Finanzhilfe Kraftstoffpreisentwicklung Bund"),
    # Direktzuschüsse Stadt
    (2024, "STADT", "SNG", 600, "ZUSCHUSS",
     "Direktzuschuss Stadt Suhl an SNG"),
    (2024, "STADT", "EBKDS", 11529, "ZUSCHUSS",
     "Pflichtbetriebskostenzuschuss EB KDS (Straßen, Abfall, Grünflächen)"),
    (2024, "STADT", "SSZ", 325, "ZUSCHUSS",
     "Zuschuss Stadt Suhl an Schießsportzentrum"),
    # Rückflüsse → Stadt
    (2024, "ITM", "STADT", 300, "AUSSCHUETTUNG",
     "Gewinnausschüttung ITM gGmbH (50,93% Anteil Stadt Suhl)"),
    (2024, "GEWO", "STADT", 150, "AUSSCHUETTUNG",
     "Gewinnausschüttung GeWo (100% Anteil Stadt Suhl)"),

    # --- 2023 ---
    (2023, "SWSZ_NETZ", "SWSZ", 1776, "EAV_GEWINN",
     "Gewinnabführung SWSZ-Netz an SWSZ"),
    (2023, "SWSZ", "SWB", 9083, "EAV_GEWINN",
     "Ergebnisabführung SWSZ an SWB (inkl. Steuerumlage)"),
    (2023, "SWB", "CCS", 6270, "EAV_GEWINN",
     "Gewinnabführung SWB an CCS"),
    (2023, "CCS", "LSIM_EXTERN", None, "AUSGLEICH_MINDERHEIT",
     "Ausgleichszahlung an LSIM (2023, Betrag nicht separat ausgewiesen)"),
    (2023, "CCS", "SNG", 2747, "VERLUSTUEBERNAHME",
     "Verlustübernahme CCS für SNG"),
    (2023, "THUERINGEN", "SNG", 683, "BEIHILFE",
     "Betriebskostenzuschuss Freistaat Thüringen"),
    (2023, "BUND", "SNG", 241, "BEIHILFE",
     "ÖPNV-Rettungsschirm Corona-Hilfen + Kraftstoffilfe"),
    (2023, "STADT", "EBKDS", 14267, "ZUSCHUSS",
     "Betriebskostenzuschuss EB KDS 2023"),
    (2023, "STADT", "SSZ", 310, "ZUSCHUSS",
     "Zuschuss Stadt Suhl an Schießsportzentrum 2023"),
    (2023, "GEWO", "STADT", 250, "AUSSCHUETTUNG",
     "Gewinnausschüttung GeWo 2023"),
    (2023, "ITM", "STADT", 0, "AUSSCHUETTUNG",
     "Gewinnausschüttung ITM 2023 (keine Ausschüttung)"),
]

# ---------------------------------------------------------------------------
# DB-Operationen
# ---------------------------------------------------------------------------

def setup_tables(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS beteiligungen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kuerzel TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        typ TEXT NOT NULL,
        beteiligung_direkt REAL,
        beteiligung_indirekt REAL,
        via_kuerzel TEXT,
        stammkapital_eur REAL,
        gruendungsjahr INTEGER,
        sektor TEXT,
        status TEXT DEFAULT 'aktiv',
        oeffentlicher_zweck TEXT
    );

    CREATE TABLE IF NOT EXISTS beteiligungen_kennzahlen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        beteiligung_id INTEGER NOT NULL REFERENCES beteiligungen(id),
        jahr INTEGER NOT NULL,
        umsatz_teur REAL,
        jahresergebnis_teur REAL,
        jahresergebnis_nach_eav_teur REAL,
        bilanzsumme_teur REAL,
        eigenkapital_teur REAL,
        verbindlichkeiten_teur REAL,
        investitionen_teur REAL,
        mitarbeiter INTEGER,
        UNIQUE(beteiligung_id, jahr)
    );

    CREATE TABLE IF NOT EXISTS finanzstroeme (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        jahr INTEGER NOT NULL,
        von_kuerzel TEXT NOT NULL,
        nach_kuerzel TEXT NOT NULL,
        betrag_teur REAL,
        typ TEXT NOT NULL,
        bezeichnung TEXT
    );
    """)
    conn.commit()
    print("Tabellen erstellt/geprüft.")


def insert_beteiligungen(conn):
    conn.execute("DELETE FROM beteiligungen")
    conn.executemany("""
        INSERT INTO beteiligungen
            (kuerzel, name, typ, beteiligung_direkt, beteiligung_indirekt,
             via_kuerzel, stammkapital_eur, gruendungsjahr, sektor, status,
             oeffentlicher_zweck)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, BETEILIGUNGEN)
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM beteiligungen").fetchone()[0]
    print(f"Beteiligungen: {n} Einträge")


def insert_kennzahlen(conn):
    conn.execute("DELETE FROM beteiligungen_kennzahlen")
    for row in KENNZAHLEN:
        kuerzel, jahr, umsatz, je, je_eav, bs, ek, vb, inv, ma = row
        bid = conn.execute(
            "SELECT id FROM beteiligungen WHERE kuerzel=?", (kuerzel,)
        ).fetchone()
        if not bid:
            print(f"WARNUNG: Kuerzel {kuerzel} nicht gefunden!")
            continue
        conn.execute("""
            INSERT OR REPLACE INTO beteiligungen_kennzahlen
                (beteiligung_id, jahr, umsatz_teur, jahresergebnis_teur,
                 jahresergebnis_nach_eav_teur, bilanzsumme_teur, eigenkapital_teur,
                 verbindlichkeiten_teur, investitionen_teur, mitarbeiter)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (bid[0], jahr, umsatz, je, je_eav, bs, ek, vb, inv, ma))
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM beteiligungen_kennzahlen").fetchone()[0]
    print(f"Kennzahlen: {n} Einträge")


def insert_finanzstroeme(conn):
    conn.execute("DELETE FROM finanzstroeme")
    conn.executemany("""
        INSERT INTO finanzstroeme
            (jahr, von_kuerzel, nach_kuerzel, betrag_teur, typ, bezeichnung)
        VALUES (?,?,?,?,?,?)
    """, FINANZSTROEME)
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM finanzstroeme").fetchone()[0]
    print(f"Finanzströme: {n} Einträge")


def run():
    print(f"DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    setup_tables(conn)
    insert_beteiligungen(conn)
    insert_kennzahlen(conn)
    insert_finanzstroeme(conn)
    conn.close()
    print("Fertig.")


if __name__ == "__main__":
    run()
