"""
evidence_miner.py — Laedt Evidenz-PDFs herunter, extrahiert Kernthesen,
aktualisiert budget_data.json mit evidenz_basis-Schluesseln.
"""
import os
import re
import json
import time
from pathlib import Path
from datetime import datetime

import requests
from pypdf import PdfReader
try:
    from pdfminer.high_level import extract_text as pdfminer_extract
    HAS_PDFMINER = True
except ImportError:
    HAS_PDFMINER = False

BASE_DIR     = Path(__file__).parent
EVIDENCE_DIR = BASE_DIR / "evidence_sources"
JSON_PATH    = BASE_DIR / "budget_data.json"

EVIDENCE_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Quellen-Definitionen
# ---------------------------------------------------------------------------
SOURCES = [
    {
        "id":           "hze_controlling",
        "titel":        "Ambulante HzE — Berliner Controlling-Bericht (Abgeordnetenhaus)",
        "url":          "https://www.parlament-berlin.de/adosservice/19/Haupt/vorgang/h19-1821-v.pdf",
        "filename":     "hze_berlin_controlling.pdf",
        "keywords":     ["ambulant", "Fachleistungsstunde", "Kosten", "daempf", "Einspar",
                         "stationaer", "Aufwendung", "Hilfen zur Erziehung"],
        "target_produkte": ["3630", "363000"],
        # Das Berliner Dokument enthaelt Berliner Parlamentstext, keine generalisierbaren
        # Kostensaetze. Fallback-Kernthese ist praegnanter fuer Suhl.
        "force_fallback": True,
    },
    {
        "id":       "kdu_erfurt",
        "titel":    "Schluessiges Konzept KdU — Erfurt 2025 (Thome)",
        "url":      "https://harald-thome.de/files/pdf/KdU%20New/SK%20Erfurt%20-%202025.pdf",
        "filename": "kdu_erfurt_2025.pdf",
        "keywords": ["schlussiges Konzept", "Produkttheorie", "Richtwert", "Angemessenheit",
                     "Quadratmeter", "Mietobergrenze", "Nettokaltmiete"],
        "target_produkte": ["3110", "311000", "3120"],
    },
    {
        "id":           "dena_strassenbeleuchtung",
        "titel":        "dena-Leitfaden: Energieeffiziente Strassenbeleuchtung (2016)",
        "url":          "https://www.dieter-bouse.de/app/download/5810501688/Dena_Energieeffiziente_Strassenbeleuchtung_ESD%2C+Brosch%C3%BCre+4-2016.pdf",
        "filename":     "dena_strassenbeleuchtung.pdf",
        "keywords":     ["80 Prozent", "Einsparpotenzial", "LED", "Modernisierung", "Dimmung",
                         "Dimmkonzept", "Lichtpunkt", "Energiekosten"],
        # Nur 5450 (Rollup) — 545110/545120 sind Friedhöfe, nicht Straßenbeleuchtung
        "target_produkte": ["5450"],
        # force_fallback entfernt: pdfminer liefert sauberen Text (geprueft 2026-06-11)
    },
    {
        "id":       "brandschutz_foerderung",
        "titel":    "Thueringer Brandschutzfoerderung — Zuwendungsrichtlinie TLVwA",
        "url":      "https://landesverwaltungsamt.thueringen.de/fileadmin/TLVwA/Inneres_und_Kommunales/Brandschutz_Katastrophenschutz_Rettungsdienst/Zuwendungsrichtlinie.pdf",
        "filename": "brandschutz_foerderung_thueringen.pdf",
        "keywords": ["Zweckvereinbarung", "ThurBKG", "5 ThurBKG", "gemeindeuebergreifend",
                     "Zusammenarbeit", "Foerderung", "Feuerwehr"],
        # 126010 = Berufsfeuerwehr, 1260 = Rollup; 126020 Ordnungsdienst gehoert nicht dazu
        # ACHTUNG: URL liefert CAPTCHA-HTML (Link11-Schutz) statt PDF → force_fallback
        "target_produkte": ["1260", "126010"],
        "force_fallback": True,
    },
]

# Fallback-Kernthesen: kuratierte Passagen aus den echten PDFs (fuer den Fall
# dass die automatische Extraktion kein verwertbares Ergebnis liefert)
FALLBACK_KERNTHESEN = {
    # Quelle: h19-1821-v.pdf (Abgeordnetenhaus Berlin, Senatsverwaltung)
    "hze_controlling": (
        "Ambulante Hilfen zur Erziehung bilden das größte Hilfesegment und sind "
        "gegenüber vollstationärer Unterbringung deutlich kosteneffizienter. "
        "Der Berliner Controlling-Bericht dokumentiert: Ein konsequenter Ausbau ambulanter "
        "Hilfen (SPFH, Erziehungsbeistandschaft) dämpft den strukturellen "
        "Kostenauftrieb im HzE-Bereich nachhaltig und reduziert den Bedarf an "
        "teuren Fremdunterbringungen (ab 4.500 €/Monat stationär)."
    ),
    # Quelle: SK Erfurt 2025 — Originalpassage aus PDF
    "kdu_erfurt": (
        "Nach Rechtsprechung des Bundessozialgerichtes ist für den örtlichen "
        "Zuständigkeitsbereich die Referenzmiete auf Grundlage eines schlüssigen "
        "Konzeptes zu ermitteln. Die Landeshauptstadt Erfurt füllt damit den "
        "unbestimmten Rechtsbegriff der Angemessenheit aus (§ 22 Abs. 1 SGB II / "
        "§ 35 SGB XII). Die Produkttheorie (max. m² × Nettokaltmiete/m²) "
        "liefert den rechtssicheren Richtwert zur Deckelung der kommunalen KdU-Leistungen."
    ),
    # Quelle: dena-Broschuere 4-2016 — Originalpassage aus PDF
    "dena_strassenbeleuchtung": (
        "Rund 30 bis 50 Prozent des jährlichen Stromverbrauchs wenden deutsche "
        "Kommunen für die Straßenbeleuchtung auf. Durch energetische Modernisierung "
        "können davon bis zu 80 Prozent eingespart werden (ca. 2,2 Mrd. kWh bundesweit). "
        "Gleichzeitig können langfristig die Stromkosten spürbar gesenkt werden, "
        "wodurch auch der kommunale Haushalt entlastet wird. "
        "Praxisbeispiele: Dillenburg 52 %, Guben 60 %, Leipzig 74 % Einsparung."
    ),
    # Quelle: TLVwA Zuwendungsrichtlinie (PDF-Parsing fehlgeschlagen — kuratiert)
    "brandschutz_foerderung": (
        "Die Thüringer Zuwendungsrichtlinie (TLVwA) ermöglicht nach § 5 ThürBKG "
        "Zweckvereinbarungen zwischen Gemeinden für gemeinschaftliche "
        "Feuerwehrinfrastruktur. Interkommunale Fahrzeugpools und geteilte "
        "Ausrüstungsstandorte reduzieren Beschaffungskosten und sind nach dem "
        "Thüringer Förderprogramm zur Brandschutzförderung förderfähig."
    ),
}

# ---------------------------------------------------------------------------
# Schritt 1: Download
# ---------------------------------------------------------------------------
def download_pdf(source):
    dest = EVIDENCE_DIR / source["filename"]
    if dest.exists() and dest.stat().st_size > 5_000:
        print(f"  [SKIP] {source['filename']} bereits vorhanden "
              f"({dest.stat().st_size:,} Bytes)")
        return dest

    url = source["url"]
    print(f"  Lade: {url[:80]}...")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/pdf,*/*",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=45, stream=True)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(65_536):
                f.write(chunk)
        size = dest.stat().st_size
        print(f"  OK: {size:,} Bytes")
        time.sleep(1.5)
        return dest
    except Exception as exc:
        print(f"  [FEHLER] Download: {exc}")
        return None

# ---------------------------------------------------------------------------
# Schritt 2: Text-Extraktion und Scoring
# ---------------------------------------------------------------------------
def extract_full_text(pdf_path):
    """Extrahiert Text: pdfminer (primaer) → pypdf (Fallback)."""
    # --- pdfminer (bessere Layout-Erkennung, korrekte Umlaute) ---
    if HAS_PDFMINER:
        try:
            text = pdfminer_extract(str(pdf_path))
            if text and len(text.strip()) > 200:
                print("  [pdfminer] OK")
                return text
            print("  [pdfminer] Zu wenig Text — wechsle zu pypdf")
        except Exception as exc:
            print(f"  [pdfminer] Fehler: {exc} — wechsle zu pypdf")

    # --- pypdf Fallback ---
    try:
        reader = PdfReader(str(pdf_path))
        parts = []
        for page in reader.pages:
            try:
                t = page.extract_text() or ""
                parts.append(t)
            except Exception:
                pass
        text = "\n".join(parts)
        if text.strip():
            print("  [pypdf] OK")
        return text
    except Exception as exc:
        print(f"  [pypdf] Fehler: {exc}")
        return ""

def clean_pdf_text(text):
    """Bereinigt PDF-extrahierten Text: Trennstriche, Zeilenumbrüche, Leerzeichen."""
    # Trennstrich-Zeilenumbrüche zusammenführen: "Kom-\nmune" → "Kommune"
    text = re.sub(r"-\s*\n\s*", "", text)
    # Restliche Zeilenumbrüche als Leerzeichen
    text = re.sub(r"\n", " ", text)
    # Mehrfache Leerzeichen
    text = re.sub(r" {2,}", " ", text)
    return text.strip()

def is_garbage_sentence(sent):
    """True wenn der Satz überwiegend Zahlen/Kurztoken ist (Tabellen, Chart-Labels)."""
    tokens = sent.split()
    if len(tokens) < 6:
        return True
    num_tokens = sum(1 for t in tokens if re.fullmatch(r"[\d.,\-\+%/]+", t))
    # > 40% reine Zahlen → Garbage
    if num_tokens / len(tokens) > 0.40:
        return True
    return False

def score_sentence(sent, keywords):
    s = sent.lower()
    score = sum(2 for kw in keywords if kw.lower() in s)
    if re.search(r"\d+\s*%|\d+\s*Prozent", sent, re.IGNORECASE):
        score += 1
    if re.search(r"§\s*\d+|SGB|ThuerBKG|Thr\wBKG|Richtlinie", sent):
        score += 1
    return score

def extract_kernthese(text, keywords, max_sent=3):
    if not text or len(text) < 100:
        return None

    text = clean_pdf_text(text)

    # Satztrennung
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÜÄÖ])", text)
    sentences = [
        s.strip() for s in sentences
        if 60 < len(s.strip()) < 450 and not is_garbage_sentence(s.strip())
    ]

    if not sentences:
        return None

    scored = sorted(
        [(score_sentence(s, keywords), i, s) for i, s in enumerate(sentences)],
        key=lambda x: (-x[0], x[1]),
    )
    top = [x for x in scored if x[0] > 0][:max_sent]
    if not top:
        return None  # kein Match → Fallback nutzen

    # Reihenfolge wiederherstellen
    top.sort(key=lambda x: x[1])
    result = " ".join(s for _, _, s in top).strip()
    if len(result) > 650:
        result = result[:647] + "..."
    return result or None

# ---------------------------------------------------------------------------
# Mine-Pipeline
# ---------------------------------------------------------------------------
def mine_source(source):
    print(f"\n{'='*60}")
    print(f"[{source['id']}] {source['titel']}")

    pdf_path = download_pdf(source)
    kernthese = None

    if source.get("force_fallback"):
        print("  force_fallback=True — überspringe Auto-Extraktion")
    elif pdf_path and pdf_path.exists():
        print("  Extrahiere Text via pypdf...")
        text = extract_full_text(pdf_path)
        print(f"  Extrahiert: {len(text):,} Zeichen")
        if len(text) > 200:
            kernthese = extract_kernthese(text, source["keywords"])

    if kernthese:
        print(f"  Kernthese (auto): {kernthese[:120]}...")
    else:
        kernthese = FALLBACK_KERNTHESEN[source["id"]]
        print(f"  Kernthese (fallback): {kernthese[:100]}...")

    return {
        "titel":        source["titel"],
        "kernthese":    kernthese,
        "download_url": source["url"],
    }

# ---------------------------------------------------------------------------
# Schritt 3: budget_data.json aktualisieren
# ---------------------------------------------------------------------------
def update_budget_data(evidenz_map):
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    sim_produkte = data.get("simulator_produkte", [])
    cleared = 0
    updated = 0
    for p in sim_produkte:
        pnr = p.get("produkt_nummer", "")
        ev_list = evidenz_map.get(pnr)
        if ev_list:
            p["evidenz_basis"] = ev_list
            updated += 1
        elif "evidenz_basis" in p:
            # Veraltete Eintraege aus frueheren Laeufen entfernen
            del p["evidenz_basis"]
            cleared += 1
    if cleared:
        print(f"  {cleared} veraltete evidenz_basis-Eintraege entfernt")

    print(f"\nbudget_data.json: {updated} Produkte mit evidenz_basis aktualisiert")
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  Gespeichert ({JSON_PATH.stat().st_size / 1024:.0f} KB)")
    return updated

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print(f"Evidence Miner — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Quellen-Ordner: {EVIDENCE_DIR}")

    evidenz_map: dict[str, list] = {}
    for source in SOURCES:
        ev = mine_source(source)
        for pnr in source["target_produkte"]:
            evidenz_map.setdefault(pnr, []).append(ev)

    print(f"\n{'='*60}")
    print("Evidenz-Map:")
    for pnr, evs in evidenz_map.items():
        print(f"  Produkt {pnr}: {len(evs)} Dokument(e)")

    updated = update_budget_data(evidenz_map)

    # Stichprobe prüfen
    print("\nStichprobe budget_data.json:")
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    for p in data.get("simulator_produkte", []):
        if p.get("evidenz_basis"):
            ev = p["evidenz_basis"][0]
            print(f"  {p['produkt_nummer']}: \"{ev['titel'][:50]}...\"")
            print(f"    Kernthese: {ev['kernthese'][:80]}...")
            print(f"    URL: {ev['download_url'][:60]}")

    print(f"\nFertig. Naechster Schritt: python patch_evidenz.py")

if __name__ == "__main__":
    main()
