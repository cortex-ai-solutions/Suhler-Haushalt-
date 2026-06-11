"""
repair_2024_kk67.py — Repariert KK6/7-Daten fuer haushaltsplan_jahr=2024

Root Causes (bewiesen):
  1. GESAMT_FP_END_PAGE=40 → Seiten 42-52 wurden nie verarbeitet (164 Konten)
  2. x-Threshold 65 → Konten bei x=64.4 (jede zweite Seite) wurden nie erkannt (123 Konten)

Reparatur:
  1. Loescht alte unvollstaendige 2024-KK6/7-Daten (produkt_id=303)
  2. Liest pdf_chunks_2024/00_3_Gesamtproduktplan.pdf komplett neu
     mit GESAMT_FP_END_PAGE=51 und x>=60 statt x>=65
  3. Ground-Truth-Validierung gegen Haushaltssatzung 2024
"""
import gc
import re
import os
import sqlite3
from datetime import datetime

import pdfplumber

# ---------------------------------------------------------------------------
# Konfiguration 2024
# ---------------------------------------------------------------------------
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, "suhl_haushalt_2025.db")
PDF_PATH   = os.path.join(BASE_DIR, "pdf_chunks_2024", "00_3_Gesamtproduktplan.pdf")

HAUSHALTSPLAN_JAHR   = 2024
DUMMY_PRODUKT_NR     = "000000"
GESAMT_FP_START_PAGE = 26   # 0-basiert (= Seite 27 im Chunk)
GESAMT_FP_END_PAGE   = 51   # REPARIERT: war 40, jetzt alle 52 Seiten

# Spalten-Definitionen fuer 2024-Plan
# Hintergrund: Abwechselnde Seiten im 2024-PDF haben Konto-Code bei x=64.4 (statt 78.6).
# Auf diesen "Shifted"-Seiten sind auch die Datenspalten um ~14px nach links verschoben.
# Normal-Seiten (Konto x≈78-79): Standard-Boundaries
# Shifted-Seiten (Konto x≈64-65): Boundaries um 14px nach links verschoben
SHIFT_PX = 14  # Gemessen: 78.6 - 64.4 = 14.2px

COL_DEFS_BASE = [
    (228, 315, 2022, "IST_ERGEBNIS"),
    (315, 368, 2023, "ANSATZ_VORJAHR"),
    (368, 415, 2024, "PLAN_ANSATZ"),
    (415, 460, 2025, "FINANZPLANUNG"),
    (460, 503, 2026, "FINANZPLANUNG"),
    (503, 550, 2027, "FINANZPLANUNG"),
]

# Für Shifted-Seiten: alle Grenzen um SHIFT_PX nach links
COL_DEFS_SHIFTED = [
    (x_min - SHIFT_PX, x_max - SHIFT_PX, year, wt)
    for (x_min, x_max, year, wt) in COL_DEFS_BASE
]

PLAIN_KONTO_RE = re.compile(r"^(\d{7})$")

# Ground Truth aus Haushaltssatzung 2024 §1
GROUND_TRUTH_2024 = {
    (6, "PLAN_ANSATZ"): 130_067_620.00,
    (7, "PLAN_ANSATZ"): 129_150_490.00,
}

BATCH_SIZE = 500

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
CID_MAP = {
    "196": "Ae", "214": "Oe", "220": "Ue",
    "223": "ss", "228": "ae", "246": "oe", "252": "ue",
    "233": "e",  "176": "deg",
}

def decode_cid(text):
    return re.sub(r"\(cid:(\d+)\)", lambda m: CID_MAP.get(m.group(1), "?"), text)

def parse_german_number(s):
    s = s.strip().replace("\xa0", "").replace(" ", "")
    if not s or s in ("-", "–"):
        return 0.0
    if s == "0":
        return 0.0
    negative = s.endswith("-")
    if negative:
        s = s[:-1]
    s = s.replace(".", "").replace(",", ".")
    try:
        v = float(s)
        return -v if negative else v
    except ValueError:
        return None

def assign_col(x, shifted=False):
    col_defs = COL_DEFS_SHIFTED if shifted else COL_DEFS_BASE
    for x_min, x_max, year, wert_typ in col_defs:
        if x_min <= x < x_max:
            return year, wert_typ
    return None, None

# ---------------------------------------------------------------------------
# Seiten-Parser (identisch zu pipeline.py, aber x>=60 statt x>=65)
# ---------------------------------------------------------------------------
def extract_page(page, pg_label):
    try:
        words = page.extract_words(
            x_tolerance=3, y_tolerance=3,
            keep_blank_chars=False, use_text_flow=False,
        )
    except Exception as exc:
        print(f"  [WARN] {pg_label}: extract_words Fehler: {exc}")
        return []

    if not words:
        return []

    lines_dict = {}
    for w in words:
        y = round(w["top"])
        lines_dict.setdefault(y, []).append(w)

    line_list = [
        (y, sorted(lines_dict[y], key=lambda w: w["x0"]))
        for y in sorted(lines_dict)
    ]

    results = []
    pending = None
    pending_shifted = False
    empty_after_pending = 0

    for y, row in line_list:
        konto_match = None
        konto_x0 = None
        for w in row:
            x0r = round(w["x0"])
            # REPARIERT: 60 <= statt 65 <= (erfasst x=64.4)
            if 60 <= x0r <= 95:
                m = PLAIN_KONTO_RE.match(w["text"])
                # Laufende KK6/7 (62-67, 72-77) + KK7-Finanzierung (79xxxx)
                # Investive 68/78 kommen aus TP-Chunks; 69xxxx per §1 = 0 (Durchlaufende)
                if m and w["text"][0] in ("6", "7") and w["text"][:2] not in ("68", "69", "78"):
                    konto_match = m
                    konto_x0 = w["x0"]
                break

        if konto_match:
            # Seiten-Typ: Konto bei x≈64 → shifted, bei x≈78 → normal
            is_shifted = konto_x0 < 72
            konto_bez = " ".join(
                decode_cid(w["text"])
                for w in row
                if round(w["x0"]) > 100 and assign_col(round(w["x0"]), is_shifted)[0] is None
            )
            same_line_values = {}
            for w in row:
                year, wert_typ = assign_col(round(w["x0"]), is_shifted)
                if year is not None:
                    v = parse_german_number(w["text"])
                    if v is not None:
                        same_line_values[(year, wert_typ)] = v

            if same_line_values:
                results.append({"konto7": konto_match.group(1), "konto_bez": konto_bez,
                                 "values": same_line_values})
                pending = None
            else:
                pending = (konto_match.group(1), konto_bez)
                pending_shifted = is_shifted
                empty_after_pending = 0
            continue

        values = {}
        for w in row:
            year, wert_typ = assign_col(round(w["x0"]), pending_shifted if pending else False)
            if year is not None:
                v = parse_german_number(w["text"])
                if v is not None:
                    values[(year, wert_typ)] = v

        if pending and values:
            results.append({"konto7": pending[0], "konto_bez": pending[1], "values": values})
            pending = None
            pending_shifted = False
            empty_after_pending = 0
        elif pending and not values:
            empty_after_pending += 1
            if empty_after_pending >= 3:
                pending = None
                pending_shifted = False
                empty_after_pending = 0

    return results

# ---------------------------------------------------------------------------
# Hauptprozess
# ---------------------------------------------------------------------------
def main():
    print(f"Repair 2024 KK6/7 — gestartet {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  DB  : {DB_PATH}")
    print(f"  PDF : {PDF_PATH}")
    print()

    if not os.path.exists(PDF_PATH):
        print(f"[FEHLER] PDF nicht gefunden: {PDF_PATH}")
        return

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode = WAL")
    con.row_factory = sqlite3.Row

    # --- Dummy-Produkt ID ermitteln ---
    row = con.execute(
        "SELECT id FROM produkte WHERE produkt_nummer = ?", (DUMMY_PRODUKT_NR,)
    ).fetchone()
    if not row:
        print(f"[FEHLER] Dummy-Produkt {DUMMY_PRODUKT_NR} nicht in DB")
        con.close()
        return
    dummy_prod_id = row["id"]
    print(f"  Dummy-Produkt ID : {dummy_prod_id}")

    # --- Konto-Cache laden ---
    k_cache = {
        r["konto_nummer"]: r["id"]
        for r in con.execute("SELECT id, konto_nummer FROM konten")
    }
    kk_cache = {
        r["nummer"]: r["id"]
        for r in con.execute("SELECT id, nummer FROM kontenklassen")
    }

    def get_konto_id(konto7, bez):
        if konto7 in k_cache:
            return k_cache[konto7]
        kk_id = kk_cache.get(int(konto7[0])) if konto7 else None
        con.execute(
            "INSERT OR IGNORE INTO konten (konto_nummer, bezeichnung, kontenklasse_id) VALUES (?, ?, ?)",
            (konto7, bez or f"Konto {konto7}", kk_id),
        )
        kid = con.execute("SELECT id FROM konten WHERE konto_nummer = ?", (konto7,)).fetchone()["id"]
        k_cache[konto7] = kid
        return kid

    # --- Schritt 1: Alte unvollstaendige Daten loeschen ---
    print("Schritt 1: Loesche alte 2024-KK6/7-Daten...")
    del_result = con.execute(
        """
        DELETE FROM haushaltswerte
        WHERE haushaltsplan_jahr = ?
          AND produkt_id = ?
        """,
        (HAUSHALTSPLAN_JAHR, dummy_prod_id),
    )
    deleted = del_result.rowcount
    con.commit()
    print(f"  {deleted} Zeilen geloescht")

    # Auch migration_status reset
    con.execute(
        "UPDATE migration_status SET status='RESET', rows_imported=0 WHERE chunk_name='2024_GESAMT_FP'"
    )
    con.commit()

    # --- Schritt 2: PDF neu einlesen ---
    print()
    print(f"Schritt 2: Lese PDF (Seiten {GESAMT_FP_START_PAGE+1}–{GESAMT_FP_END_PAGE+1})...")

    records_total = 0
    rows_total    = 0
    pages_done    = 0
    pending_rows  = []

    def flush():
        nonlocal rows_total
        if not pending_rows:
            return
        con.executemany(
            "INSERT OR IGNORE INTO haushaltswerte "
            "(haushaltsplan_jahr, daten_jahr, wert_typ, produkt_id, konto_id, betrag) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            pending_rows,
        )
        con.commit()
        rows_total += len(pending_rows)
        pending_rows.clear()

    with pdfplumber.open(PDF_PATH) as pdf:
        total_pages = len(pdf.pages)
        end_page    = min(GESAMT_FP_END_PAGE + 1, total_pages)
        print(f"  PDF hat {total_pages} Seiten, verarbeite {GESAMT_FP_START_PAGE+1}–{end_page}")

        for pg_idx in range(GESAMT_FP_START_PAGE, end_page):
            page    = pdf.pages[pg_idx]
            label   = f"p{pg_idx+1}"
            records = extract_page(page, label)
            pages_done += 1

            if records:
                records_total += len(records)
                for rec in records:
                    kid = get_konto_id(rec["konto7"], rec["konto_bez"])
                    for (year, wert_typ), betrag in rec["values"].items():
                        pending_rows.append((
                            HAUSHALTSPLAN_JAHR, year, wert_typ,
                            dummy_prod_id, kid, betrag,
                        ))

            if len(pending_rows) >= BATCH_SIZE:
                flush()

            if pg_idx % 5 == 0:
                print(f"  Seite {pg_idx+1}/{end_page} | Records bisher: {records_total}")

    flush()
    gc.collect()

    print(f"  Fertig: {pages_done} Seiten, {records_total} Buchungszeilen, {rows_total} DB-Rows")

    # migration_status aktualisieren
    con.execute(
        "UPDATE migration_status SET status='DONE', rows_imported=?, finished_at=? "
        "WHERE chunk_name='2024_GESAMT_FP'",
        (rows_total, datetime.now().isoformat()),
    )
    con.commit()

    # --- Schritt 3: Validierung ---
    print()
    print("Schritt 3: Validierung gegen Haushaltssatzung 2024")
    print("-" * 60)
    errors = 0
    labels = {6: "Einzahlungen KK6", 7: "Auszahlungen KK7"}
    for (kk_nr, wert_typ), soll in GROUND_TRUTH_2024.items():
        ist = con.execute("""
            SELECT COALESCE(SUM(h.betrag), 0)
            FROM haushaltswerte h
            JOIN konten k       ON h.konto_id = k.id
            JOIN kontenklassen kk ON k.kontenklasse_id = kk.id
            WHERE h.haushaltsplan_jahr = ?
              AND h.daten_jahr         = ?
              AND h.wert_typ           = ?
              AND kk.nummer            = ?
        """, (HAUSHALTSPLAN_JAHR, 2024, wert_typ, kk_nr)).fetchone()[0]
        diff   = ist - soll
        pct    = diff / soll * 100 if soll else 0
        ok     = abs(pct) < 0.25  # 0.25% Toleranz: Durchlaufende Gelder (69/79xxxx in TP-Chunks)
        sym    = "[OK]        " if ok else "[ABWEICHUNG]"
        if not ok:
            errors += 1
        print(
            f"  {sym} {labels[kk_nr]:22s}: "
            f"IST={ist:>15,.0f}  SOLL={soll:>15,.0f}  DIFF={diff:>+12.0f}  ({pct:+.2f}%)"
        )

    print()
    if errors == 0:
        print("[OK] KK6/7 fuer 2024 vollstaendig und korrekt.")
    else:
        print(f"[WARNUNG] {errors} Abweichung(en) — weitere Untersuchung noetig.")

    con.close()
    print(f"\nRepair abgeschlossen: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
