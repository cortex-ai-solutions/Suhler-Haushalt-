"""
repair_konten_bezeichnungen.py — Backfill fuer abgeschnittene Kontobezeichnungen

Root Cause (behoben in pipeline.py/_2023/_2024/_2026, siehe extract_page()):
  1. Feste x-Schwelle (125 bzw. 100) zur Abgrenzung Kontocode/Bezeichnung war bei
     laengeren Sub-Kontocodes zu weit rechts angesetzt -> erstes Bezeichnungswort
     wurde abgeschnitten (betraf praktisch jede Kontobezeichnung).
  2. Ueber zwei PDF-Zeilen umgebrochene Bezeichnungen wurden nur einzeilig erfasst
     (~9,5% der Konten, endet auf eine deutsche Praeposition).

Der Pipeline-Fix wirkt nur fuer NEUE Importe. Die bereits in `konten` gespeicherten
Bezeichnungen wurden per INSERT OR IGNORE beim allerersten Sehen des Kontos fixiert
und werden nie aktualisiert (siehe get_konto_id()). Dieses Skript liest darum mit den
(gefixten) Extract-Funktionen aller vier Pipeline-Module erneut die PDF-Chunks und
aktualisiert NUR die Text-Spalte `konten.bezeichnung` -- `haushaltswerte`,
`migration_status` und `produkte` werden nicht beruehrt.

Sicherheitsregeln fuer ein Update:
  - der aktuell gespeicherte Text muss ein Praefix des neu gefundenen Textes sein
    (verhindert Zuordnung zu falschem/unzusammenhaengendem Text)
  - der neue Zusatz darf keine Ziffern und keine Kopf-/Fusszeilen-Token enthalten
    ("Seite", "IST", "PLAN", "ANSATZ", nackte Jahreszahlen 20xx)
  - der Zusatz ist maximal 80 Zeichen lang

Modus:
  python repair_konten_bezeichnungen.py            -> Dry-Run, nur Diff-Report
  python repair_konten_bezeichnungen.py --apply     -> nach Sichtung des Reports:
                                                        UPDATE tatsaechlich ausfuehren
"""
import io
import os
import re
import sys
import glob
import sqlite3
import importlib
from datetime import datetime

import pdfplumber

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "suhl_haushalt_2025.db")

sys.path.insert(0, BASE_DIR)

# (Modulname, Teilplan-Chunk-Ordner) -- GESAMT_FP-Konstanten werden je Modul
# direkt aus dem importierten Modul gelesen (module.GESAMT_FINANZPLAN_CHUNK etc.)
PIPELINE_MODULES = [
    ("pipeline",      "pdf_chunks"),
    ("pipeline_2023", "pdf_chunks_2023"),
    ("pipeline_2024", "pdf_chunks_2024"),
    ("pipeline_2026", "pdf_chunks_2026"),
]

# Suffix-Sicherheitsfilter: verbotene Muster im NEUEN Textzusatz
BAD_SUFFIX_RE = re.compile(
    r"\d|Seite\b|IST\b|PLAN\b|ANSATZ\b|\b20\d{2}\b", re.IGNORECASE
)
MAX_SUFFIX_LEN = 80

# decode_cid() liefert ASCII-Transliterationen (ue/oe/ae/ss). Bereits in der DB
# gespeicherter Text stammt teils aus PDF-Stellen, die pdfplumber direkt als
# echtes Unicode ("ü") extrahiert hat -- derselbe Wortlaut sieht dann je nach
# Quelle unterschiedlich aus. Fuer den reinen VERGLEICH beide Seiten auf ASCII
# normalisieren; als neuer Wert wird der komplette (in sich konsistente)
# Kandidat uebernommen statt einer Teilspleissung aus zwei Schreibweisen.
_UMLAUT_MAP = str.maketrans({
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
})


def _norm(s: str) -> str:
    return s.translate(_UMLAUT_MAP)


def harvest_bezeichnungen(fail_log) -> dict:
    """Sammelt {konto_nummer: [kandidat, ...]} ueber alle 4 Jahrgaenge/Chunks."""
    candidates: dict[str, list[str]] = {}

    def add(konto7: str, bez: str):
        bez = (bez or "").strip()
        if not bez:
            return
        candidates.setdefault(konto7, []).append(bez)

    for modname, chunks_dir in PIPELINE_MODULES:
        mod = importlib.import_module(modname)
        chunks_path = os.path.join(BASE_DIR, chunks_dir)

        # TP-Chunks
        for tpf in sorted(glob.glob(os.path.join(chunks_path, "tp_*.pdf"))):
            with pdfplumber.open(tpf) as pdf:
                for i, page in enumerate(pdf.pages):
                    label = f"{modname}:{os.path.basename(tpf)}:p{i+1}"
                    for r in mod.extract_page(page, fail_log, label):
                        add(r["konto7"], r["konto_bez"])

        # Gesamtproduktplan-Finanzplan-Chunk (KK6/7)
        gfp_path = mod.GESAMT_FINANZPLAN_CHUNK
        if os.path.exists(gfp_path):
            with pdfplumber.open(gfp_path) as pdf:
                end_page = min(mod.GESAMT_FP_END_PAGE + 1, len(pdf.pages))
                for pg_idx in range(mod.GESAMT_FP_START_PAGE, end_page):
                    label = f"{modname}:GESAMT_FP:p{pg_idx+1}"
                    for r in mod.extract_page_gesamt(pdf.pages[pg_idx], fail_log, label):
                        add(r["konto7"], r["konto_bez"])

        print(f"  [{modname}] verarbeitet")

    return candidates


def best_extension(current: str, kandidaten: list) -> str | None:
    """
    Waehlt aus den Kandidaten den laengsten, der `current` vollstaendig
    enthaelt (als Praefix, Suffix, oder in der Mitte -- der haeufigste Fall
    ist eine fehlende ERSTE Wort ganz am Anfang, z.B. "und Zuschuesse..."
    statt "Zuweisungen und Zuschuesse..."). Beide moeglichen Zusaetze
    (davor UND danach) muessen einzeln die Sicherheitsfilter bestehen.

    Vergleich erfolgt umlaut-normalisiert (ue/oe/ae/ss vs. ü/ö/ä/ß), da
    `current` (bereits in der DB) und `k` (frisch von decode_cid erzeugt,
    das ASCII transliteriert) je nach urspruenglicher PDF-Textquelle
    unterschiedliche Schreibweise haben koennen. Bei Treffer wird der
    ORIGINALE Kandidat `k` unveraendert uebernommen (nicht zusammengespleisst),
    damit das Ergebnis in sich konsistent in EINER Schreibweise bleibt.

    None, falls kein gueltiger Kandidat laenger als `current` ist.
    """
    current = (current or "").strip()
    if len(current) < 4:
        return None  # zu kurz/unspezifisch fuer einen sicheren Substring-Treffer
    norm_current = _norm(current)
    best = None
    for k in kandidaten:
        if len(k) <= len(current):
            continue
        norm_k = _norm(k)
        idx = norm_k.find(norm_current)
        if idx < 0:
            continue
        prefix_add = norm_k[:idx].strip()
        suffix_add = norm_k[idx + len(norm_current):].strip()
        if not prefix_add and not suffix_add:
            continue
        if len(prefix_add) > MAX_SUFFIX_LEN or len(suffix_add) > MAX_SUFFIX_LEN:
            continue
        if prefix_add and BAD_SUFFIX_RE.search(prefix_add):
            continue
        if suffix_add and BAD_SUFFIX_RE.search(suffix_add):
            continue
        if best is None or len(k) > len(best):
            best = k
    return best


def main():
    apply_mode = "--apply" in sys.argv

    print(f"repair_konten_bezeichnungen.py — gestartet {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Modus: {'APPLY (schreibt in DB)' if apply_mode else 'DRY-RUN (nur Report)'}")
    print()

    fail_log = io.StringIO()

    print("Schritt 1: Kandidaten aus allen 4 Jahrgaengen einsammeln...")
    candidates = harvest_bezeichnungen(fail_log)
    print(f"  {len(candidates)} unterschiedliche Kontonummern mit mind. 1 Kandidat")
    if fail_log.getvalue():
        print(f"  Hinweis: {len(fail_log.getvalue().splitlines())} Parse-Warnungen (siehe Fail-Log unten)")
    print()

    print("Schritt 2: Gegen aktuelle DB-Bezeichnungen abgleichen...")
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    updates = []  # (konto_nummer, alt, neu)
    for row in con.execute("SELECT konto_nummer, bezeichnung FROM konten ORDER BY konto_nummer"):
        konto7 = row["konto_nummer"]
        current = row["bezeichnung"]
        kandidaten = candidates.get(konto7, [])
        neu = best_extension(current, kandidaten)
        if neu:
            updates.append((konto7, current, neu))

    print(f"  {len(updates)} Konten mit gueltiger, sicherer Textverlaengerung")
    print()

    print("=" * 78)
    print("DIFF-REPORT (alt -> neu)")
    print("=" * 78)
    for konto7, alt, neu in updates:
        print(f"  {konto7}:")
        print(f"    alt: {alt!r}")
        print(f"    neu: {neu!r}")
    print("=" * 78)
    print(f"Gesamt: {len(updates)} Konten wuerden aktualisiert.")
    print()

    if not apply_mode:
        print("[DRY-RUN] Keine Aenderung geschrieben. Zum Anwenden nach Sichtung:")
        print("  python repair_konten_bezeichnungen.py --apply")
        con.close()
        return

    print("Schritt 3: UPDATE ausfuehren...")
    for konto7, alt, neu in updates:
        con.execute(
            "UPDATE konten SET bezeichnung = ? WHERE konto_nummer = ? AND bezeichnung = ?",
            (neu, konto7, alt),
        )
    con.commit()
    changed = con.total_changes
    print(f"  {len(updates)} UPDATE-Statements ausgefuehrt (con.total_changes={changed})")
    con.close()
    print()
    print("[OK] Fertig. Bitte anschliessend: python generate_json.py")


if __name__ == "__main__":
    main()
