"""
pipeline_stellenplan.py
Extrahiert Stellenplan-Daten aus dem Haushaltsplan 2025 PDF und schreibt sie
in die bestehende SQLite-DB (Tabellen besoldungsgruppen + stellenplan).

Seiten 893–898 des PDFs enthalten:
  Seite 893: TP01 (Verwaltungsführung), TP02 (Kultur/Tourismus/Sport)
  Seite 894: TP03 (Personal/Zentrale Dienste), TP04 (Finanzverwaltung)
  Seite 895: TP07 (Ordnung und Sicherheit)
  Seite 896: TP08 (Umwelt)
  Seite 897: TP09 (Soziales/Gesundheit), TP10 (Schulträger)
  Seite 898: TP11 (KJF), TP12 (Einrichtungen Sozialdezernat)

Spalten im Stellenplan 2025:
  - "Stellen für das Haushaltsjahr 2025" → daten_jahr=2025, wert_typ=PLAN_ANSATZ
  - "Soll 2024"                          → daten_jahr=2024, wert_typ=PLAN_ANSATZ
  - "Ist 30.06.2024"                     → daten_jahr=2024, wert_typ=IST

TP05 (Öfftl. Flächen) und TP06 (Allg. Finanzwirtschaft) haben keinen eigenen
Stellenplan-Abschnitt (werden durch Eigenbetrieb KDS abgebildet).
"""

import fitz  # PyMuPDF
import re
import sqlite3
import os
import sys
from setup_database import DB_PATH, add_stellenplan_tables

PDF_PATH = os.path.join(os.path.dirname(__file__), "knowledge", "HH-Plan Stadt Suhl 2025.pdf")

# 0-indexed Seitenbereiche im Haupt-PDF (Seiten 893–898)
STELLENPLAN_PAGES = list(range(892, 898))

# Nach Normierung (Leerzeichen entfernt) passende Besoldungs-/Entgeltgruppen
GRUPPE_RE = re.compile(
    r'^([AB]\d+Z?|[AE]\d+[a-z]?|S\d+[a-zA-Z]?)$'
)
NUMBER_RE = re.compile(r'^\d+[.,]\d+$')

# Leerzeichen-Normierung, z. B. "A 16" → "A16", "E 9a" → "E9a"
def norm(s: str) -> str:
    return s.replace(" ", "").strip()


def typ_from_kuerzel(k: str) -> str:
    return "BEAMTE" if k[0] in ("A", "B") else "TARIF"


BESCHREIBUNG = {
    "A": "Beamte – allg. Verwaltungs- oder techn. Dienst",
    "B": "Beamte – höherer Dienst / Leitungsfunktionen (Wahlbeamte)",
    "E": "Tarifbeschäftigte TVöD",
    "S": "Tarifbeschäftigte – Sozial- und Erziehungsdienst (TVöD-SuE)",
}


def parse_stellenplan_pdf() -> list[tuple]:
    """
    Liest den Stellenplan-Abschnitt aus dem Haupt-PDF und gibt eine Liste von
    Tupeln zurück:
      (tp_nr, kuerzel, plan_2025, soll_2024, ist_2024)
    wobei alle Zahlenwerte float (oder None bei fehlendem Wert) sind.
    """
    doc = fitz.open(PDF_PATH)
    entries = []

    current_tp = None       # z. B. "01", "07"
    current_typ = None      # "BEAMTE" | "TARIF"

    # Zeilen überspringen, die Summen oder Textblöcke ankündigen
    SKIP_PREFIXES = (
        "Summe", "A. Verwaltung", "Bes.-", "Zahl der", "Vermerke",
        "Gruppe", "Stellen für", "Entgeltgruppe lt.", "Vorjahreswerte",
        "Wahlbeamte", "Höherer", "Gehobener", "Mittlerer",
        "k. w.", "Vollzug", "\"", "Seite ", "Übersicht",
        "Stellenplan", "Haushaltsjahr", "Soll", "Ist ",
        "Arbeitnehmer\n",
    )

    for pg_idx in STELLENPLAN_PAGES:
        txt = doc[pg_idx].get_text()
        lines = [l.strip() for l in txt.split("\n") if l.strip()]

        i = 0
        while i < len(lines):
            line = lines[i]

            # ── TP-Kopfzeile erkennen ─────────────────────────────────────
            if "Teilplan" in line:
                m = re.search(r"Teilplan\s+(\d+)", line)
                if m:
                    new_tp = m.group(1).zfill(2)
                    # Nur vorwärts wechseln, nie rückwärts (verhindert
                    # doppelte TP11-Kopfzeile am Ende von Seite 898)
                    if current_tp is None or int(new_tp) > int(current_tp):
                        current_tp = new_tp
                        current_typ = None
                i += 1
                continue

            # ── Typ-Abschnitt: Beamte / Arbeitnehmer ─────────────────────
            if re.match(r"^1\.\s*Beamte", line):
                current_typ = "BEAMTE"
                i += 1
                continue
            if re.match(r"^2\.\s*Arbeitnehmer", line):
                current_typ = "TARIF"
                i += 1
                continue
            # Manche TPs haben nur Arbeitnehmer ohne "2." Präfix
            if line == "Arbeitnehmer":
                current_typ = "TARIF"
                i += 1
                continue

            # ── Überspringe bekannte Nicht-Daten-Zeilen ───────────────────
            if any(line.startswith(p) for p in SKIP_PREFIXES):
                i += 1
                continue

            # ── Gruppe erkennen ───────────────────────────────────────────
            normed = norm(line)
            if GRUPPE_RE.match(normed) and current_tp and current_typ:
                kuerzel = normed

                # Sammle bis zu 3 Zahlenwerte ab der nächsten Zeile
                nums = []
                j = i + 1
                while j < len(lines) and len(nums) < 3:
                    nxt = lines[j].strip()
                    if NUMBER_RE.match(nxt):
                        nums.append(float(nxt.replace(",", ".")))
                        j += 1
                    elif any(nxt.startswith(p) for p in SKIP_PREFIXES):
                        j += 1  # kw-Vermerke o. ä. überspringen
                    elif not nxt:
                        j += 1
                    else:
                        break  # unbekannte Zeile → Nummernsammlung abbrechen

                if nums:
                    plan_2025 = nums[0] if len(nums) > 0 else None
                    soll_2024 = nums[1] if len(nums) > 1 else None
                    ist_2024  = nums[2] if len(nums) > 2 else None
                    entries.append(
                        (current_tp, kuerzel, plan_2025, soll_2024, ist_2024)
                    )
                i = j
                continue

            i += 1

    doc.close()
    return entries


def insert_into_db(entries: list[tuple]) -> None:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")

    # Sicherstellen, dass Tabellen existieren
    add_stellenplan_tables(con)
    con.commit()

    # Teilpläne-Lookup
    tp_map = {
        r["nummer"]: r["id"]
        for r in con.execute("SELECT id, nummer FROM teilplaene")
    }

    # Besoldungsgruppen upsert + Cache
    bg_cache: dict[str, int] = {}

    def get_or_create_bg(kuerzel: str) -> int:
        if kuerzel in bg_cache:
            return bg_cache[kuerzel]
        typ = typ_from_kuerzel(kuerzel)
        bez = BESCHREIBUNG.get(kuerzel[0], "Tarifbeschäftigte")
        con.execute(
            "INSERT OR IGNORE INTO besoldungsgruppen (kuerzel, typ, beschreibung) VALUES (?,?,?)",
            (kuerzel, typ, bez),
        )
        bg_id = con.execute(
            "SELECT id FROM besoldungsgruppen WHERE kuerzel = ?", (kuerzel,)
        ).fetchone()["id"]
        bg_cache[kuerzel] = bg_id
        return bg_id

    inserted = skipped = 0

    for tp_nr, kuerzel, plan_2025, soll_2024, ist_2024 in entries:
        tp_id = tp_map.get(tp_nr)
        if tp_id is None:
            print(f"  [WARN] TP{tp_nr} nicht in DB — überspringe", file=sys.stderr)
            skipped += 1
            continue
        bg_id = get_or_create_bg(kuerzel)

        rows = []
        if plan_2025 is not None:
            rows.append((tp_id, bg_id, 2025, "PLAN_ANSATZ", plan_2025))
        if soll_2024 is not None:
            rows.append((tp_id, bg_id, 2024, "PLAN_ANSATZ", soll_2024))
        if ist_2024 is not None:
            rows.append((tp_id, bg_id, 2024, "IST",         ist_2024))

        for row in rows:
            try:
                con.execute(
                    """INSERT OR REPLACE INTO stellenplan
                       (teilplan_id, besoldungsgruppe_id, daten_jahr, wert_typ, planstellen)
                       VALUES (?,?,?,?,?)""",
                    row,
                )
                inserted += 1
            except sqlite3.IntegrityError as e:
                print(f"  [ERR] {tp_nr}/{kuerzel}: {e}", file=sys.stderr)
                skipped += 1

    con.commit()
    con.close()

    print(f"\n  Datensätze eingefügt : {inserted}")
    print(f"  Übersprungen/Fehler  : {skipped}")


def print_summary() -> None:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    print("\n=== Stellenplan-Zusammenfassung ===")
    for row in con.execute("""
        SELECT s.daten_jahr, s.wert_typ,
               t.typ,
               SUM(s.planstellen) AS summe,
               COUNT(*) AS zeilen
        FROM stellenplan s
        JOIN besoldungsgruppen t ON s.besoldungsgruppe_id = t.id
        GROUP BY s.daten_jahr, s.wert_typ, t.typ
        ORDER BY s.daten_jahr, s.wert_typ, t.typ
    """):
        print(
            f"  {row['daten_jahr']} | {row['wert_typ']:<12} | "
            f"{row['typ']:<6} | {row['summe']:>8.3f} Stellen | {row['zeilen']:>3} Zeilen"
        )

    print("\n=== Stellen je Teilplan (Plan 2025) ===")
    for row in con.execute("""
        SELECT tp.nummer, tp.bezeichnung,
               SUM(CASE WHEN bg.typ='BEAMTE' THEN s.planstellen ELSE 0 END) AS beamte,
               SUM(CASE WHEN bg.typ='TARIF'  THEN s.planstellen ELSE 0 END) AS tarif,
               SUM(s.planstellen) AS gesamt
        FROM stellenplan s
        JOIN teilplaene tp ON s.teilplan_id = tp.id
        JOIN besoldungsgruppen bg ON s.besoldungsgruppe_id = bg.id
        WHERE s.daten_jahr = 2025 AND s.wert_typ = 'PLAN_ANSATZ'
        GROUP BY tp.nummer, tp.bezeichnung
        ORDER BY tp.nummer
    """):
        print(
            f"  TP{row['nummer']}  Beamte: {row['beamte']:>6.3f}  "
            f"Tarif: {row['tarif']:>7.3f}  Gesamt: {row['gesamt']:>8.3f}"
        )

    totals = con.execute("""
        SELECT
          SUM(CASE WHEN bg.typ='BEAMTE' THEN s.planstellen ELSE 0 END) AS beamte,
          SUM(CASE WHEN bg.typ='TARIF'  THEN s.planstellen ELSE 0 END) AS tarif,
          SUM(s.planstellen) AS gesamt
        FROM stellenplan s
        JOIN besoldungsgruppen bg ON s.besoldungsgruppe_id = bg.id
        WHERE s.daten_jahr = 2025 AND s.wert_typ = 'PLAN_ANSATZ'
    """).fetchone()
    print(
        f"\n  GESAMT  Beamte: {totals['beamte']:>6.3f}  "
        f"Tarif: {totals['tarif']:>7.3f}  Gesamt: {totals['gesamt']:>8.3f}"
    )
    print(f"  (Soll laut PDF: Beamte 77,000 | Arbeitnehmer 413,238 | Gesamt 490,238)")

    con.close()


def main() -> None:
    print(f"PDF  : {PDF_PATH}")
    print(f"DB   : {DB_PATH}")
    print(f"Seiten: {[p+1 for p in STELLENPLAN_PAGES]} (0-indiziert: {STELLENPLAN_PAGES})\n")

    print("1. Parsing PDF...")
    entries = parse_stellenplan_pdf()
    print(f"   {len(entries)} Rohdaten-Zeilen extrahiert")

    # Aggregation: gleiche Gruppe im selben TP summieren
    # (z. B. TP07 hat A13-Beamte UND A13-Feuerwehr → sum statt last-wins)
    from collections import defaultdict
    agg: dict[tuple, list] = defaultdict(lambda: [0.0, 0.0, 0.0])
    for tp_nr, kuerzel, p25, s24, i24 in entries:
        key = (tp_nr, kuerzel)
        agg[key][0] += p25 or 0.0
        agg[key][1] += s24 or 0.0
        agg[key][2] += i24 or 0.0
    entries_dedup = [(tp, kg, v[0], v[1], v[2]) for (tp, kg), v in agg.items()]
    print(f"   {len(entries_dedup)} nach Aggregation (je TP+Gruppe, Stellen summiert)")

    print("\n2. Einlesen in DB...")
    insert_into_db(entries_dedup)

    print("\n3. Validierung...")
    print_summary()


if __name__ == "__main__":
    main()
