"""
pipeline_2024.py - ETL fuer Haushaltsplan Suhl 2024
Identisch zu pipeline.py, aber mit 2024-Konfiguration (COL_DEFS, Ground Truth).
"""

import gc
import re
import os
import sys
import sqlite3
from datetime import datetime
from glob import glob

import pdfplumber

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CHUNKS_DIR = os.path.join(BASE_DIR, "pdf_chunks_2024")
DB_PATH    = os.path.join(BASE_DIR, "suhl_haushalt_2025.db")  # selbe DB, anderes haushaltsplan_jahr
FAIL_LOG   = os.path.join(BASE_DIR, "parsing_failures_2024.log")
HAUSHALTSPLAN_JAHR = 2024
BATCH_SIZE = 500

# Spalten-Definitionen: (x_min, x_max, daten_jahr, wert_typ)
# Ermittelt durch Seiten-Probe; Jahres-Labels im PDF bei x=306,353,399,444,489,534
COL_DEFS = [
    (265, 340, 2022, "IST_ERGEBNIS"),
    (340, 392, 2023, "ANSATZ_VORJAHR"),
    (392, 437, 2024, "PLAN_ANSATZ"),
    (437, 482, 2025, "FINANZPLANUNG"),
    (482, 527, 2026, "FINANZPLANUNG"),
    (527, 580, 2027, "FINANZPLANUNG"),
]

# Account-Code-Format: PPPPPP.KKKKKK(K) bei x=55-125
KONTO_LINE_RE = re.compile(r"^(\d{5,6})\.(\d{6,7})$")

# Spalten-Definitionen für Gesamtproduktplan Finanzplan (Seiten 27-41 im Chunk)
# Jahresspalten liegen ~37px weiter links als in TP-Chunks
COL_DEFS_GESAMT = [
    (225, 293, 2022, "IST_ERGEBNIS"),
    (293, 348, 2023, "ANSATZ_VORJAHR"),
    (348, 401, 2024, "PLAN_ANSATZ"),
    (401, 450, 2025, "FINANZPLANUNG"),
    (450, 500, 2026, "FINANZPLANUNG"),
    (500, 555, 2027, "FINANZPLANUNG"),
]

# Account-Code-Format im Gesamtproduktplan Finanzplan: 7-stellig, kein Punkt, bei x=65-95
PLAIN_KONTO_RE = re.compile(r"^(\d{7})$")

GESAMT_FINANZPLAN_CHUNK = os.path.join(CHUNKS_DIR, "00_3_Gesamtproduktplan.pdf")
GESAMT_FP_START_PAGE = 34   # 0-basiert (= Seite 35 im Chunk, dok-Seite 133)
GESAMT_FP_END_PAGE   = 51   # 0-basiert, inklusiv (= Seite 52 im Chunk, dok-Seite 150)

# CID-Kodierung → UTF-8 (Umlaute in PDF)
CID_MAP = {
    "196": "Ae", "214": "Oe", "220": "Ue",
    "223": "ss", "228": "ae", "246": "oe", "252": "ue",
    "233": "e",  "176": "°",
}

# Ground Truth aus der Haushaltssatzung 2024 §1
GROUND_TRUTH = {
    (4, "PLAN_ANSATZ"): 130_353_020.00,
    (5, "PLAN_ANSATZ"): 133_802_080.00,
    (6, "PLAN_ANSATZ"): 124_398_580.00,
    (7, "PLAN_ANSATZ"): 123_750_200.00,
}

# Korrekte Teilplan-Bezeichnungen aus dem PDF-TOC (ersetzen Platzhalter in setup_database.py)
TEILPLAENE_KORREKT = {
    "01": "Verwaltungsfuehrung",
    "02": "Kultur, Tourismus und Sport",
    "03": "Personal/Zentrale Dienste",
    "04": "Finanzverwaltung",
    "05": "Oeffentliche Flaechen und Strassen",
    "06": "Allgemeine Finanzwirtschaft",
    "07": "Ordnung und Sicherheit",
    "08": "Umwelt",
    "09": "Soziales und Gesundheit",
    "10": "Schultraegeraufgaben",
    "11": "Kinder-, Jugend- und Familienhilfe",
    "12": "Einrichtungen Sozialdezernat",
}


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


MIGRATION_PREFIX = "2024_"

def mkey(name: str) -> str:
    return MIGRATION_PREFIX + name

def decode_cid(text: str) -> str:
    return re.sub(r"\(cid:(\d+)\)", lambda m: CID_MAP.get(m.group(1), "?"), text)


def parse_german_number(s: str):
    """Konvertiert deutschen Haushaltsbetrag in float; None bei ungültigem Format."""
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


def assign_column(x: float):
    for x_min, x_max, year, wert_typ in COL_DEFS:
        if x_min <= x < x_max:
            return year, wert_typ
    return None, None


def assign_column_gesamt(x: float):
    for x_min, x_max, year, wert_typ in COL_DEFS_GESAMT:
        if x_min <= x < x_max:
            return year, wert_typ
    return None, None


# ---------------------------------------------------------------------------
# DB-Kontext
# ---------------------------------------------------------------------------

class DbContext:
    """Kapselt DB-Verbindung und FK-Lookup-Caches."""

    def __init__(self, con):
        self.con = con
        self._reload()

    def _reload(self):
        c = self.con
        self.hpb_by_digit = {
            r["nummer"]: r["id"]
            for r in c.execute("SELECT id, nummer FROM hauptproduktbereiche")
        }
        self.tp_by_nr = {
            r["nummer"]: r["id"]
            for r in c.execute("SELECT id, nummer FROM teilplaene")
        }
        self.kk_by_nr = {
            r["nummer"]: r["id"]
            for r in c.execute("SELECT id, nummer FROM kontenklassen")
        }
        self.p_cache = {
            r["produkt_nummer"]: r["id"]
            for r in c.execute("SELECT id, produkt_nummer FROM produkte")
        }
        self.k_cache = {
            r["konto_nummer"]: r["id"]
            for r in c.execute("SELECT id, konto_nummer FROM konten")
        }
        # Steuerungskategorie von 4-stelligem Produkt-Präfix
        self.sk_by_p4 = {
            r["produkt_nummer"]: r["steuerungs_kategorie_id"]
            for r in c.execute(
                "SELECT produkt_nummer, steuerungs_kategorie_id FROM produkte "
                "WHERE steuerungs_kategorie_id IS NOT NULL AND length(produkt_nummer)=4"
            )
        }

    def get_produkt_id(self, prod6: str, bez: str, tp_nr: str) -> int:
        if prod6 in self.p_cache:
            return self.p_cache[prod6]
        prefix4 = prod6[:4]
        sk_id  = self.sk_by_p4.get(prefix4)
        hpb_id = self.hpb_by_digit.get(prod6[0])
        tp_id  = self.tp_by_nr.get(tp_nr.zfill(2))
        self.con.execute(
            "INSERT OR IGNORE INTO produkte "
            "(produkt_nummer, bezeichnung, teilplan_id, hauptproduktbereich_id, steuerungs_kategorie_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (prod6, bez or f"Produkt {prod6}", tp_id, hpb_id, sk_id),
        )
        pid = self.con.execute(
            "SELECT id FROM produkte WHERE produkt_nummer = ?", (prod6,)
        ).fetchone()["id"]
        self.p_cache[prod6] = pid
        return pid

    def get_konto_id(self, konto7: str, bez: str) -> int:
        if konto7 in self.k_cache:
            return self.k_cache[konto7]
        kk_id = self.kk_by_nr.get(int(konto7[0])) if konto7 else None
        self.con.execute(
            "INSERT OR IGNORE INTO konten (konto_nummer, bezeichnung, kontenklasse_id) "
            "VALUES (?, ?, ?)",
            (konto7, bez or f"Konto {konto7}", kk_id),
        )
        kid = self.con.execute(
            "SELECT id FROM konten WHERE konto_nummer = ?", (konto7,)
        ).fetchone()["id"]
        self.k_cache[konto7] = kid
        return kid


# ---------------------------------------------------------------------------
# Extract – eine Seite parsen
# ---------------------------------------------------------------------------

def extract_page(page, fail_log, page_label: str) -> list:
    """
    Parst eine Seite des Chunks. Gibt Buchungszeilen-Records zurück.
    State Machine: KONTO_LINE_RE → values (folgende Zeile).
    Look-Ahead-Buffer: bis 3 leere Zeilen nach Account-Code toleriert.
    """
    try:
        words = page.extract_words(
            x_tolerance=3, y_tolerance=3,
            keep_blank_chars=False, use_text_flow=False,
        )
    except Exception as exc:
        fail_log.write(f"[{page_label}] extract_words Fehler: {exc}\n")
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
    pending = None      # (prod6, konto7, konto_bez)
    empty_after_pending = 0

    for y, row in line_list:
        # Account-Code: PPPPPP.KKKKKK bei x=50–125 (2024-PDF: ~54px)
        konto_match = None
        for w in row:
            if 50 <= round(w["x0"]) <= 125:
                m = KONTO_LINE_RE.match(w["text"])
                if m:
                    konto_match = m
                    break

        if konto_match:
            konto_bez = " ".join(
                decode_cid(w["text"])
                for w in row
                if round(w["x0"]) > 125 and assign_column(round(w["x0"]))[0] is None
            )
            # Prüfe: sind Werte auf DERSELBEN Zeile (Finanzplan-Format)?
            # Dash "-" im Spaltenbereich ist Beschreibungspunktuierung, kein Wert.
            same_line_values = {}
            for w in row:
                x = round(w["x0"])
                year, wert_typ = assign_column(x)
                if year is not None and w["text"].strip() not in ("-", "–"):
                    v = parse_german_number(w["text"])
                    if v is not None:
                        same_line_values[(year, wert_typ)] = v

            if same_line_values:
                # Finanzplan-Format: Wert auf gleicher Zeile wie Konto-Code
                results.append({
                    "prod6":    konto_match.group(1),
                    "konto7":   konto_match.group(2),
                    "konto_bez": konto_bez,
                    "values":   same_line_values,
                })
                pending = None
            else:
                # Ergebnisplan-Format: Werte auf der nächsten Zeile
                pending = (konto_match.group(1), konto_match.group(2), konto_bez)
                empty_after_pending = 0
            continue

        # Werte-Extraktion
        values = {}
        for w in row:
            x = round(w["x0"])
            year, wert_typ = assign_column(x)
            if year is not None:
                v = parse_german_number(w["text"])
                if v is not None:
                    values[(year, wert_typ)] = v

        if pending and values:
            prod6, konto7, konto_bez = pending
            results.append({
                "prod6":    prod6,
                "konto7":   konto7,
                "konto_bez": konto_bez,
                "values":   values,
            })
            pending = None
            empty_after_pending = 0

        elif pending and not values:
            # Leere / Textzeile nach Account-Code: bis 3 tolerieren
            empty_after_pending += 1
            if empty_after_pending >= 3:
                fail_log.write(
                    f"[{page_label}:y{y}] Account-Code ohne Werte verworfen: "
                    f"{pending[0]}.{pending[1]}\n"
                )
                pending = None
                empty_after_pending = 0

    return results


def extract_page_gesamt(page, fail_log, page_label: str) -> list:
    """
    Parst eine Seite des Gesamtproduktplan-Finanzplans (Seiten 27-41).
    Account-Code: 7-stellige Zahl ohne Punkt bei x=65-95.
    Nur KK6/7 (Einzahlungen/Auszahlungen) werden extrahiert.
    Unterstützt same-line (Finanzplan) und next-line (Ergebnisplan) Formate.
    """
    try:
        words = page.extract_words(
            x_tolerance=3, y_tolerance=3,
            keep_blank_chars=False, use_text_flow=False,
        )
    except Exception as exc:
        fail_log.write(f"[{page_label}] extract_words Fehler: {exc}\n")
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
    empty_after_pending = 0

    for y, row in line_list:
        konto_match = None
        for w in row:
            if 65 <= round(w["x0"]) <= 95:
                m = PLAIN_KONTO_RE.match(w["text"])
                # Nur laufende KK6/7 (62-67xxxxx, 72-77xxxxx).
                # Investive/Finanzierung 68/69/78/79xxxxx bereits in TP-Chunks
                # oder außerhalb der HH-Satzungs-Eckwerte.
                if m and w["text"][0] in ("6", "7") and w["text"][:2] not in ("68", "69", "78", "79"):
                    konto_match = m
                break

        if konto_match:
            konto_bez = " ".join(
                decode_cid(w["text"])
                for w in row
                if round(w["x0"]) > 100 and assign_column_gesamt(round(w["x0"]))[0] is None
            )
            same_line_values = {}
            for w in row:
                x = round(w["x0"])
                year, wert_typ = assign_column_gesamt(x)
                if year is not None:
                    v = parse_german_number(w["text"])
                    if v is not None:
                        same_line_values[(year, wert_typ)] = v

            if same_line_values:
                results.append({
                    "konto7":    konto_match.group(1),
                    "konto_bez": konto_bez,
                    "values":    same_line_values,
                })
                pending = None
            else:
                pending = (konto_match.group(1), konto_bez)
                empty_after_pending = 0
            continue

        values = {}
        for w in row:
            x = round(w["x0"])
            year, wert_typ = assign_column_gesamt(x)
            if year is not None:
                v = parse_german_number(w["text"])
                if v is not None:
                    values[(year, wert_typ)] = v

        if pending and values:
            konto7, konto_bez = pending
            results.append({
                "konto7":    konto7,
                "konto_bez": konto_bez,
                "values":    values,
            })
            pending = None
            empty_after_pending = 0

        elif pending and not values:
            empty_after_pending += 1
            if empty_after_pending >= 3:
                fail_log.write(
                    f"[{page_label}:y{y}] Konto ohne Werte verworfen: {pending[0]}\n"
                )
                pending = None
                empty_after_pending = 0

    return results


# ---------------------------------------------------------------------------
# Build – Records → DB-Tupel
# ---------------------------------------------------------------------------

def build_rows(records: list, db: DbContext, tp_nr: str) -> list:
    rows = []
    for rec in records:
        prod_id  = db.get_produkt_id(rec["prod6"], "", tp_nr)
        konto_id = db.get_konto_id(rec["konto7"], rec["konto_bez"])
        for (year, wert_typ), betrag in rec["values"].items():
            rows.append((HAUSHALTSPLAN_JAHR, year, wert_typ, prod_id, konto_id, betrag))
    return rows


# ---------------------------------------------------------------------------
# Phase 3: Chunk verarbeiten (mit aggressivem RAM-Management)
# ---------------------------------------------------------------------------

def process_chunk(chunk_path: str, tp_nr: str, con, db: DbContext, fail_log) -> dict:
    """
    Öffnet, verarbeitet, schließt einen PDF-Chunk vollständig.
    Schreibt nach BATCH_SIZE Zeilen in die DB (Bulk-Insert).
    Ruft gc.collect() nach dem Schließen des PDFs auf.
    """
    chunk_name = os.path.basename(chunk_path)
    chunk_key  = mkey(chunk_name)

    # Resumability: bereits verarbeitete Chunks überspringen
    row = con.execute(
        "SELECT status FROM migration_status WHERE chunk_name = ?", (chunk_key,)
    ).fetchone()
    if row and row["status"] == "DONE":
        hw_count = con.execute(
            "SELECT rows_imported FROM migration_status WHERE chunk_name = ?", (chunk_key,)
        ).fetchone()["rows_imported"]
        print(f"  [SKIP] {chunk_name} (bereits DONE, {hw_count} Rows)")
        return {"pages": 0, "records": 0, "rows": hw_count, "errors": 0, "skipped": True}

    # Status → PROCESSING
    con.execute(
        "INSERT OR REPLACE INTO migration_status "
        "(chunk_name, status, rows_imported, started_at) VALUES (?, 'PROCESSING', 0, ?)",
        (mkey(chunk_name), datetime.now().isoformat()),
    )
    con.commit()

    stats = {"pages": 0, "records": 0, "rows": 0, "errors": 0, "skipped": False}
    pending_rows = []

    def flush():
        if not pending_rows:
            return
        con.executemany(
            "INSERT OR IGNORE INTO haushaltswerte "
            "(haushaltsplan_jahr, daten_jahr, wert_typ, produkt_id, konto_id, betrag) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            pending_rows,
        )
        con.commit()
        stats["rows"] += len(pending_rows)
        pending_rows.clear()

    try:
        with pdfplumber.open(chunk_path) as pdf:
            for pg_idx, page in enumerate(pdf.pages):
                label = f"{chunk_name}:p{pg_idx + 1}"
                stats["pages"] += 1
                try:
                    records = extract_page(page, fail_log, label)
                    if records:
                        stats["records"] += len(records)
                        new_rows = build_rows(records, db, tp_nr)
                        pending_rows.extend(new_rows)
                    if len(pending_rows) >= BATCH_SIZE:
                        flush()
                except Exception as exc:
                    stats["errors"] += 1
                    fail_log.write(f"[{label}] Verarbeitungsfehler: {exc}\n")

        # Letzter Batch
        flush()

    except Exception as exc:
        con.execute(
            "UPDATE migration_status SET status='ERROR', error_msg=?, finished_at=? "
            "WHERE chunk_name=?",
            (str(exc), datetime.now().isoformat(), mkey(chunk_name)),
        )
        con.commit()
        raise

    finally:
        # Phase 3: RAM-Management — pdfplumber-Instanz wurde durch 'with' bereits
        # geschlossen; Garbage Collector explizit aufrufen
        gc.collect()

    # Status → DONE
    con.execute(
        "UPDATE migration_status SET status='DONE', rows_imported=?, finished_at=? "
        "WHERE chunk_name=?",
        (stats["rows"], datetime.now().isoformat(), chunk_key),
    )
    con.commit()

    return stats


# ---------------------------------------------------------------------------
# Zweiter ETL-Pass: laufende KK6/7 aus Gesamtproduktplan Finanzplan
# ---------------------------------------------------------------------------

def process_gesamtproduktplan_finanzplan(con, db: DbContext, fail_log) -> dict:
    """
    Extrahiert laufende KK6/7-Konten (62-67xxxxx / 72-77xxxxx) aus dem
    Gesamtproduktplan Finanzplan mit Einzelkontengliederung (Seiten 27-41).
    Diese Konten existieren NICHT in den TP-Chunks → kein Doppelzählen-Risiko.
    Dummy-Produkt '000000' (kein TP-Bezug) wird für alle Zeilen verwendet.
    """
    chunk_name = "GESAMT_FP"
    chunk_key  = mkey(chunk_name)

    row = con.execute(
        "SELECT status FROM migration_status WHERE chunk_name = ?", (chunk_key,)
    ).fetchone()
    if row and row["status"] == "DONE":
        hw_count = con.execute(
            "SELECT rows_imported FROM migration_status WHERE chunk_name = ?", (chunk_key,)
        ).fetchone()["rows_imported"]
        print(f"  [SKIP] {chunk_name} (bereits DONE, {hw_count} Rows)")
        return {"pages": 0, "records": 0, "rows": hw_count, "errors": 0, "skipped": True}

    if not os.path.exists(GESAMT_FINANZPLAN_CHUNK):
        print(f"  [FEHLER] Chunk nicht gefunden: {GESAMT_FINANZPLAN_CHUNK}")
        return {"pages": 0, "records": 0, "rows": 0, "errors": 1, "skipped": False}

    con.execute(
        "INSERT OR REPLACE INTO migration_status "
        "(chunk_name, status, rows_imported, started_at) VALUES (?, 'PROCESSING', 0, ?)",
        (mkey(chunk_name), datetime.now().isoformat()),
    )
    con.commit()

    dummy_prod_id = db.get_produkt_id(
        "000000", "Gesamtfinanzplan laufende Verwaltung", "00"
    )

    stats = {"pages": 0, "records": 0, "rows": 0, "errors": 0, "skipped": False}
    pending_rows = []

    def flush():
        if not pending_rows:
            return
        con.executemany(
            "INSERT OR IGNORE INTO haushaltswerte "
            "(haushaltsplan_jahr, daten_jahr, wert_typ, produkt_id, konto_id, betrag) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            pending_rows,
        )
        con.commit()
        stats["rows"] += len(pending_rows)
        pending_rows.clear()

    try:
        with pdfplumber.open(GESAMT_FINANZPLAN_CHUNK) as pdf:
            end_page = min(GESAMT_FP_END_PAGE + 1, len(pdf.pages))
            for pg_idx in range(GESAMT_FP_START_PAGE, end_page):
                page  = pdf.pages[pg_idx]
                label = f"GFP:p{pg_idx + 1}"
                stats["pages"] += 1
                try:
                    records = extract_page_gesamt(page, fail_log, label)
                    if records:
                        stats["records"] += len(records)
                        for rec in records:
                            konto_id = db.get_konto_id(rec["konto7"], rec["konto_bez"])
                            for (year, wert_typ), betrag in rec["values"].items():
                                pending_rows.append((
                                    HAUSHALTSPLAN_JAHR, year, wert_typ,
                                    dummy_prod_id, konto_id, betrag,
                                ))
                    if len(pending_rows) >= BATCH_SIZE:
                        flush()
                except Exception as exc:
                    stats["errors"] += 1
                    fail_log.write(f"[{label}] Verarbeitungsfehler: {exc}\n")

        flush()

    except Exception as exc:
        con.execute(
            "UPDATE migration_status SET status='ERROR', error_msg=?, finished_at=? "
            "WHERE chunk_name=?",
            (str(exc), datetime.now().isoformat(), mkey(chunk_name)),
        )
        con.commit()
        raise

    finally:
        gc.collect()

    con.execute(
        "UPDATE migration_status SET status='DONE', rows_imported=?, finished_at=? "
        "WHERE chunk_name=?",
        (stats["rows"], datetime.now().isoformat(), chunk_key),
    )
    con.commit()

    return stats


# ---------------------------------------------------------------------------
# Phase 4: Ground Truth Validierung
# ---------------------------------------------------------------------------

def run_validation(con) -> int:
    errors = 0
    print("\n--- Ground Truth Validierung (Haushaltssatzung 2024) ---")
    labels = {
        4: "Ertraege    KK4",
        5: "Aufwendungen KK5",
        6: "Einzahlungen KK6",
        7: "Auszahlungen KK7",
    }
    for (kk_nr, wert_typ), soll in GROUND_TRUTH.items():
        ist = con.execute(
            """
            SELECT COALESCE(SUM(h.betrag), 0)
            FROM haushaltswerte h
            JOIN konten k       ON h.konto_id = k.id
            JOIN kontenklassen kk ON k.kontenklasse_id = kk.id
            WHERE h.haushaltsplan_jahr = ?
              AND h.daten_jahr         = 2024
              AND h.wert_typ           = ?
              AND kk.nummer            = ?
            """,
            (HAUSHALTSPLAN_JAHR, wert_typ, kk_nr),
        ).fetchone()[0]
        diff = ist - soll
        ok   = abs(diff) < 0.01
        sym  = "[OK]        " if ok else "[ABWEICHUNG]"
        if not ok:
            errors += 1
        print(
            f"  {sym} {labels[kk_nr]:20s}: "
            f"IST={ist:>16,.2f}  SOLL={soll:>16,.2f}  DIFF={diff:>+13.2f}"
        )
    return errors


# ---------------------------------------------------------------------------
# Teilplan-Bezeichnungen in DB aktualisieren (korrigiert Platzhalter)
# ---------------------------------------------------------------------------

def fix_teilplan_bezeichnungen(con):
    for nr, bez in TEILPLAENE_KORREKT.items():
        con.execute(
            "UPDATE teilplaene SET bezeichnung = ? WHERE nummer = ?", (bez, nr)
        )
    con.commit()
    print("  Teilplan-Bezeichnungen aktualisiert.")


# ---------------------------------------------------------------------------
# Hauptprozess
# ---------------------------------------------------------------------------

def main():
    start_ts = datetime.now()

    if not os.path.exists(DB_PATH):
        print(f"[FEHLER] DB nicht gefunden: {DB_PATH}. Bitte setup_database.py ausfuehren.")
        sys.exit(1)
    if not os.path.exists(CHUNKS_DIR):
        print(f"[FEHLER] Chunk-Verzeichnis nicht gefunden: {CHUNKS_DIR}. Bitte smart_split.py ausfuehren.")
        sys.exit(1)

    chunk_files = sorted(glob(os.path.join(CHUNKS_DIR, "tp_*.pdf")))
    if not chunk_files:
        print(f"[FEHLER] Keine tp_*.pdf in {CHUNKS_DIR}. Bitte smart_split.py ausfuehren.")
        sys.exit(1)

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    con.row_factory = sqlite3.Row

    # Migration-Status-Tabelle (Phase 3)
    con.execute("""
        CREATE TABLE IF NOT EXISTS migration_status (
            chunk_name  TEXT PRIMARY KEY,
            status      TEXT NOT NULL,
            rows_imported INTEGER DEFAULT 0,
            started_at  TEXT,
            finished_at TEXT,
            error_msg   TEXT
        )
    """)
    con.commit()

    # Korrekte TP-Bezeichnungen eintragen
    fix_teilplan_bezeichnungen(con)

    db = DbContext(con)

    print(f"ETL-Pipeline gestartet : {start_ts.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Chunks gefunden        : {len(chunk_files)}")
    print(f"Datenbank              : {DB_PATH}")
    print(f"Failures-Log           : {FAIL_LOG}\n")

    fail_log = open(FAIL_LOG, "w", encoding="utf-8")
    fail_log.write(f"Parsing Failures Log - {start_ts.isoformat()}\n{'='*60}\n\n")

    total_rows   = 0
    total_errors = 0

    for chunk_path in chunk_files:
        fname    = os.path.basename(chunk_path)
        m        = re.match(r"tp_(\d+)_", fname)
        tp_nr    = m.group(1) if m else "01"
        size_mb  = os.path.getsize(chunk_path) / 1_048_576

        print(f"[TP {tp_nr:>2s}] {fname}  ({size_mb:.1f} MB)")

        try:
            stats = process_chunk(chunk_path, tp_nr, con, db, fail_log)
            total_rows   += stats["rows"]
            total_errors += stats["errors"]
            if not stats.get("skipped"):
                print(
                    f"       Seiten={stats['pages']:3d} | "
                    f"Buchungszeilen={stats['records']:5d} | "
                    f"DB-Rows={stats['rows']:5d} | "
                    f"Fehler={stats['errors']}"
                )
        except Exception as exc:
            total_errors += 1
            print(f"       [CHUNK-FEHLER] {exc}")
            fail_log.write(f"\n=== CHUNK FEHLGESCHLAGEN: {fname} ===\n{exc}\n\n")

        # Phase 3: explizites RAM-Freigeben zwischen Chunks
        gc.collect()
        print()

    # Zweiter ETL-Pass: laufende KK6/7 aus Gesamtproduktplan Finanzplan
    print(f"[GESAMT-FP] {os.path.basename(GESAMT_FINANZPLAN_CHUNK)}  (Seiten 27-41)")
    try:
        stats = process_gesamtproduktplan_finanzplan(con, db, fail_log)
        total_rows   += stats["rows"]
        total_errors += stats["errors"]
        if not stats.get("skipped"):
            print(
                f"       Seiten={stats['pages']:3d} | "
                f"Buchungszeilen={stats['records']:5d} | "
                f"DB-Rows={stats['rows']:5d} | "
                f"Fehler={stats['errors']}"
            )
    except Exception as exc:
        total_errors += 1
        print(f"       [GESAMT-FP-FEHLER] {exc}")
        fail_log.write(f"\n=== GESAMT-FP FEHLGESCHLAGEN ===\n{exc}\n\n")
    gc.collect()
    print()

    fail_log.close()

    elapsed = (datetime.now() - start_ts).seconds
    hw_count = con.execute("SELECT COUNT(*) FROM haushaltswerte").fetchone()[0]
    p_count  = con.execute("SELECT COUNT(*) FROM produkte").fetchone()[0]
    k_count  = con.execute("SELECT COUNT(*) FROM konten").fetchone()[0]

    print(f"{'='*60}")
    print(f"ETL abgeschlossen in {elapsed}s")
    print(f"  haushaltswerte in DB  : {hw_count:>7,}")
    print(f"  produkte in DB        : {p_count:>7,}")
    print(f"  konten in DB          : {k_count:>7,}")
    print(f"  Parse-Fehler gesamt   : {total_errors:>7,}")

    # Phase 4: Ground Truth Validierung
    gt_errors = run_validation(con)
    con.close()

    print(f"\n{'='*60}")
    if gt_errors == 0:
        print("[OK] ALLE ECKWERTE VALIDIERT - Datenbank bereit fuer Dashboard.")
    else:
        print(f"[WARNUNG] {gt_errors} Eckwert-Abweichungen.")
        print(f"  Parsing-Failures: {FAIL_LOG}")
        print("  Tipp: python -X utf8 validate.py fuer Detailbericht")
    print(f"{'='*60}")

    sys.exit(1 if gt_errors > 0 else 0)


if __name__ == "__main__":
    main()
