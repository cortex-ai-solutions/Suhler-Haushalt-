"""
pipeline_schulden.py
Befüllt schulden_entwicklung aus HH-Plan 2025 S. 83.
Keine Neuverschuldung seit 2013; 2025/2026 = Planwerte.
"""
import sqlite3

DB = "suhl_haushalt_2025.db"

SCHULDEN = [
    # (jahr, schuldenstand_teur, einwohner, prokopf_eur, ist_prognose)
    (2013, 54419,  36570, 1488, 0),
    (2014, 20903,  35967,  581, 0),
    (2015, 19857,  35665,  557, 0),
    (2016, 18937,  36208,  523, 0),
    (2017, 16277,  36778,  443, 0),
    (2018, 14213,  35608,  399, 0),
    (2019, 14218,  37321,  381, 0),
    (2020, 12060,  36955,  326, 0),
    (2021,  9949,  36789,  270, 0),
    (2022,  7657,  36395,  210, 0),
    (2023,  5739,  36054,  159, 0),
    (2024,  3846,  37009,  104, 0),
    (2025,  2020,  36307,   56, 1),  # voraussichtlich
    (2026,   202,  34685,    6, 1),  # voraussichtlich
]

def run():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS schulden_entwicklung (
            id            INTEGER PRIMARY KEY,
            jahr          INTEGER NOT NULL UNIQUE,
            schuldenstand_teur REAL NOT NULL,
            einwohner     INTEGER,
            prokopf_eur   REAL,
            ist_prognose  INTEGER NOT NULL DEFAULT 0
        )
    """)
    con.execute("DELETE FROM schulden_entwicklung")
    con.executemany(
        "INSERT INTO schulden_entwicklung (jahr, schuldenstand_teur, einwohner, prokopf_eur, ist_prognose) "
        "VALUES (?,?,?,?,?)",
        SCHULDEN
    )
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM schulden_entwicklung").fetchone()[0]
    print(f"schulden_entwicklung: {n} Eintraege eingefuegt.")
    con.close()

if __name__ == "__main__":
    run()
