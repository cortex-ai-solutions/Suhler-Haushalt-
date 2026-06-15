"""
pipeline_zweckverband.py
Befüllt zweckverbände-Tabelle aus Beteiligungsbericht GJ 2024 S. 80-86.
"""
import sqlite3

DB = "suhl_haushalt_2025.db"

# Kategorien: WASSER, ABFALL, RETTUNG, ENERGIE, SONSTIGES
VERBÄNDE = [
    # (nr, kuerzel, name, kategorie, adresse, anmerkung)
    (1, "ZV-MR",
     "ZV Wasser und Abwasser 'Mittlerer Rennsteig' Suhl",
     "WASSER",
     "Am Schießstand 30, 98544 Zella-Mehlis",
     "Trinkwasserversorgung und Abwasserbeseitigung für Suhl und 15 Gemeinden; Suhl = Gründungsmitglied"),
    (2, "FWZV",
     "Fernwasserzweckverband Südthüringen",
     "WASSER",
     "Gabeler Straße 41, 98667 Schönbrunn",
     "Gewinnung und Lieferung von Trinkwasser an Verbandsmitglieder; Suhl über ZV Mittlerer Rennsteig"),
    (3, "WAV-OG",
     "Wasser- und Abwasserzweckverband 'Obere Gera'",
     "WASSER",
     "An der Glashütte 3, 99330 Gräfenroda",
     "Trinkwasserversorgung und Abwasserbeseitigung; Stadt Suhl mit OT Gehlberg beteiligt"),
    (4, "WAV-ILM",
     "ZV Wasser- und Abwasserverband Ilmenau",
     "WASSER",
     "Naumannstraße 21, 98693 Ilmenau",
     "Trink-/Brauchwasserversorgung und Abwasserbeseitigung; Stadt Suhl mit OT Schmiedefeld"),
    (5, "GUV-HLW",
     "Gewässerunterhaltungsverband Hasel/Lauter/Werra",
     "GEWAESSER",
     "3. Tongraben 2a, 98617 Meiningen",
     "Unterhaltung Gewässer II. Ordnung; Stadt Suhl (gesamtes Stadtgebiet) ist Mitglied"),
    (6, "GUV-OWS",
     "Gewässerunterhaltungsverband Obere Werra/Schleuse",
     "GEWAESSER",
     "Birkenfelder Straße 16a, 98646 Hildburghausen",
     "Unterhaltung Gewässer II. Ordnung; Stadt Suhl mit OT Schmiedefeld und Vesser"),
    (7, "GUV-GAI",
     "Gewässerunterhaltungsverband Gera/Apfelstädt/Obere Ilm",
     "GEWAESSER",
     "Feldstraße 23, 99334 Amt Wachsenburg/OT Ichtershausen",
     "Unterhaltung Gewässer II. Ordnung; Stadt Suhl mit OT Gehlberg"),
    (8, "RDZ-ST",
     "Rettungsdienstzweckverband Südthüringen",
     "RETTUNG",
     "Rennsteigstraße 10, 98544 Zella-Mehlis",
     "Bodengebundener Rettungsdienst + Zentrale Leitstelle; Mitglieder: Suhl (34.685 EW), LK Hildburghausen, LK Sonneberg"),
    (9, "SPK-ZV",
     "Sparkassenzweckverband 'Rhön-Rennsteig'",
     "SONSTIGES",
     "Leipziger Straße 4, 98617 Meiningen",
     "Träger der Zweckverbandssparkasse; LK Schmalkalden-Meiningen 2/3, Stadt Suhl 1/3 Haftung"),
    (10, "ZAST",
     "ZV für Abfallwirtschaft Südwestthüringen (ZASt)",
     "ABFALL",
     "Am Schießstand 15, 98544 Zella-Mehlis",
     "Abfallentsorgung, Restabfallbehandlung, Deponien; Mitglieder: Suhl, LK Hildburghausen, LK Sonneberg u.a."),
    (11, "ZV-TKB",
     "ZV Tierkörperbeseitigung Thüringen",
     "SONSTIGES",
     "c/o Landratsamt Greiz, Dr. Rathenau-Platz 11, 07973 Greiz",
     "Aufgabenträger für Tierkörperbeseitigung nach ThürTierNebG; alle Landkreise und kreisfreien Städte Thüringens"),
    (12, "KET",
     "Kommunaler Energiezweckverband Thüringen (KET)",
     "ENERGIE",
     "Alfred-Hess-Straße 37, 99094 Erfurt",
     "Kommunale Strom-/Gas-/Fernwärme-/Breitbandversorgung; Beteiligungen KEBT AG + Thüringer Energie AG; Stadt Suhl mit OT Schmiedefeld und Gehlberg"),
    (13, "KISA",
     "KISA Kommunale Informationsverarbeitung Sachsen",
     "ENERGIE",
     "Eilenburger Straße 1a, 04317 Leipzig",
     "Datennetz und IT-Dienste für Kommunen; Stadt Suhl beigetreten zum 31.12.2021"),
]


def run():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS zweckverbände (
            id         INTEGER PRIMARY KEY,
            nr         INTEGER NOT NULL,
            kuerzel    TEXT NOT NULL,
            name       TEXT NOT NULL,
            kategorie  TEXT NOT NULL,
            adresse    TEXT,
            anmerkung  TEXT
        )
    """)
    con.execute("DELETE FROM zweckverbände")
    con.executemany(
        "INSERT INTO zweckverbände (nr, kuerzel, name, kategorie, adresse, anmerkung) "
        "VALUES (?,?,?,?,?,?)",
        VERBÄNDE
    )
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM zweckverbände").fetchone()[0]
    print(f"zweckverbände: {n} Eintraege eingefuegt.")

    # Kategorien-Übersicht
    cats = con.execute("SELECT kategorie, COUNT(*) FROM zweckverbände GROUP BY kategorie").fetchall()
    for c in cats:
        print(f"  {c[0]:12s}: {c[1]}")
    con.close()


if __name__ == "__main__":
    run()
