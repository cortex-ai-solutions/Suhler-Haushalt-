"""
setup_database.py
Schritt 1+2+4: DB-Initialisierung, Stammdaten-Seeding, View-Erstellung
Haushalt Suhl 2025 - Datenbankgerüst
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "suhl_haushalt_2025.db")

DDL = """
PRAGMA foreign_keys = ON;

-- DIME_6: Rechtliche Steuerungskategorien (neu, muss zuerst existieren)
CREATE TABLE IF NOT EXISTS steuerungs_kategorien (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    bezeichnung TEXT NOT NULL,
    ebene_zustaendigkeit TEXT NOT NULL,
    beschreibung TEXT
);

-- DIME_1: Institutionelle Struktur (Organigramm / Dezernate)
CREATE TABLE IF NOT EXISTS teilplaene (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nummer TEXT UNIQUE NOT NULL,
    bezeichnung TEXT NOT NULL
);

-- DIME_2: Makroökonomische Zuordnung (Produktbereiche)
CREATE TABLE IF NOT EXISTS hauptproduktbereiche (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nummer TEXT UNIQUE NOT NULL,
    bezeichnung TEXT NOT NULL
);

-- DIME_4: Doppik-Steuerung (Kontenklassen)
CREATE TABLE IF NOT EXISTS kontenklassen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nummer INTEGER UNIQUE NOT NULL,
    bezeichnung TEXT NOT NULL,
    rechnungstyp TEXT NOT NULL
);

-- DIME_5: Kommunaler Kontenrahmen (Sachkonten)
CREATE TABLE IF NOT EXISTS konten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    konto_nummer TEXT UNIQUE NOT NULL,
    bezeichnung TEXT NOT NULL,
    kontenklasse_id INTEGER,
    FOREIGN KEY(kontenklasse_id) REFERENCES kontenklassen(id)
);

-- DIME_3: Funktionale Struktur (Produkte & Leistungen)
CREATE TABLE IF NOT EXISTS produkte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produkt_nummer TEXT UNIQUE NOT NULL,
    bezeichnung TEXT NOT NULL,
    teilplan_id INTEGER,
    hauptproduktbereich_id INTEGER,
    steuerungs_kategorie_id INTEGER,
    rechtsgrundlage TEXT,
    FOREIGN KEY(teilplan_id) REFERENCES teilplaene(id),
    FOREIGN KEY(hauptproduktbereich_id) REFERENCES hauptproduktbereiche(id),
    FOREIGN KEY(steuerungs_kategorie_id) REFERENCES steuerungs_kategorien(id)
);

-- FAKTEN: Haushaltswerte (Plan-Ansätze, Ist-Werte, Finanzplanung)
CREATE TABLE IF NOT EXISTS haushaltswerte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    haushaltsplan_jahr INTEGER NOT NULL,
    daten_jahr INTEGER NOT NULL,
    wert_typ TEXT NOT NULL,
    produkt_id INTEGER,
    konto_id INTEGER,
    betrag REAL NOT NULL,
    FOREIGN KEY(produkt_id) REFERENCES produkte(id),
    FOREIGN KEY(konto_id) REFERENCES konten(id),
    UNIQUE(produkt_id, konto_id, haushaltsplan_jahr, daten_jahr, wert_typ)
);
"""

VIEW_SQL = """
DROP VIEW IF EXISTS view_dashboard_flach;
CREATE VIEW view_dashboard_flach AS
SELECT
    h.haushaltsplan_jahr,
    h.daten_jahr,
    h.wert_typ,
    h.betrag,
    t.nummer  AS teilplan_nummer,
    t.bezeichnung AS teilplan,
    hpb.nummer AS hauptproduktbereich_nummer,
    hpb.bezeichnung AS hauptproduktbereich,
    p.produkt_nummer,
    p.bezeichnung AS produkt,
    p.rechtsgrundlage,
    sk.code   AS steuerungs_code,
    sk.bezeichnung AS steuerungs_bezeichnung,
    sk.ebene_zustaendigkeit,
    k.konto_nummer,
    k.bezeichnung AS konto,
    kk.nummer AS kontenklasse_nummer,
    kk.bezeichnung AS kontenklasse,
    kk.rechnungstyp
FROM haushaltswerte h
JOIN produkte p           ON h.produkt_id = p.id
JOIN teilplaene t         ON p.teilplan_id = t.id
JOIN hauptproduktbereiche hpb ON p.hauptproduktbereich_id = hpb.id
LEFT JOIN steuerungs_kategorien sk ON p.steuerungs_kategorie_id = sk.id
JOIN konten k             ON h.konto_id = k.id
JOIN kontenklassen kk     ON k.kontenklasse_id = kk.id;
"""

STEUERUNGS_KATEGORIEN = [
    (
        "FREIWILLIG",
        "Freiwillige Selbstverwaltungsaufgabe",
        "STADTRAT",
        "Die Stadt erbringt diese Leistung auf freiwilliger Basis. Der Stadtrat "
        "hat volle Entscheidungsfreiheit über Umfang, Standard und Fortbestand. "
        "Kürzungen oder Einstellungen sind ohne rechtliche Einschränkungen möglich.",
    ),
    (
        "PFLICHT_ERMESSEN",
        "Pflichtaufgabe mit kommunalem Ermessensspielraum",
        "STADTRAT",
        "Die Stadt muss diese Aufgabe erfüllen (gesetzliche Pflicht), besitzt "
        "jedoch erheblichen Ermessensspielraum bei Umfang, Qualität, "
        "Organisationsform und Finanzierungshöhe. Steuerung über Satzungen, "
        "Richtlinien und Förderbedingungen möglich.",
    ),
    (
        "PFLICHT_STRIKT",
        "Strikte Pflichtaufgabe (gebundene Entscheidung)",
        "BUND_LAND",
        "Individuell einklagbarer Rechtsanspruch oder zwingende gesetzliche "
        "Verpflichtung ohne kommunalen Ermessensspielraum. Leistungsverweigerung "
        "führt zu Klagen und Aufsichtsmaßnahmen. Budget folgt dem Bedarf, "
        "nicht umgekehrt.",
    ),
    (
        "UEBERTRAGEN",
        "Übertragene Aufgabe (Auftragsangelegenheit)",
        "LAND",
        "Aufgabe wurde durch Bundes- oder Landesgesetz auf die Stadt übertragen "
        "(Konnexitätsprinzip). Das Land erstattet die Kosten ganz oder teilweise. "
        "Die Stadt handelt als Erfüllungsgehilfe des Landes; Ermessen nur im "
        "Rahmen der Übertragungsvorschriften.",
    ),
]

KONTENKLASSEN = [
    (0, "Aktiva",                   "BILANZ"),
    (1, "Passiva",                  "BILANZ"),
    (2, "Sonderposten",             "BILANZ"),
    (3, "Rechnungsabgrenzung",      "BILANZ"),
    (4, "Erträge",                  "ERGEBNIS"),
    (5, "Aufwendungen",             "ERGEBNIS"),
    (6, "Einzahlungen",             "FINANZ"),
    (7, "Auszahlungen",             "FINANZ"),
]

HAUPTPRODUKTBEREICHE = [
    ("1", "Zentrale Verwaltung"),
    ("2", "Schule und Kultur"),
    ("3", "Soziales und Jugend"),
    ("4", "Gesundheit und Sport"),
    ("5", "Gestaltung Umwelt und Infrastruktur"),
    ("6", "Wirtschaft und Tourismus"),
]

# 12 Teilpläne – die vollständigen Bezeichnungen sind aus dem PDF zu verifizieren.
# Mit TODO markierte Einträge sind vorläufige Platzhalter.
TEILPLAENE = [
    ("01", "Zentrale Verwaltung und Steuerung"),
    ("02", "Sicherheit und Ordnung"),
    ("03", "Schulen"),
    ("04", "Kultur, Tourismus und Sport"),
    ("05", "Soziales"),       # TODO: aus PDF verifizieren
    ("06", "Jugend und Familie"),   # TODO: aus PDF verifizieren
    ("07", "Gesundheit"),           # TODO: aus PDF verifizieren
    ("08", "Stadtentwicklung und Bau"),  # TODO: aus PDF verifizieren
    ("09", "Straßen und Umwelt"),   # TODO: aus PDF verifizieren
    ("10", "Wirtschaft und Liegenschaften"),  # TODO: aus PDF verifizieren
    ("11", "Technische Dienste / Bauhof"),    # TODO: aus PDF verifizieren
    ("12", "Eigenbetriebe und Sonstiges"),    # TODO: aus PDF verifizieren
]


DDL_STELLENPLAN = """
CREATE TABLE IF NOT EXISTS besoldungsgruppen (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kuerzel     TEXT UNIQUE NOT NULL,
    typ         TEXT NOT NULL CHECK(typ IN ('BEAMTE','TARIF')),
    beschreibung TEXT
);

CREATE TABLE IF NOT EXISTS stellenplan (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    teilplan_id          INTEGER NOT NULL,
    besoldungsgruppe_id  INTEGER NOT NULL,
    daten_jahr           INTEGER NOT NULL,
    wert_typ             TEXT NOT NULL CHECK(wert_typ IN ('PLAN_ANSATZ','IST')),
    planstellen          REAL NOT NULL,
    FOREIGN KEY(teilplan_id)         REFERENCES teilplaene(id),
    FOREIGN KEY(besoldungsgruppe_id) REFERENCES besoldungsgruppen(id),
    UNIQUE(teilplan_id, besoldungsgruppe_id, daten_jahr, wert_typ)
);
"""


def add_stellenplan_tables(con):
    con.executescript(DDL_STELLENPLAN)
    print("[OK] Stellenplan-Tabellen angelegt (besoldungsgruppen, stellenplan)")


def get_connection():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con


def create_tables(con):
    con.executescript(DDL)
    print("[OK] Tabellen angelegt (CREATE TABLE IF NOT EXISTS)")


def seed_steuerungs_kategorien(con):
    con.executemany(
        """INSERT OR IGNORE INTO steuerungs_kategorien
           (code, bezeichnung, ebene_zustaendigkeit, beschreibung)
           VALUES (?, ?, ?, ?)""",
        STEUERUNGS_KATEGORIEN,
    )
    count = con.execute("SELECT COUNT(*) FROM steuerungs_kategorien").fetchone()[0]
    print(f"✓ steuerungs_kategorien: {count} Einträge")


def seed_kontenklassen(con):
    con.executemany(
        """INSERT OR IGNORE INTO kontenklassen (nummer, bezeichnung, rechnungstyp)
           VALUES (?, ?, ?)""",
        KONTENKLASSEN,
    )
    count = con.execute("SELECT COUNT(*) FROM kontenklassen").fetchone()[0]
    print(f"✓ kontenklassen: {count} Einträge")


def seed_hauptproduktbereiche(con):
    con.executemany(
        """INSERT OR IGNORE INTO hauptproduktbereiche (nummer, bezeichnung)
           VALUES (?, ?)""",
        HAUPTPRODUKTBEREICHE,
    )
    count = con.execute("SELECT COUNT(*) FROM hauptproduktbereiche").fetchone()[0]
    print(f"✓ hauptproduktbereiche: {count} Einträge")


def seed_teilplaene(con):
    con.executemany(
        """INSERT OR IGNORE INTO teilplaene (nummer, bezeichnung) VALUES (?, ?)""",
        TEILPLAENE,
    )
    count = con.execute("SELECT COUNT(*) FROM teilplaene").fetchone()[0]
    print(f"✓ teilplaene: {count} Einträge (8 als TODO-Platzhalter markiert)")


def create_view(con):
    con.executescript(VIEW_SQL)
    print("✓ view_dashboard_flach erstellt")


def main():
    print(f"Datenbank: {DB_PATH}\n")
    con = get_connection()
    try:
        create_tables(con)
        seed_steuerungs_kategorien(con)
        seed_kontenklassen(con)
        seed_hauptproduktbereiche(con)
        seed_teilplaene(con)
        create_view(con)
        add_stellenplan_tables(con)
        con.commit()
        print("\n✓ setup_database.py erfolgreich abgeschlossen.")
    except Exception as exc:
        con.rollback()
        print(f"\n✗ Fehler: {exc}")
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
