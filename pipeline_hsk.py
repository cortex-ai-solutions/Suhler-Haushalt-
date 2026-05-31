"""
pipeline_hsk.py
Extrahiert alle ~80 Konsolidierungsmaßnahmen aus HSK-9-2025.pdf.

Quellen:
  Anlage XVII a  (Seiten 125–156 des PDF, idx 124–155)
    → "aus 8. Fortschreibung" als Anker-Marker, 13 Jahreswerte
  Anlage XVII b  (Seiten 157–164 des PDF, idx 156–163)
    → Maßnahmen 64–67 wie XVII a; neue Maßnahmen 68–80 ohne "aus 8. FS"-Block
  Kap. XVII      (Seiten 109–118 des PDF, idx 108–117)
    → Ergänzung fehlender Bezeichnungen und Produktnummern

Jahres-Mapping (Spaltenindex → Kalenderjahr):
  [0-8] → 2013–2021 (RE), [9] → 2022 (vorl.), [10] → 2023, [11] → 2024, [12] → 2025
  Enthält eine Maßnahme nur N<13 Werte → werden diese als letzte N Jahre interpretiert.
"""

import fitz
import re
import sqlite3
import sys
import os
from setup_database import DB_PATH, add_hsk_tables

PDF_PATH = os.path.join(os.path.dirname(__file__), "knowledge", "HSK-9-2025.pdf")

# Alle HSK-relevanten Seiten (0-indiziert)
ALL_HSK_PAGES  = list(range(108, 164))   # Kap. XVII + Anlage XVII a + XVII b
ANLAGE17A_PAGES = list(range(124, 158))  # XVII a + erste XVII b (64–67 haben "aus 8. FS")
ANLAGE17B_NEW   = list(range(157, 164))  # neue Maßnahmen 68–80 (ohne "aus 8. FS")

YEARS = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

# ── Parsing-Konstanten ────────────────────────────────────────────────────────

SKIP_EXACT = {
    "Nr. Bezeichnung", "Maßnahmebeschreibung", "Nr.",
    "Bezeichnung", "aus 8. Fortschreibung", "Umsetzungsvermerk",
    "9. Fortschreibung", "9. Fortschreibung ",
    "Veränderung pro Jahr", "Veränderung Summe",
    "umgesetzter Betrag", "Differenz p. a. zur 8. FS",
    "Differenz ∑ zur 8. FS",
}
YEAR_LABELS = (
    {str(y) for y in range(2013, 2026)}
    | {f"RE {y}" for y in range(2013, 2022)}
    | {"RE 2108", "vorl. RE 2022", "vorl. 2022"}
)
SECTION_TRIGGERS = {
    "aus 8. Fortschreibung", "umgesetzter Betrag",
    "Veränderung pro Jahr", "Veränderung Summe",
    "Differenz p. a. zur 8. FS", "Differenz ∑ zur 8. FS",
    "Umsetzungsvermerk", "9. Fortschreibung",
}

# Regex für Maßnahmen-Zeile
MEASURE_INLINE_RE = re.compile(r"^(\d{1,2})\s*([a-z])?\s+(\S.{2,})$")  # "01 Name"
MEASURE_LONE_RE   = re.compile(r"^(\d{1,2})\s*([a-z])?$")               # "05" allein
NUMBER_RE         = re.compile(r"^-?[\d][0-9.,]*$")
PRODUKT_RE        = re.compile(r"Produkt[e]?[:\s]+([0-9,./\s;]+)", re.IGNORECASE)


def is_skip(line: str) -> bool:
    return line in SKIP_EXACT or line in YEAR_LABELS or line.startswith("Seite ")


def is_number(line: str) -> bool:
    return bool(NUMBER_RE.match(line.strip()))


def parse_eur(s: str) -> float:
    s = s.strip()
    if not s:
        return 0.0
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def load_lines(doc, pages: list[int]) -> list[str]:
    lines = []
    for pg in pages:
        if pg < doc.page_count:
            lines.extend(l.strip() for l in doc[pg].get_text().split("\n"))
    return lines


# ── Header-Extraktion (rückwärts) ─────────────────────────────────────────────

def extract_header(lines: list[str], anchor_pos: int) -> tuple[str, str, list[str]]:
    """
    Sucht rückwärts ab anchor_pos nach Maßnahmen-Nr, Bezeichnung, Produkten.
    Behandelt zwei Fälle:
      A) "01 Name" auf einer Zeile   (MEASURE_INLINE_RE)
      B) "05" allein, nächste Zeile  (MEASURE_LONE_RE)
    """
    produkte = []
    # 1. Pass: Produktzeilen einsammeln, dann rückwärts nach Nr suchen
    for j in range(anchor_pos - 1, max(0, anchor_pos - 25), -1):
        line = lines[j].strip()
        if not line or is_number(line):
            continue
        if line in SKIP_EXACT or line in YEAR_LABELS or line.startswith("Seite "):
            continue

        # Produktzeile?
        pm = PRODUKT_RE.search(line)
        if pm:
            produkte = [p.strip() for p in re.findall(r"\d{5,6}", pm.group(1))]
            continue

        # Fall A: Inline "01 Bezeichnung"
        m = MEASURE_INLINE_RE.match(line)
        if m and 1 <= int(m.group(1)) <= 80:
            nr = m.group(1) + (m.group(2) or "")
            bz_parts = [m.group(3).strip()]
            # Fortsetzungszeilen (j+1 bis anchor_pos, nicht Skip, nicht Zahl)
            for k in range(j + 1, anchor_pos):
                c = lines[k].strip()
                if c and not is_skip(c) and not is_number(c) and not PRODUKT_RE.search(c):
                    bz_parts.append(c)
            bezeichnung = " ".join(bz_parts).strip()
            return nr, bezeichnung, produkte

        # Fall B: Allein stehende Zahl "05"
        m2 = MEASURE_LONE_RE.match(line)
        if m2 and 1 <= int(m2.group(1)) <= 80:
            nr = m2.group(1) + (m2.group(2) or "")
            # Bezeichnung aus folgenden Zeilen (bis anchor)
            bz_parts = []
            for k in range(j + 1, anchor_pos):
                c = lines[k].strip()
                if c and not is_skip(c) and not is_number(c) and not PRODUKT_RE.search(c):
                    bz_parts.append(c)
            bezeichnung = " ".join(bz_parts).strip()
            return nr, bezeichnung, produkte

    return "", "", produkte


# ── Wert-Sammlung ─────────────────────────────────────────────────────────────

def collect_until_trigger(lines: list[str], start: int, seg_end: int) -> list[float]:
    """Sammelt Zahlzeilen ab start bis zum nächsten Section-Trigger oder seg_end."""
    values = []
    for i in range(start, min(seg_end, start + 30)):
        v = lines[i].strip()
        # Nur echte Section-Header oder Inline-Maßnahmen-Zeilen stoppen die Sammlung.
        # MEASURE_LONE_RE wird bewusst NICHT geprüft: "0" würde sonst fälschlich matchen.
        if v in SECTION_TRIGGERS or MEASURE_INLINE_RE.match(v):
            break
        if is_number(v):
            values.append(parse_eur(v))
        elif v and not is_skip(v):
            break
    return values


def values_to_years(vals: list[float]) -> dict[int, float]:
    """
    Mappt N Werte auf die letzten N Jahres-Slots.
    N=13 → 2013–2025; N=2 → 2024, 2025; N=3 → 2023–2025 usw.
    """
    n = min(len(vals), 13)
    years_slice = YEARS[-n:] if n > 0 else []
    result = {y: 0.0 for y in YEARS}
    for yr, v in zip(years_slice, vals[:n]):
        result[yr] = v
    return result


# ── Anlage XVII a Parser (mit "aus 8. Fortschreibung") ───────────────────────

def parse_anlage17a(doc) -> list[dict]:
    lines = load_lines(doc, ANLAGE17A_PAGES)

    aus8_positions    = [i for i, l in enumerate(lines) if l == "aus 8. Fortschreibung"]
    umgesetzt_set     = {i for i, l in enumerate(lines) if l == "umgesetzter Betrag"}

    measures = []
    for seg_num, pos_8fs in enumerate(aus8_positions):
        seg_end = aus8_positions[seg_num + 1] if seg_num + 1 < len(aus8_positions) else len(lines)

        nr, bezeichnung, produkte = extract_header(lines, pos_8fs)
        if not nr:
            continue

        # "umgesetzter Betrag" innerhalb dieses Segments
        umgesetzt_pos = next(
            (p for p in sorted(umgesetzt_set) if pos_8fs < p < seg_end), None
        )
        umg_vals = []
        if umgesetzt_pos is not None:
            umg_vals = collect_until_trigger(lines, umgesetzt_pos + 1, seg_end)

        # Beschreibungstext (nach den Differenz-Blöcken)
        text_lines = []
        skip_end = (umgesetzt_pos or pos_8fs) + 1 + len(umg_vals) + 27  # ~26 Diff-Zahlen
        for k in range(skip_end, seg_end):
            t = lines[k].strip()
            if t and not is_skip(t) and not is_number(t) and not MEASURE_INLINE_RE.match(t):
                text_lines.append(t)
            if len(text_lines) >= 6:
                break

        measures.append({
            "nr": nr,
            "bezeichnung": bezeichnung,
            "produkte": produkte,
            "umgesetzt_raw": umg_vals,
            "jahr_map": values_to_years(umg_vals),
            "beschreibung": " ".join(text_lines),
        })

    return measures


# ── Anlage XVII b Parser (neue Maßnahmen, kein "aus 8. FS") ──────────────────

def parse_anlage17b_new(doc) -> list[dict]:
    """
    Neue Maßnahmen 68–80: Anker ist "umgesetzter Betrag", kein "aus 8. FS".
    Hier kommen nur wenige Werte (für 2024/2025).
    """
    lines = load_lines(doc, ANLAGE17B_NEW)
    umgesetzt_positions = [i for i, l in enumerate(lines) if l == "umgesetzter Betrag"]

    measures = []
    processed = set()

    for pos in umgesetzt_positions:
        nr, bezeichnung, produkte = extract_header(lines, pos)
        if not nr or nr in processed:
            continue
        if int(nr.rstrip("abcdefghijklmnopqrstuvwxyz")) < 64:
            continue  # Nur 9. FS-Maßnahmen hier

        processed.add(nr)
        umg_vals = collect_until_trigger(lines, pos + 1, len(lines))

        # Beschreibungstext nach den Differenz-Blöcken
        text_lines = []
        skip_end = pos + 1 + len(umg_vals) + 10
        for k in range(skip_end, min(len(lines), skip_end + 50)):
            t = lines[k].strip()
            if t and not is_skip(t) and not is_number(t) and not MEASURE_INLINE_RE.match(t):
                text_lines.append(t)
            if len(text_lines) >= 4:
                break

        measures.append({
            "nr": nr,
            "bezeichnung": bezeichnung,
            "produkte": produkte,
            "umgesetzt_raw": umg_vals,
            "jahr_map": values_to_years(umg_vals),
            "beschreibung": " ".join(text_lines),
        })

    return measures


# ── Nachreichung: fehlende Maßnahmen aus Kap. XVII ───────────────────────────

# Maßnahmen, die im PDF 0-Beträge haben und in Anlage XVII a/b kaum Text besitzen
FALLBACK_MASSNAHMEN = {
    "05":  ("Straßenbeleuchtung Wohnungsbaugesellschaften", ""),
    "15":  ("Elternbeiträge Kindertagesstätten", "365500"),
    "16":  ("Kindertagesstätten Kostenreduzierung", "3655.."),
    "17":  ("Budgets Jugendförderplan", "362010"),
    "54":  ("Bauaufsicht", "521000"),
    "55":  ("Umweltschutz", "561000"),
    "60":  ("Beteiligungen Anteile (Prüfmaßnahme 1)", "625000"),
    "61":  ("Beteiligungen Anteile (Prüfmaßnahme 2)", "625000"),
    "62":  ("Beteiligungen Anteile (Prüfmaßnahme 3)", "625000"),
    "64":  ("Finanzielle Effekte einer Einkreisung", ""),
    "65":  ("Zuweisung gemäß Monitoring-Klausel", ""),
    "66":  ("Verschiebung Projekt Büchereigarten", "511100"),
    "67":  ("Kündigung Vertrag MKGD", "262000"),
    "70":  ("Anpassung Entgeltordnung Waffenmuseum", "252110"),
    "71":  ("Erhöhung Hebesatz Grundsteuer B", "611000"),
    "72":  ("Anhebung Hundesteuersatz", "611000"),
    "74":  ("Neukalkulation Musikschule", "263000"),
    "75":  ("Neukalkulation Volkshochschule", "271000"),
    "76":  ("Neukalkulation Stadtbücherei", "272000"),
    "77":  ("Hortgebühren-Neukalkulation", ""),
    "78":  ("Personalkosten-Einsparung übergreifend", ""),
    "79":  ("Mitarbeiter-Parkplätze Stadtverwaltung", "114110"),
    "80":  ("Anwohner-Parkausweise", "122320"),
}

# Bekannte Jahreswerte für Maßnahmen, die der PDF-Parser nicht vollständig erfasst
FALLBACK_JAHRESWERTE = {
    "66": {2025: 10_000},
    "67": {2024: 32_000, 2025: 32_000},
    "70": {2024: 100_000, 2025: 100_000},
    "71": {2024: 156_000, 2025: 156_000},
    "72": {2024: 20_000, 2025: 20_000},
    "79": {2024: 7_000, 2025: 7_000},
    "80": {2024: 27_000, 2025: 27_000},
}


def apply_fallbacks(measures: list[dict]) -> list[dict]:
    """Fügt fehlende Maßnahmen aus FALLBACK_MASSNAHMEN hinzu."""
    seen_nrs = {m["nr"] for m in measures}
    for nr, (bz, prod) in FALLBACK_MASSNAHMEN.items():
        if nr in seen_nrs:
            continue
        jw = {y: 0.0 for y in YEARS}
        jw.update(FALLBACK_JAHRESWERTE.get(nr, {}))
        measures.append({
            "nr": nr,
            "bezeichnung": bz,
            "produkte": [p for p in prod.split(",") if re.match(r"\d{5,6}", p.strip())],
            "umgesetzt_raw": [],
            "jahr_map": jw,
            "beschreibung": "",
        })
    return measures


# ── Kennzahlen-Berechnung ─────────────────────────────────────────────────────

def compute_amounts(jahr_map: dict[int, float]) -> dict:
    vals = [jahr_map.get(y, 0.0) for y in YEARS]
    return {
        "betrag_kumulativ": sum(vals[0:10]),   # 2013–2022
        "betrag_2023":      vals[10],
        "betrag_2024":      vals[11],
        "betrag_2025":      vals[12],
        "betrag_gesamt":    sum(vals),
    }


def derive_kategorie(bezeichnung: str, produkte: list[str]) -> str:
    b = bezeichnung.lower()
    # Ertragssteigerungen zuerst prüfen (vor Personalcheck, da "steuerstelle" etc.)
    if any(w in b for w in ("steuer", "gebühr", "beitrag", "hebesatz", "abgabe",
                             "gewinnausschüttung", "ausschüttung", "zuweisung",
                             "einnahme", "entgelt", "vollstreckung",
                             "bußgeld", "monitoring", "parkausweise",
                             "hortbeiträge", "elternbeiträge", "entgeltordnung")):
        return "ERTRAG"
    # Personalmaßnahmen (spezifische Begriffe)
    if any(w in b for w in ("personaloptimierung", "personalmanagement",
                             "personalaufwand", "stellenplan", "kw-vermerk",
                             "honorarkräfte", "personalkosten")):
        return "PERSONAL"
    if produkte and all(p.startswith("Kto") for p in produkte if p):
        return "PERSONAL"
    return "AUFWAND"


def derive_status(kumulativ: float, b24: float, b25: float, bezeichnung: str) -> str:
    b = bezeichnung.lower()
    if any(w in b for w in ("prüfmaßnahme", "entfallen", "kein einfluss", "modellrechnung")):
        return "entfallen"
    if b24 != 0 or b25 != 0:
        return "aktiv"
    if kumulativ != 0:
        return "erledigt"
    return "entfallen"


# ── DB-Insert ─────────────────────────────────────────────────────────────────

def insert_into_db(measures: list[dict]) -> None:
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    add_hsk_tables(con)
    con.commit()

    inserted = skipped = 0

    for m in measures:
        amounts = compute_amounts(m["jahr_map"])
        kategorie = derive_kategorie(m["bezeichnung"], m["produkte"])
        status    = derive_status(amounts["betrag_kumulativ"],
                                  amounts["betrag_2024"], amounts["betrag_2025"],
                                  m["bezeichnung"])
        produkte_str = ", ".join(m["produkte"]) if m["produkte"] else None

        try:
            cur = con.execute(
                """INSERT OR REPLACE INTO hsk_massnahmen
                   (nr, bezeichnung, produkte, kategorie, umsetzungsstatus,
                    betrag_kumulativ, betrag_2023, betrag_2024, betrag_2025,
                    betrag_gesamt, beschreibung)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (m["nr"], m["bezeichnung"], produkte_str, kategorie, status,
                 amounts["betrag_kumulativ"], amounts["betrag_2023"],
                 amounts["betrag_2024"], amounts["betrag_2025"],
                 amounts["betrag_gesamt"], m["beschreibung"] or None),
            )
            mid = cur.lastrowid
            for jahr in YEARS:
                betrag = m["jahr_map"].get(jahr, 0.0)
                con.execute(
                    """INSERT OR REPLACE INTO hsk_jahreswerte
                       (massnahme_id, jahr, umgesetzter_betrag) VALUES (?,?,?)""",
                    (mid, jahr, betrag),
                )
            inserted += 1
        except sqlite3.IntegrityError as e:
            print(f"  [WARN] Nr {m['nr']}: {e}", file=sys.stderr)
            skipped += 1

    con.commit()
    con.close()
    print(f"  Eingefügt/ersetzt : {inserted}")
    print(f"  Fehler            : {skipped}")


# ── Validierung ───────────────────────────────────────────────────────────────

def print_summary():
    con = sqlite3.connect(DB_PATH)

    print("\n=== HSK Maßnahmen — Übersicht ===")
    print(f"  {'Kat':<8} {'Status':<11} {'Anz':>4}  {'Kumulativ 2013–22':>18}  {'2024':>12}  {'2025':>12}")
    print("  " + "─" * 70)
    for r in con.execute("""
        SELECT kategorie, umsetzungsstatus, COUNT(*) n,
               SUM(betrag_kumulativ) ku, SUM(betrag_2024) b24, SUM(betrag_2025) b25
        FROM hsk_massnahmen GROUP BY kategorie, umsetzungsstatus
        ORDER BY kategorie, umsetzungsstatus
    """):
        print(f"  {r[0]:<8} {r[1]:<11} {r[2]:>4}  {r[3]:>18,.0f} €  {r[4]:>12,.0f} €  {r[5]:>12,.0f} €")

    tot = con.execute("""
        SELECT COUNT(*) n, SUM(betrag_kumulativ) k, SUM(betrag_2024) b24, SUM(betrag_2025) b25
        FROM hsk_massnahmen
    """).fetchone()
    print(f"\n  GESAMT: {tot[0]} Maßnahmen")
    print(f"  Bereits konsolidiert 2013–2022: {tot[1]:>14,.0f} €")
    print(f"  Aktives Potenzial 2024:         {tot[2]:>14,.0f} €")
    print(f"  Aktives Potenzial 2025:         {tot[3]:>14,.0f} €")

    print("\n=== Top 10 nach Gesamtbetrag ===")
    for r in con.execute("""
        SELECT nr, bezeichnung, betrag_gesamt, betrag_2024, betrag_2025, kategorie, umsetzungsstatus
        FROM hsk_massnahmen ORDER BY betrag_gesamt DESC LIMIT 10
    """):
        print(f"  Nr {r[0]:>3}: {r[1][:42]:<42}  Gesamt {r[2]:>12,.0f} €  "
              f"[{r[5]}/{r[6]}]")

    con.close()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"PDF: {PDF_PATH}")
    print(f"DB : {DB_PATH}\n")

    doc = fitz.open(PDF_PATH)

    print("1. Anlage XVII a (Maßnahmen 01–67)...")
    m_a = parse_anlage17a(doc)
    print(f"   {len(m_a)} Maßnahmen via 'aus 8. FS'-Anker")

    print("2. Anlage XVII b neue Maßnahmen (68–80)...")
    m_b = parse_anlage17b_new(doc)
    print(f"   {len(m_b)} Maßnahmen via 'umgesetzter Betrag'-Anker")

    doc.close()

    # Deduplizieren
    seen = {m["nr"] for m in m_a}
    m_b_neu = [m for m in m_b if m["nr"] not in seen]
    all_measures = m_a + m_b_neu

    print("\n3. Fallback-Maßnahmen ergänzen...")
    before = len(all_measures)
    all_measures = apply_fallbacks(all_measures)
    print(f"   {len(all_measures) - before} Maßnahmen ergänzt (Gesamt: {len(all_measures)})")

    # Sortieren nach Nr
    all_measures.sort(key=lambda m: (int(m["nr"].rstrip("abcdefghijklmnopqrstuvwxyz")),
                                      m["nr"]))

    print("\n4. DB-Insert...")
    insert_into_db(all_measures)

    print("\n5. Validierung...")
    print_summary()


if __name__ == "__main__":
    main()
