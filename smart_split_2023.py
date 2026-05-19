"""
smart_split_2023.py - PDF-Splitting fuer Haushaltsplan Suhl 2023
Manuell definierte Seitenbereiche (PDF hat kein nutzbares internes TOC).
Offset Dokument-Seite → PDF-Seite: +6
"""
import fitz
import os

BASE_DIR = os.path.dirname(__file__)
PDF_PATH = os.path.join(BASE_DIR, "haushalt_suhl_2023.pdf")
OUT_DIR  = os.path.join(BASE_DIR, "pdf_chunks_2023")

# (filename, title, pdf_start_1based, pdf_end_1based, etl_relevant)
CHUNKS = [
    ("00_Gesamtfinanzplan.pdf",      "Gesamtfinanzplan 2023",                    125, 141, False),
    ("tp_01_Verwaltungsfuehrung.pdf", "TP 01 - Verwaltungsführung",              225, 264, True),
    ("tp_02_Kultur_Tourismus_Sport.pdf", "TP 02 - Kultur, Tourismus und Sport",  265, 324, True),
    ("tp_03_Personal_Zentrale_Dienste.pdf", "TP 03 - Personal/Zentrale Dienste", 325, 380, True),
    ("tp_04_Finanzverwaltung.pdf",    "TP 04 - Finanzverwaltung",                381, 408, True),
    ("tp_05_Oeffentliche_Flaechen.pdf", "TP 05 - Öffentliche Flächen und Straßen", 409, 434, True),
    ("tp_06_Allgemeine_Finanzwirtschaft.pdf", "TP 06 - Allgemeine Finanzwirtschaft", 435, 454, True),
    ("tp_07_Ordnung_Sicherheit.pdf",  "TP 07 - Ordnung und Sicherheit",          455, 516, True),
    ("tp_08_Umwelt.pdf",              "TP 08 - Umwelt",                           517, 566, True),
    ("tp_09_Soziales_Gesundheit.pdf", "TP 09 - Soziales und Gesundheit",         567, 702, True),
    ("tp_10_Schultraegeraufgaben.pdf", "TP 10 - Schulträgeraufgaben",            703, 770, True),
    ("tp_11_KJF.pdf",                 "TP 11 - Kinder-, Jugend- und Familienhilfe", 771, 848, True),
    ("tp_12_Einrichtungen.pdf",       "TP 12 - Einrichtungen Sozialdezernat",   849, 864, True),
]


def main():
    if not os.path.exists(PDF_PATH):
        print(f"[FEHLER] PDF nicht gefunden: {PDF_PATH}")
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    doc   = fitz.open(PDF_PATH)
    total = doc.page_count
    print(f"Öffne PDF: {PDF_PATH}  ({total} Seiten)")

    tp_chunks    = [c for c in CHUNKS if c[4]]
    other_chunks = [c for c in CHUNKS if not c[4]]

    print(f"\n[ETL-RELEVANT: {len(tp_chunks)} Teilpläne]")
    for fn, title, s, e, _ in tp_chunks:
        print(f"  S.{s:4d}-{e:4d}  ({e-s+1:3d} S.)  -> {fn}")

    print(f"\n[REFERENZ: {len(other_chunks)} Abschnitte]")
    for fn, title, s, e, _ in other_chunks:
        print(f"  S.{s:4d}-{e:4d}  ({e-s+1:3d} S.)  -> {fn}")

    print(f"\nSpeichere nach: {OUT_DIR}")
    for fn, title, s, e, etl in CHUNKS:
        out_doc = fitz.open()
        out_doc.insert_pdf(doc, from_page=s - 1, to_page=e - 1)
        out_path = os.path.join(OUT_DIR, fn)
        out_doc.save(out_path, garbage=4, deflate=True)
        out_doc.close()
        tag = "[ETL]" if etl else "[REF]"
        print(f"  {tag} {title[:55]:55s} -> {fn}")

    doc.close()
    print(f"\nFertig. {len(tp_chunks)} TP-Chunks + {len(other_chunks)} Referenz-Chunks.")


if __name__ == "__main__":
    main()
