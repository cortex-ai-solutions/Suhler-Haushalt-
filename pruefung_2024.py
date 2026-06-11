"""
Prüfung 2024 KK6/7 — Verifiziert Root Causes:
1. Konten bei x<65 fehlen in DB (Threshold-Problem)
2. Konten bei x>=65 haben falsches Jahr/wert_typ (Column-Offset-Problem)
3. Konten auf Seiten >41 fehlen komplett (END_PAGE-Problem)
"""
import sqlite3
import pdfplumber
import re

PDF_PATH = r"pdf_chunks_2024\00_3_Gesamtproduktplan.pdf"
DB_PATH  = "suhl_haushalt_2025.db"
PLAIN_KONTO_RE = re.compile(r"^(\d{7})$")

# Seiten 35-43 (0-basiert): abwechselnd sichtbar/unsichtbar + jenseits END_PAGE
TEST_PAGES = [34, 35, 36, 37, 38, 39, 40, 41, 42, 43]  # 0-basiert

def extract_konten_from_page(page):
    """Gibt Liste von (konto_nr, x0, werte_dict) zurück."""
    words  = page.extract_words()
    rows   = page.extract_words()
    result = []

    # Nach Konto-Nummern suchen (7-stellig, beginnt mit 6 oder 7)
    for w in rows:
        if not PLAIN_KONTO_RE.match(w["text"]):
            continue
        if w["text"][0] not in ("6", "7"):
            continue
        if w["text"][:2] in ("68", "69", "78", "79"):
            continue
        result.append((w["text"], round(w["x0"], 1)))

    return result

def check_db(conn, konto_nr):
    """Gibt alle haushaltswerte-Zeilen für dieses Konto zurück."""
    cur = conn.cursor()
    cur.execute("""
        SELECT hv.haushaltsplan_jahr, hv.daten_jahr, hv.wert_typ, hv.betrag,
               k.konto_nummer
        FROM haushaltswerte hv
        JOIN konten k ON k.id = hv.konto_id
        WHERE k.konto_nummer = ?
          AND hv.haushaltsplan_jahr = 2024
        ORDER BY hv.daten_jahr, hv.wert_typ
    """, (konto_nr,))
    return cur.fetchall()

def main():
    conn = sqlite3.connect(DB_PATH)

    print("=" * 70)
    print("PRÜFUNG 2024 — Root Cause Verifikation")
    print("=" * 70)

    # Sammle Beispiel-Konten: je 3 aus sichtbaren und unsichtbaren Seiten
    visible_samples   = []  # x >= 65
    invisible_samples = []  # x < 65
    out_of_range_samples = []  # jenseits END_PAGE=40

    with pdfplumber.open(PDF_PATH) as pdf:
        for pg_idx in TEST_PAGES:
            if pg_idx >= len(pdf.pages):
                break
            page = pdf.pages[pg_idx]
            konten = extract_konten_from_page(page)

            in_range = pg_idx <= 40  # END_PAGE=40 (0-basiert)
            tag = "IN " if in_range else "OUT"

            for konto_nr, x0 in konten:
                entry = (konto_nr, x0, pg_idx + 1)  # +1 für 1-basierte Seitennr.
                if not in_range:
                    if len(out_of_range_samples) < 4:
                        out_of_range_samples.append(entry)
                elif x0 < 65:
                    if len(invisible_samples) < 4:
                        invisible_samples.append(entry)
                else:
                    if len(visible_samples) < 4:
                        visible_samples.append(entry)

            if len(visible_samples) >= 4 and len(invisible_samples) >= 4 and len(out_of_range_samples) >= 4:
                break

    print()
    print("=" * 70)
    print("A) Konten auf SICHTBAREN Seiten (x >= 65, IN RANGE) — sollten in DB sein")
    print("   aber möglicherweise mit falschem Jahr/wert_typ wegen Column-Offset")
    print("=" * 70)
    for konto_nr, x0, pg in visible_samples:
        rows = check_db(conn, konto_nr)
        print(f"  Konto {konto_nr}  x={x0}  Seite {pg}")
        if rows:
            for r in rows:
                print(f"    DB: hh_jahr={r[0]}, daten_jahr={r[1]}, wert_typ={r[2]}, betrag={r[3]:>15,.2f}")
        else:
            print(f"    DB: -- NICHT IN DB -- (haushaltsplan_jahr=2024)")

    print()
    print("=" * 70)
    print("B) Konten auf UNSICHTBAREN Seiten (x < 65, IN RANGE) — sollten FEHLEN")
    print("=" * 70)
    for konto_nr, x0, pg in invisible_samples:
        rows = check_db(conn, konto_nr)
        print(f"  Konto {konto_nr}  x={x0}  Seite {pg}")
        if rows:
            print(f"    DB: UNERWARTET VORHANDEN — {len(rows)} Zeile(n)")
            for r in rows:
                print(f"       hh_jahr={r[0]}, daten_jahr={r[1]}, wert_typ={r[2]}, betrag={r[3]:>15,.2f}")
        else:
            print(f"    DB: -- FEHLT (korrekt: sollte fehlen) --")

    print()
    print("=" * 70)
    print("C) Konten JENSEITS END_PAGE (Seiten 42+) — sollten komplett fehlen")
    print("=" * 70)
    for konto_nr, x0, pg in out_of_range_samples:
        rows = check_db(conn, konto_nr)
        print(f"  Konto {konto_nr}  x={x0}  Seite {pg}")
        if rows:
            print(f"    DB: UNERWARTET VORHANDEN — {len(rows)} Zeile(n)")
        else:
            print(f"    DB: -- FEHLT (korrekt: sollte fehlen) --")

    print()
    print("=" * 70)
    print("D) Column-Offset Check: Konto 6xxx von sichtbarer Seite — welches daten_jahr?")
    print("   PLAN_ANSATZ 2024 sollte als ANSATZ_VORJAHR daten_jahr=2023 gespeichert sein")
    print("=" * 70)
    for konto_nr, x0, pg in visible_samples:
        rows = check_db(conn, konto_nr)
        if rows:
            for r in rows:
                if r[2] == "ANSATZ_VORJAHR" and r[1] == 2023:
                    print(f"  Konto {konto_nr}: ANSATZ_VORJAHR/2023 mit Betrag {r[3]:>15,.2f}")
                    print(f"    --> In Wirklichkeit: PLAN_ANSATZ 2024 (Column-Offset-Fehler bestaetigt)")
                elif r[2] == "PLAN_ANSATZ" and r[1] == 2024:
                    print(f"  Konto {konto_nr}: PLAN_ANSATZ/2024 mit Betrag {r[3]:>15,.2f}")
                    print(f"    --> Korrekt gespeichert (kein Column-Offset-Problem hier)")

    conn.close()
    print()
    print("Pruefung abgeschlossen.")

if __name__ == "__main__":
    main()
