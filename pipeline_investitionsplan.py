"""
pipeline_investitionsplan.py - ETL fuer den Investitionsplan nach Investitionsnummern
(Gliederungspunkt "4." in jedem Haushaltsplan-PDF).

Anders als pipeline_2023/2024/2026.py (die den normalen Konten-Zahlenraster parsen)
ist der Investitionsplan ein Freitext+Zahlen-Hybrid: pro Massnahme ein Kopf
(Investitionsnummer + Bezeichnung), ein Erlaeuterungs-Freitext, 1-3 Summenzeilen
(Einzahlungen/Auszahlungen/Zu-/Ueberschuss) und darunter 1-n Konto-Einzelzeilen
(Produkt.Konto + Bezeichnung + dieselben 7 Zahlenspalten). Der Parser arbeitet
daher zeilenbasiert per Regex statt ueber x-Koordinaten-Spalten.

Investitionsnummern sind ueber Jahrgaenge hinweg stabil (siehe Memory
project_investitionsplan_fund.md) - Kern dieser Pipeline ist daher, pro Massnahme
eine "Edition" je Haushaltsplan-Jahrgang zu speichern, damit sich daraus sowohl
Foerdermittel-/Eigenanteil-Aufschluesselung als auch eine Jahres-Prognose-Drift
(Kostensteigerungen/Terminverzug) ableiten lassen.

Validierung: Summe der Ansatz-Spalte (Auszahlungen/Einzahlungen) ueber alle
geparsten Massnahmen eines Jahrgangs wird gegen die im PDF selbst enthaltene
Endsumme (letzte Zeilen des Abschnitts) sowie gegen die Werte aus 2.4.4 (bzw.
2.4.3 in 2023-2025) abgeglichen und beim Lauf ausgegeben.
"""

import os
import re
import sqlite3
import sys

import pdfplumber

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "suhl_haushalt_2025.db")

# ---------------------------------------------------------------------------
# Editionen-Konfiguration: (hh_plan_jahr, pdf_pfad, section_start_page, section_end_page, has_ve)
# section_start/end_page = tatsaechliche Tabellenseiten mit wiederholtem Kopf
# "Investitionsplan <jahr>" (NICHT die Top-Level-TOC-Seite "4." - dort beginnen erst
# 4.1 Erlaeuterungen + Zuordnungstabelle, noch keine Massnahmen-Datensaetze).
# has_ve: ab Haushaltsplanung 2026 wurde die Veranschlagung von Verpflichtungs-
# ermaechtigungen (VE) wieder eingefuehrt (siehe 4.1-Erlaeuterungstext) - dadurch
# hat die Tabelle ab 2026 eine 7. Zahlenspalte ("Gesamt VE"), die es 2023-2025
# nicht gibt (dort nur 6 Zahlenspalten: Ansatz/PW1/PW2/PW3/bisher/Gesamt Invest.).
# ---------------------------------------------------------------------------
EDITIONS = [
    (2023, os.path.join(BASE_DIR, "haushalt_suhl_2023.pdf"), 147, 167, False),
    (2024, os.path.join(BASE_DIR, "haushalt_suhl_2024.pdf"), 155, 176, False),
    (2025, os.path.join(BASE_DIR, "knowledge", "HH-Plan Stadt Suhl 2025.pdf"), 146, 169, False),
    (2026, os.path.join(BASE_DIR, "knowledge", "HH-Plan Stadt Suhl 2026", "HHPlan 2026.pdf"), 160, 186, True),
]

# Erwartete Grand-Total-Auszahlungen/Einzahlungen (Ansatz-Spalte, Jahr = Edition-Jahr)
# aus dem jeweiligen Vorbericht-Abschnitt (2.4.3/2.4.4 "Investitionen") zur Validierung.
# None = noch nicht per Hand verifiziert -> Validierung wird uebersprungen.
EXPECTED_TOTALS = {
    2023: None,
    2024: None,
    2025: None,
    2026: (4_583_090.00, 7_798_730.00),  # (Einzahlungen Ansatz, Auszahlungen Ansatz)
}

CID_MAP = {
    "196": "Ae", "214": "Oe", "220": "Ue",
    "223": "ss", "228": "ae", "246": "oe", "252": "ue",
    "233": "e", "176": "°",
}


def decode_cid(text: str) -> str:
    return re.sub(r"\(cid:(\d+)\)", lambda m: CID_MAP.get(m.group(1), "?"), text)


def parse_german_number(s: str):
    s = s.strip().replace("\xa0", "").replace(" ", "")
    if not s or s in ("-", "–"):
        return 0.0
    if s == "0":
        return 0.0
    negative = s.startswith("-")
    if negative:
        s = s[1:]
    s = s.replace(".", "").replace(",", ".")
    try:
        v = float(s)
        return -v if negative else v
    except ValueError:
        return None


NUM = r"-?[\d.]+"
NUM_DEC = r"-?[\d.,]+"
# Ab Haushaltsplan 2026 gibt es 7 Zahlenspalten (Ansatz/PW1/PW2/PW3/bisher/VE/Gesamt),
# 2023-2025 nur 6 (Ansatz/PW1/PW2/PW3/bisher/Gesamt, keine VE-Spalte) - siehe EDITIONS.
NUMS_TAIL_7 = rf"\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM_DEC})\s+({NUM})\s+({NUM_DEC})"
NUMS_TAIL_6 = rf"\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM_DEC})\s+({NUM_DEC})"

MEASURE_HEADER_RE = re.compile(r"^(\d{6,10})[ \t]+(\S.*)$", re.MULTILINE)
ERLAEUTERUNG_MARKER = "Erlaeuterung:"


def compile_row_regexes(has_ve: bool):
    tail = NUMS_TAIL_7 if has_ve else NUMS_TAIL_6
    summary_re = re.compile(r"(Einzahlungen|Auszahlungen|Zu-/Ueberschuss)" + tail)
    subline_re = re.compile(r"(?<![\d.])(\d{5,6})\.(\d{6,7})\s+(.*?)" + tail, re.DOTALL)
    n_vals = 7 if has_ve else 6
    return summary_re, subline_re, n_vals


def normalize_vals(vals_raw, has_ve: bool):
    """Bringt geparste Werte immer auf die 7-Spalten-Form
    (ansatz, pw1, pw2, pw3, bisher, ve, gesamt) - bei 6-Spalten-Editionen ist ve=None."""
    if has_ve:
        return list(vals_raw)
    ansatz, pw1, pw2, pw3, bisher, gesamt = vals_raw
    return [ansatz, pw1, pw2, pw3, bisher, None, gesamt]

NOISE_PATTERNS = [
    re.compile(r"^Investitionsplan \d{4}$"),
    re.compile(r"^\(in .\)$"),
    re.compile(r"^Investitionsnummer Ansatz Planwert"),
    re.compile(r"^\d{4} \d{4} \d{4} \d{4} bereitgestellt$"),
    re.compile(r"^\d{4} \d{4} \d{4} \d{4}$"),
    re.compile(r"^1 2 3 4 5 6 7$"),
    re.compile(r"^Seite \d+$"),
    re.compile(r"^$"),
]


def is_noise(line: str) -> bool:
    return any(p.match(line) for p in NOISE_PATTERNS)


def extract_section_text(path: str, start_page: int, end_page: int) -> str:
    with pdfplumber.open(path) as pdf:
        raw_lines = []
        for pnum in range(start_page, end_page + 1):
            text = pdf.pages[pnum - 1].extract_text() or ""
            text = decode_cid(text)
            raw_lines.extend(text.split("\n"))
    clean_lines = [l for l in raw_lines if not is_noise(l)]
    return "\n".join(clean_lines)


def parse_measures(full_text: str, has_ve: bool) -> list:
    summary_re, subline_re, n_vals = compile_row_regexes(has_ve)
    val_group_start = 2  # SUMMARY_RE: Gruppe 1 = Label, ab 2 die Zahlenspalten
    subline_val_group_start = 4  # SUBLINE_RE: 1=Produkt, 2=Konto, 3=Bezeichnung, ab 4 die Zahlenspalten

    raw_headers = list(MEASURE_HEADER_RE.finditer(full_text))

    # Falsch-Positive ausfiltern: Erlaeuterungstexte referenzieren gelegentlich eine ANDERE
    # Investitionsnummer im Fliesstext (z.B. "... Mitfinanzierung durch Verkauf ... in 2023
    # unter\n1142000003 Allg. Grundvermoegen/Grundstuecke\nnotwendige Ersatzbeschaffung ...").
    # Durch den Zeilenumbruch sieht das wie ein neuer Massnahmen-Kopf aus. Ein ECHTER Kopf hat
    # aber immer zeitnah ein "Erlaeuterung:"-Label; bei einer Referenz mitten im Fliesstext folgt
    # stattdessen direkt der naechste Satz. Kandidaten ohne "Erlaeuterung:" vor dem naechsten
    # Kandidaten-Header werden daher verworfen (ihr Text bleibt Teil des vorherigen Chunks).
    filtered = []
    for i, m in enumerate(raw_headers):
        window_end = raw_headers[i + 1].start() if i + 1 < len(raw_headers) else len(full_text)
        window = full_text[m.start():window_end]
        if ERLAEUTERUNG_MARKER in window:
            filtered.append(m)

    # Bei Seitenumbruechen mitten in einer Massnahme wiederholt sich die Investitionsnummer
    # manchmal als eigene Kopfzeile (z.B. Fortsetzung nach einem Seitenumbruch). Aufeinander-
    # folgende Treffer mit IDENTISCHER Nummer gehoeren daher zur selben Massnahme und werden
    # zu einem Chunk zusammengefasst (nur der erste Treffer liefert die Bezeichnung).
    headers = []
    for m in filtered:
        if headers and headers[-1].group(1) == m.group(1):
            continue
        headers.append(m)

    measures = []
    for i, m in enumerate(headers):
        start = m.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(full_text)
        chunk = full_text[start:end]
        investnr = m.group(1)
        rest_first_line = m.group(2)

        erl_idx = chunk.find(ERLAEUTERUNG_MARKER)
        header_block = chunk[:erl_idx] if erl_idx != -1 else chunk[:200]
        header_lines = header_block.split("\n")
        bezeichnung_parts = [rest_first_line] + [l.strip() for l in header_lines[1:] if l.strip()]
        bezeichnung = " ".join(bezeichnung_parts).strip()

        summaries = {}
        first_summary_pos = len(chunk)
        last_summary_end = 0
        for sm in summary_re.finditer(chunk):
            key = sm.group(1)
            vals_raw = [parse_german_number(sm.group(j)) for j in range(val_group_start, val_group_start + n_vals)]
            summaries[key] = normalize_vals(vals_raw, has_ve)
            first_summary_pos = min(first_summary_pos, sm.start())
            last_summary_end = max(last_summary_end, sm.end())

        # Kein gueltiger Datensatz gefunden (z.B. False-Positive-Header-Match in Fliesstext) -> verwerfen
        if not summaries:
            continue

        erlaeuterung = ""
        if erl_idx != -1:
            erl_text_start = erl_idx + len(ERLAEUTERUNG_MARKER)
            erlaeuterung = chunk[erl_text_start:first_summary_pos].strip()

        subline_text = chunk[last_summary_end:]
        sublines = []
        for sl in subline_re.finditer(subline_text):
            produkt, konto, bez = sl.group(1), sl.group(2), sl.group(3)
            bez_clean = " ".join(x.strip() for x in bez.split("\n") if x.strip())
            vals_raw = [parse_german_number(sl.group(j)) for j in range(subline_val_group_start, subline_val_group_start + n_vals)]
            vals = normalize_vals(vals_raw, has_ve)
            sublines.append((produkt, konto, bez_clean, vals))

        gesperrt = "Bewirtschaftung gesperrt" in erlaeuterung

        measures.append({
            "investnr": investnr,
            "bezeichnung": bezeichnung,
            "erlaeuterung": erlaeuterung,
            "gesperrt": gesperrt,
            "summaries": summaries,
            "sublines": sublines,
        })
    return measures


# ---------------------------------------------------------------------------
# DB-Schema
# ---------------------------------------------------------------------------

def setup_schema(con: sqlite3.Connection):
    con.executescript("""
    DROP TABLE IF EXISTS investitionsmassnahmen_konten;
    DROP TABLE IF EXISTS investitionsmassnahmen_editionen;
    DROP TABLE IF EXISTS investitionsmassnahmen;

    CREATE TABLE investitionsmassnahmen (
        id INTEGER PRIMARY KEY,
        investitionsnummer TEXT UNIQUE NOT NULL,
        bezeichnung TEXT
    );

    CREATE TABLE investitionsmassnahmen_editionen (
        id INTEGER PRIMARY KEY,
        massnahme_id INTEGER NOT NULL REFERENCES investitionsmassnahmen(id),
        hh_plan_jahr INTEGER NOT NULL,
        bezeichnung TEXT,
        erlaeuterung TEXT,
        gesperrt INTEGER NOT NULL DEFAULT 0,
        ein_ansatz REAL, ein_planwert_j1 REAL, ein_planwert_j2 REAL, ein_planwert_j3 REAL,
        ein_bisher REAL, ein_ve REAL, ein_gesamt REAL,
        aus_ansatz REAL, aus_planwert_j1 REAL, aus_planwert_j2 REAL, aus_planwert_j3 REAL,
        aus_bisher REAL, aus_ve REAL, aus_gesamt REAL,
        UNIQUE(massnahme_id, hh_plan_jahr)
    );

    CREATE TABLE investitionsmassnahmen_konten (
        id INTEGER PRIMARY KEY,
        edition_id INTEGER NOT NULL REFERENCES investitionsmassnahmen_editionen(id),
        produkt_nummer TEXT,
        konto_nummer TEXT,
        richtung TEXT,
        bezeichnung TEXT,
        ansatz REAL, planwert_j1 REAL, planwert_j2 REAL, planwert_j3 REAL,
        bisher_bereitgestellt REAL, ve REAL, gesamt REAL
    );
    """)


def import_edition(con: sqlite3.Connection, hh_plan_jahr: int, measures: list):
    cur = con.cursor()
    for m in measures:
        cur.execute(
            "INSERT INTO investitionsmassnahmen (investitionsnummer, bezeichnung) VALUES (?, ?) "
            "ON CONFLICT(investitionsnummer) DO UPDATE SET bezeichnung=excluded.bezeichnung",
            (m["investnr"], m["bezeichnung"]),
        )
        massnahme_id = cur.execute(
            "SELECT id FROM investitionsmassnahmen WHERE investitionsnummer=?", (m["investnr"],)
        ).fetchone()[0]

        ein = m["summaries"].get("Einzahlungen", [None] * 7)
        aus = m["summaries"].get("Auszahlungen", [None] * 7)

        cur.execute(
            "INSERT INTO investitionsmassnahmen_editionen "
            "(massnahme_id, hh_plan_jahr, bezeichnung, erlaeuterung, gesperrt, "
            " ein_ansatz, ein_planwert_j1, ein_planwert_j2, ein_planwert_j3, ein_bisher, ein_ve, ein_gesamt, "
            " aus_ansatz, aus_planwert_j1, aus_planwert_j2, aus_planwert_j3, aus_bisher, aus_ve, aus_gesamt) "
            "VALUES (?,?,?,?,?, ?,?,?,?,?,?,?, ?,?,?,?,?,?,?)",
            (
                massnahme_id, hh_plan_jahr, m["bezeichnung"], m["erlaeuterung"], int(m["gesperrt"]),
                *ein, *aus,
            ),
        )
        edition_id = cur.lastrowid

        for produkt, konto, bez, vals in m["sublines"]:
            richtung = "EINZAHLUNG" if konto.startswith("6") else ("AUSZAHLUNG" if konto[:1] in ("7", "8") else "UNKLAR")
            cur.execute(
                "INSERT INTO investitionsmassnahmen_konten "
                "(edition_id, produkt_nummer, konto_nummer, richtung, bezeichnung, "
                " ansatz, planwert_j1, planwert_j2, planwert_j3, bisher_bereitgestellt, ve, gesamt) "
                "VALUES (?,?,?,?,?, ?,?,?,?,?,?,?)",
                (edition_id, produkt, konto, richtung, bez, *vals),
            )
    con.commit()


def main():
    con = sqlite3.connect(DB_PATH)
    setup_schema(con)

    total_measures = 0
    for hh_plan_jahr, pdf_path, start_page, end_page, has_ve in EDITIONS:
        if not os.path.exists(pdf_path):
            print(f"[{hh_plan_jahr}] UEBERSPRUNGEN - PDF nicht gefunden: {pdf_path}")
            continue

        print(f"[{hh_plan_jahr}] Extrahiere Seiten {start_page}-{end_page} aus {os.path.basename(pdf_path)} "
              f"(has_ve={has_ve}) ...")
        text = extract_section_text(pdf_path, start_page, end_page)
        measures = parse_measures(text, has_ve)
        print(f"[{hh_plan_jahr}] {len(measures)} Massnahmen geparst.")

        sum_ein = sum(m["summaries"].get("Einzahlungen", [0] * 7)[0] or 0 for m in measures)
        sum_aus = sum(m["summaries"].get("Auszahlungen", [0] * 7)[0] or 0 for m in measures)
        print(f"[{hh_plan_jahr}] Summe Ansatz Einzahlungen: {sum_ein:,.2f} | Auszahlungen: {sum_aus:,.2f}")

        expected = EXPECTED_TOTALS.get(hh_plan_jahr)
        if expected:
            exp_ein, exp_aus = expected
            diff_ein = sum_ein - exp_ein
            diff_aus = sum_aus - exp_aus
            print(f"[{hh_plan_jahr}] Erwartet:                   {exp_ein:,.2f} | {exp_aus:,.2f}  "
                  f"(Diff: {diff_ein:+,.2f} / {diff_aus:+,.2f})")
        else:
            print(f"[{hh_plan_jahr}] (keine manuell verifizierte Erwartungssumme hinterlegt)")

        import_edition(con, hh_plan_jahr, measures)
        total_measures += len(measures)

    n_distinct = con.execute("SELECT COUNT(*) FROM investitionsmassnahmen").fetchone()[0]
    n_editionen = con.execute("SELECT COUNT(*) FROM investitionsmassnahmen_editionen").fetchone()[0]
    n_konten = con.execute("SELECT COUNT(*) FROM investitionsmassnahmen_konten").fetchone()[0]
    print()
    print(f"Fertig: {n_distinct} distinkte Investitionsnummern, {n_editionen} Editionen-Zeilen "
          f"({total_measures} Massnahmen-Vorkommen gesamt), {n_konten} Konto-Einzelzeilen.")
    con.close()


if __name__ == "__main__":
    main()
