#!/usr/bin/env python3
"""
budget_query.py — OpenClaw CLI-Skill: Haushaltsplan Stadt Suhl

Aufruf:
  python budget_query.py "Wie viel hat Suhl 2025 fuer Soziales ausgegeben?"
  python budget_query.py "Top 5 Ausgaben 2025"
  python budget_query.py --json "Soziales 2023 vs 2025"

Umgebungsvariable:
  BUDGET_DB_PATH  Pfad zur SQLite-DB (Standard: /opt/omni-haushalt/suhl_haushalt.db)

Verbesserungen ggü. CLAUDE.md-Plan:
  - Dynamische Jahreserkennung (kein Hardcode)
  - Erweiterte Keyword-Liste (tourismus, gesundheit, famili, feuerwehr, ...)
  - KK5-Ground-Truth-Override (§1 Haushaltssatzung) fuer offizielle Jahressummen
  - Rechtsgrundlagen-Ausgabe bei Produktabfragen
  - IST-Daten 2021/2022/2023 verfuegbar (mehr als im Plan dokumentiert)
  - Steuerungskategorie-Abfragen
  - Beste Werttyp-Auswahl je Jahr automatisch
"""

import sys
import os
import re
import sqlite3
import json

# ── Konfiguration ─────────────────────────────────────────────────────────────

DB_PATH = os.environ.get(
    "BUDGET_DB_PATH",
    "/opt/omni-haushalt/suhl_haushalt.db"
)

# §1 Haushaltssatzung — offizielle Summen als Ground Truth
# KK5 weicht in der DB um ~4,3% ab (Innere Leistungsverrechnungen 58xxxxx)
# KK4/6/7 passen auf <0,2% — wir zeigen trotzdem immer den offiziellen Wert
GROUND_TRUTH = {
    2025: {4: 136_395_290, 5: 138_003_230, 6: 136_365_830, 7: 135_802_480},
    2024: {4: 130_353_020, 5: 133_802_080, 6: 124_398_580, 7: 123_750_200},
}

# Werttyp-Labels fuer die Ausgabe
WERT_TYP_LABELS = {
    "PLAN_ANSATZ":    "Planansatz",
    "IST_ERGEBNIS":   "Ist-Ergebnis",
    "ANSATZ_VORJAHR": "Ansatz Vorjahr",
    "FINANZPLANUNG":  "Finanzplanung",
}

# Teilplan-Keyword-Mapping (Kleinbuchstaben, Substring-Match)
TEILPLAN_KEYWORDS = {
    "verwaltung":       ["01"],
    "stadtrat":         ["01"],
    "buergermeister":   ["01"],
    "bürgermeister":    ["01"],
    "kultur":           ["02"],
    "tourismus":        ["02"],
    "sport":            ["02"],
    "personal":         ["03"],
    "zentrale dienste": ["03"],
    "finanzverwaltung": ["04"],
    "kaemmerei":        ["04"],
    "kämmer":           ["04"],
    "steueramt":        ["04"],
    "strasse":          ["05"],
    "straße":           ["05"],
    "verkehr":          ["05"],
    "infrastruktur":    ["05"],
    "flaeche":          ["05"],
    "fläche":           ["05"],
    "bauhof":           ["05"],
    "finanzwirtschaft": ["06"],
    "ordnung":          ["07"],
    "sicherheit":       ["07"],
    "feuerwehr":        ["07"],
    "umwelt":           ["08"],
    "natur":            ["08"],
    "abfall":           ["08"],
    "abwasser":         ["08"],
    "sozial":           ["09", "12"],
    "gesundheit":       ["09"],
    "schule":           ["10"],
    "schulen":          ["10"],
    "bildung":          ["10"],
    "kinder":           ["11"],
    "jugend":           ["11"],
    "kita":             ["11"],
    "krippe":           ["11"],
    "famili":           ["11"],
    "jugendhilfe":      ["11"],
    "einrichtung":      ["12"],
    "sozialdezernat":   ["12"],
}

# Kontenklasse-Keyword-Mapping
KONTENKLASSE_KEYWORDS = {
    "ertrag":          4,
    "ertraege":        4,
    "erträge":         4,
    "einnahme":        4,
    "einnahmen":       4,
    "steuereinnahmen": 4,
    "zuweisungen":     4,
    "aufwand":         5,
    "aufwendungen":    5,
    "ausgabe":         5,
    "ausgaben":        5,
    "kosten":          5,
    "einzahlung":      6,
    "einzahlungen":    6,
    "auszahlung":      7,
    "auszahlungen":    7,
    "investition":     7,
    "investitionen":   7,
}

# Steuerungskategorie-Keyword-Mapping
SK_KEYWORDS = {
    "PFLICHT_STRIKT":    ["pflicht", "zwingend", "rechtsanspruch", "einklagbar"],
    "PFLICHT_ERMESSEN":  ["pflicht ermessen", "pflichtaufgabe mit ermessen"],
    "FREIWILLIG":        ["freiwillig", "freiwillige", "kür", "optional", "gestaltungsspielraum"],
    "UEBERTRAGEN":       ["übertragen", "uebertragen", "auftragsangelegenheit", "konnexität"],
}

# Stellenplan-Keywords (Headcount-Abfragen — nicht Personalkosten!)
STELLENPLAN_KEYWORDS = [
    "stellenplan", "planstelle", "planstellen",
    "stelle ", "stellen ", " stelle", " stellen",  # Leerzeichen verhindert Match auf "Aufwandsstelle" etc.
    "besoldungsgruppe", "entgeltgruppe",
    "vbe ", "vollzeitäquivalent", "vollzeitaequivalent",
    "kopfzahl", "köpfe",
    "wie viele mitarbeiter", "wieviele mitarbeiter",
    "wie viele beamte", "wieviele beamte",
    "wie viele beschäftigte", "wieviele beschäftigte",
    "wie viele tarifbeschäftigte", "wieviele tarifbeschäftigte",
    "anzahl stellen", "anzahl mitarbeiter", "anzahl beschäftigte",
]


# ── DB-Zugriff ────────────────────────────────────────────────────────────────

def get_con():
    if not os.path.exists(DB_PATH):
        _exit_error(f"Datenbank nicht gefunden: {DB_PATH}\n"
                    "Bitte BUDGET_DB_PATH setzen oder DB unter "
                    "/opt/omni-haushalt/suhl_haushalt.db ablegen.")
    # URI-Modus: read-only (kein Journal-File noetig, funktioniert auch auf gemounteten Volumes)
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _exit_error(msg):
    print(f"FEHLER: {msg}", file=sys.stderr)
    sys.exit(1)


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def fmt_eur(v, mio_threshold=500_000):
    if v is None:
        return "—"
    av = abs(v)
    sign = "-" if v < 0 else ""
    av_fmt = abs(v)
    if av >= mio_threshold:
        return f"{'-' if v < 0 else ''}{av_fmt / 1_000_000:.3f} Mio. €"
    if av >= 1_000:
        return f"{v:,.0f} €".replace(",", ".")
    return f"{v:.2f} €"


def fmt_stellen(v):
    """Planstellen im deutschen Format: 490,238 / 1,000 / 0,500"""
    if v is None:
        return "—"
    return f"{v:.3f}".replace(".", ",")


def fmt_diff(a, b):
    if a is None or b is None or a == 0:
        return ""
    d = b - a
    # abs(a) damit Vorzeichen des % immer dem Vorzeichen von d entspricht
    pct = d / abs(a) * 100
    sign = "+" if d >= 0 else ""
    return f"{sign}{fmt_eur(d)} ({sign}{pct:.1f}%)"


def get_available_years(con):
    rows = con.execute(
        "SELECT DISTINCT daten_jahr FROM haushaltswerte ORDER BY daten_jahr"
    ).fetchall()
    return [r[0] for r in rows]


def get_best_wert_typ(year, con):
    rows = con.execute(
        "SELECT DISTINCT wert_typ FROM haushaltswerte WHERE daten_jahr=?",
        (year,)
    ).fetchall()
    available = [r[0] for r in rows]
    for preferred in ("PLAN_ANSATZ", "IST_ERGEBNIS", "ANSATZ_VORJAHR", "FINANZPLANUNG"):
        if preferred in available:
            return preferred
    return available[0] if available else "PLAN_ANSATZ"


def get_default_year(con):
    rows = con.execute(
        "SELECT DISTINCT daten_jahr FROM haushaltswerte "
        "WHERE wert_typ='PLAN_ANSATZ' ORDER BY daten_jahr DESC LIMIT 1"
    ).fetchone()
    return rows[0] if rows else 2025


def has_stellenplan_tables(con):
    try:
        con.execute("SELECT 1 FROM stellenplan LIMIT 1")
        return True
    except Exception:
        return False


def get_stellenplan_years(con):
    rows = con.execute(
        "SELECT DISTINCT daten_jahr FROM stellenplan ORDER BY daten_jahr"
    ).fetchall()
    return [r[0] for r in rows]


def resolve_ground_truth(year, kk_nr, db_summe):
    if year in GROUND_TRUTH and kk_nr in GROUND_TRUTH[year]:
        return GROUND_TRUTH[year][kk_nr], True
    return db_summe, False


# ── Intent-Erkennung ──────────────────────────────────────────────────────────

def detect_years(text):
    return sorted(set(int(y) for y in re.findall(r"\b(20\d{2})\b", text)))


def detect_teilplaene(text):
    t = text.lower()
    found = set()
    # Laengere Keywords zuerst (Prioritaet: "zentrale dienste" vor "zentrale")
    for kw in sorted(TEILPLAN_KEYWORDS, key=len, reverse=True):
        if kw in t:
            found.update(TEILPLAN_KEYWORDS[kw])
    return sorted(found)


def detect_kk(text):
    t = text.lower()
    # Laengere Keywords zuerst
    for kw in sorted(KONTENKLASSE_KEYWORDS, key=len, reverse=True):
        if kw in t:
            return KONTENKLASSE_KEYWORDS[kw]
    return None


def detect_sk(text):
    t = text.lower()
    for code, keywords in SK_KEYWORDS.items():
        for kw in keywords:
            if kw in t:
                return code
    return None


def detect_topn(text):
    m = re.search(r"top\s*(\d+)", text.lower())
    if m:
        return int(m.group(1))
    if any(w in text.lower() for w in ("größten", "grössten", "wichtigsten", "teuersten", "höchsten")):
        return 5
    return None


def detect_comparison(text):
    t = text.lower()
    return any(w in t for w in ("vs", "versus", "vergleich", "vergleiche", "entwicklung", "gegenüber", "gegenueber"))


def detect_stellenplan(text):
    t = text.lower()
    return any(kw in t for kw in STELLENPLAN_KEYWORDS)


# ── Query-Funktionen ──────────────────────────────────────────────────────────

def query_jahressumme(con, year, wert_typ=None):
    if wert_typ is None:
        wert_typ = get_best_wert_typ(year, con)

    rows = con.execute("""
        SELECT kk.nummer, kk.bezeichnung, SUM(h.betrag) AS summe
        FROM haushaltswerte h
        JOIN konten k ON h.konto_id = k.id
        JOIN kontenklassen kk ON k.kontenklasse_id = kk.id
        WHERE h.daten_jahr = ? AND h.wert_typ = ? AND kk.nummer IN (4,5,6,7)
        GROUP BY kk.nummer ORDER BY kk.nummer
    """, (year, wert_typ)).fetchall()

    kontenklassen = {}
    for r in rows:
        kk_nr = r["nummer"]
        db_summe = r["summe"] or 0
        summe, gt_override = resolve_ground_truth(year, kk_nr, db_summe)
        kontenklassen[kk_nr] = {
            "bezeichnung": r["bezeichnung"],
            "summe": summe,
            "db_summe": db_summe,
            "gt_override": gt_override,
        }

    return {"year": year, "wert_typ": wert_typ, "kontenklassen": kontenklassen}


def query_teilplan(con, tp_nrs, year, wert_typ=None):
    if wert_typ is None:
        wert_typ = get_best_wert_typ(year, con)

    placeholders = ",".join("?" * len(tp_nrs))
    rows = con.execute(f"""
        SELECT t.nummer AS tp_nr, t.bezeichnung AS tp_name,
               kk.nummer AS kk_nr, kk.bezeichnung AS kk_name,
               SUM(h.betrag) AS summe
        FROM haushaltswerte h
        JOIN produkte p ON h.produkt_id = p.id
        JOIN teilplaene t ON p.teilplan_id = t.id
        JOIN konten k ON h.konto_id = k.id
        JOIN kontenklassen kk ON k.kontenklasse_id = kk.id
        WHERE t.nummer IN ({placeholders})
          AND h.daten_jahr = ? AND h.wert_typ = ?
          AND kk.nummer IN (4,5,6,7)
        GROUP BY t.nummer, kk.nummer ORDER BY t.nummer, kk.nummer
    """, (*tp_nrs, year, wert_typ)).fetchall()

    tps = {}
    for r in rows:
        nr = r["tp_nr"]
        if nr not in tps:
            tps[nr] = {"tp_name": r["tp_name"], "kontenklassen": {}}
        tps[nr]["kontenklassen"][r["kk_nr"]] = {
            "bezeichnung": r["kk_name"],
            "summe": r["summe"] or 0,
        }
    return {"year": year, "wert_typ": wert_typ, "teilplaene": tps}


def query_topn(con, n, year, kk=5, wert_typ=None):
    if wert_typ is None:
        wert_typ = get_best_wert_typ(year, con)

    rows = con.execute("""
        SELECT p.produkt_nummer, p.bezeichnung AS prod_name,
               t.nummer AS tp_nr, t.bezeichnung AS tp_name,
               SUM(h.betrag) AS summe,
               p.rechtsgrundlage,
               sk.code AS sk_code, sk.bezeichnung AS sk_bez
        FROM haushaltswerte h
        JOIN produkte p ON h.produkt_id = p.id
        JOIN teilplaene t ON p.teilplan_id = t.id
        JOIN konten k ON h.konto_id = k.id
        JOIN kontenklassen kk ON k.kontenklasse_id = kk.id
        LEFT JOIN steuerungs_kategorien sk ON p.steuerungs_kategorie_id = sk.id
        WHERE h.daten_jahr = ? AND h.wert_typ = ? AND kk.nummer = ?
          AND p.produkt_nummer != '000000'
        GROUP BY p.id ORDER BY summe DESC LIMIT ?
    """, (year, wert_typ, kk, n)).fetchall()

    return {
        "year": year, "wert_typ": wert_typ, "kk": kk, "n": n,
        "items": [dict(r) for r in rows],
    }


def query_vergleich_tp(con, tp_nrs, year_a, year_b):
    data_a = query_teilplan(con, tp_nrs, year_a)
    data_b = query_teilplan(con, tp_nrs, year_b)
    return {"year_a": year_a, "year_b": year_b, "a": data_a, "b": data_b}


def query_vergleich_gesamt(con, year_a, year_b):
    data_a = query_jahressumme(con, year_a)
    data_b = query_jahressumme(con, year_b)
    return {"year_a": year_a, "year_b": year_b, "a": data_a, "b": data_b}


def query_steuerung(con, sk_code, year, wert_typ=None):
    if wert_typ is None:
        wert_typ = get_best_wert_typ(year, con)

    rows = con.execute("""
        SELECT p.produkt_nummer, p.bezeichnung AS prod_name,
               t.bezeichnung AS tp_name,
               sk.bezeichnung AS sk_bez,
               p.rechtsgrundlage,
               SUM(h.betrag) AS summe
        FROM haushaltswerte h
        JOIN produkte p ON h.produkt_id = p.id
        JOIN teilplaene t ON p.teilplan_id = t.id
        JOIN konten k ON h.konto_id = k.id
        JOIN kontenklassen kk ON k.kontenklasse_id = kk.id
        JOIN steuerungs_kategorien sk ON p.steuerungs_kategorie_id = sk.id
        WHERE sk.code = ? AND h.daten_jahr = ? AND h.wert_typ = ? AND kk.nummer = 5
          AND p.produkt_nummer != '000000'
        GROUP BY p.id ORDER BY summe DESC
    """, (sk_code, year, wert_typ)).fetchall()

    total = sum(r["summe"] or 0 for r in rows)
    return {
        "year": year, "wert_typ": wert_typ, "sk_code": sk_code,
        "total": total, "items": [dict(r) for r in rows],
    }


def query_alle_jahre_uebersicht(con):
    rows = con.execute("""
        SELECT daten_jahr, wert_typ, COUNT(*) AS zeilen, SUM(betrag) AS summe
        FROM haushaltswerte
        GROUP BY daten_jahr, wert_typ
        ORDER BY daten_jahr, wert_typ
    """).fetchall()
    return [dict(r) for r in rows]


def query_stellenplan(con, year, wert_typ="PLAN_ANSATZ", tp_nrs=None):
    """Stellenplan-Kennzahlen: gesamt, beamte, tarif, nach_gruppe, nach_tp."""
    where = "WHERE s.daten_jahr = ? AND s.wert_typ = ?"
    params = [year, wert_typ]
    if tp_nrs:
        ph = ",".join("?" * len(tp_nrs))
        where += f" AND tp.nummer IN ({ph})"
        params.extend(tp_nrs)

    totals = con.execute(f"""
        SELECT
          SUM(CASE WHEN bg.typ='BEAMTE' THEN s.planstellen ELSE 0 END) AS beamte,
          SUM(CASE WHEN bg.typ='TARIF'  THEN s.planstellen ELSE 0 END) AS tarif,
          SUM(s.planstellen) AS gesamt
        FROM stellenplan s
        JOIN teilplaene tp ON s.teilplan_id = tp.id
        JOIN besoldungsgruppen bg ON s.besoldungsgruppe_id = bg.id
        {where}
    """, params).fetchone()

    rows_gruppe = con.execute(f"""
        SELECT bg.kuerzel, bg.typ, SUM(s.planstellen) AS planstellen
        FROM stellenplan s
        JOIN teilplaene tp ON s.teilplan_id = tp.id
        JOIN besoldungsgruppen bg ON s.besoldungsgruppe_id = bg.id
        {where}
        GROUP BY bg.kuerzel, bg.typ
        ORDER BY bg.typ, planstellen DESC
    """, params).fetchall()

    rows_tp = con.execute(f"""
        SELECT tp.nummer, tp.bezeichnung,
               SUM(CASE WHEN bg.typ='BEAMTE' THEN s.planstellen ELSE 0 END) AS beamte,
               SUM(CASE WHEN bg.typ='TARIF'  THEN s.planstellen ELSE 0 END) AS tarif,
               SUM(s.planstellen) AS gesamt
        FROM stellenplan s
        JOIN teilplaene tp ON s.teilplan_id = tp.id
        JOIN besoldungsgruppen bg ON s.besoldungsgruppe_id = bg.id
        {where}
        GROUP BY tp.nummer, tp.bezeichnung
        ORDER BY tp.nummer
    """, params).fetchall()

    return {
        "year": year, "wert_typ": wert_typ,
        "gesamt": totals["gesamt"] or 0,
        "beamte": totals["beamte"] or 0,
        "tarif":  totals["tarif"]  or 0,
        "nach_gruppe": [dict(r) for r in rows_gruppe],
        "nach_tp":     [dict(r) for r in rows_tp],
    }


# ── Output-Formatter ──────────────────────────────────────────────────────────

def _hr(width=55):
    return "─" * width


def _wt_label(wt):
    return WERT_TYP_LABELS.get(wt, wt)


def format_jahressumme(data, query_text):
    year = data["year"]
    wt = data["wert_typ"]
    kks = data["kontenklassen"]
    lines = [f'Anfrage: {query_text}', "", f"Stadt Suhl — Haushalt {year} ({_wt_label(wt)})", _hr()]

    e4 = kks.get(4, {}).get("summe", 0)
    e5 = kks.get(5, {}).get("summe", 0)
    saldo = e4 - e5
    gt5 = kks.get(5, {}).get("gt_override", False)

    lines += [
        "",
        "Ergebnisplan:",
        f"  Ertraege     (KK4):  {fmt_eur(e4):>22}",
        f"  Aufwendungen (KK5):  {fmt_eur(e5):>22}{'  *' if gt5 else ''}",
        f"  {'─'*40}",
        f"  Jahresergebnis:      {fmt_eur(saldo):>22}",
    ]

    if 6 in kks or 7 in kks:
        e6 = kks.get(6, {}).get("summe", 0)
        e7 = kks.get(7, {}).get("summe", 0)
        fsal = e6 - e7
        lines += [
            "",
            "Finanzplan:",
            f"  Einzahlungen (KK6): {fmt_eur(e6):>22}",
            f"  Auszahlungen (KK7): {fmt_eur(e7):>22}",
            f"  {'─'*40}",
            f"  Finanzmittelsaldo:  {fmt_eur(fsal):>22}",
        ]

    if gt5:
        lines.append("")
        lines.append("* Gem. Haushaltssatzung §1 (offizielle Planwerte).")
        lines.append("  DB-Rohsumme weicht durch interne Verrechnungen (58xxxxx) ab.")

    return "\n".join(lines)


def format_teilplan(data, query_text):
    year = data["year"]
    wt = data["wert_typ"]
    tps = data["teilplaene"]
    lines = [f'Anfrage: {query_text}', "", _hr()]

    for tp_nr, tp in sorted(tps.items()):
        kks = tp["kontenklassen"]
        e4 = kks.get(4, {}).get("summe", 0)
        e5 = kks.get(5, {}).get("summe", 0)
        e6 = kks.get(6, {}).get("summe", 0)
        e7 = kks.get(7, {}).get("summe", 0)
        saldo = e4 - e5

        lines += [
            f"Teilplan {tp_nr} — {tp['tp_name']}",
            f"Haushaltsjahr {year} ({_wt_label(wt)})",
            "",
            "  Ergebnisplan:",
            f"    Ertraege     (KK4):  {fmt_eur(e4):>20}",
            f"    Aufwendungen (KK5):  {fmt_eur(e5):>20}",
            f"    {'─'*36}",
            f"    Saldo:               {fmt_eur(saldo):>20}",
        ]
        if e6 or e7:
            lines += [
                "",
                "  Finanzplan:",
                f"    Einzahlungen (KK6): {fmt_eur(e6):>20}",
                f"    Auszahlungen (KK7): {fmt_eur(e7):>20}",
            ]
        lines.append("")

    return "\n".join(lines)


def format_topn(data, query_text):
    year = data["year"]
    wt = data["wert_typ"]
    kk = data["kk"]
    n = data["n"]
    items = data["items"]
    kk_labels = {4: "Ertraege (KK4)", 5: "Aufwendungen (KK5)", 6: "Einzahlungen (KK6)", 7: "Auszahlungen (KK7)"}
    lines = [
        f'Anfrage: {query_text}', "",
        f"Top {n} {kk_labels.get(kk, f'KK{kk}')} — Stadt Suhl {year} ({_wt_label(wt)})",
        _hr(), "",
    ]

    for i, item in enumerate(items, 1):
        sk_info = f"  [{item['sk_code']}]" if item.get("sk_code") else ""
        lines.append(f"  {i:>2}. {fmt_eur(item['summe']):>22}  TP {item['tp_nr']} — {item['prod_name']}{sk_info}")
        if item.get("rechtsgrundlage"):
            rg = item["rechtsgrundlage"][:120] + ("…" if len(item["rechtsgrundlage"]) > 120 else "")
            lines.append(f"       Rechtsgrundlage: {rg}")

    return "\n".join(lines)


def format_vergleich_gesamt(data, query_text):
    ya = data["year_a"]
    yb = data["year_b"]
    a_kks = data["a"]["kontenklassen"]
    b_kks = data["b"]["kontenklassen"]
    wta = data["a"]["wert_typ"]
    wtb = data["b"]["wert_typ"]

    lines = [
        f'Anfrage: {query_text}', "",
        f"Stadt Suhl — Jahresvergleich {ya} vs. {yb}",
        f"({'─' * 12} {_wt_label(wta)} vs. {_wt_label(wtb)} {'─' * 12})",
        "",
        f"  {'Posten':<22} {str(ya):>16} {str(yb):>16} {'Veraenderung':>22}",
        f"  {'─'*80}",
    ]

    for kk_nr, label in ((4, "Ertraege (KK4)"), (5, "Aufwendungen (KK5)"),
                          (6, "Einzahlungen (KK6)"), (7, "Auszahlungen (KK7)")):
        va = a_kks.get(kk_nr, {}).get("summe", 0)
        vb = b_kks.get(kk_nr, {}).get("summe", 0)
        diff = fmt_diff(va, vb) if va else "—"
        lines.append(f"  {label:<22} {fmt_eur(va):>16} {fmt_eur(vb):>16} {diff:>22}")

    saldo_a = a_kks.get(4, {}).get("summe", 0) - a_kks.get(5, {}).get("summe", 0)
    saldo_b = b_kks.get(4, {}).get("summe", 0) - b_kks.get(5, {}).get("summe", 0)
    lines.append(f"  {'─'*80}")
    lines.append(f"  {'Jahresergebnis':<22} {fmt_eur(saldo_a):>16} {fmt_eur(saldo_b):>16} {fmt_diff(saldo_a, saldo_b):>22}")

    return "\n".join(lines)


def format_vergleich_tp(data, query_text):
    ya = data["year_a"]
    yb = data["year_b"]
    a_tps = data["a"]["teilplaene"]
    b_tps = data["b"]["teilplaene"]

    lines = [f'Anfrage: {query_text}', "", _hr()]

    all_tp_nrs = sorted(set(list(a_tps.keys()) + list(b_tps.keys())))
    for tp_nr in all_tp_nrs:
        tp_name = (a_tps.get(tp_nr) or b_tps.get(tp_nr) or {}).get("tp_name", f"TP {tp_nr}")
        a_kks = (a_tps.get(tp_nr) or {}).get("kontenklassen", {})
        b_kks = (b_tps.get(tp_nr) or {}).get("kontenklassen", {})

        lines += [
            f"Teilplan {tp_nr} — {tp_name}",
            f"  {'Posten':<22} {str(ya):>14} {str(yb):>14} {'Veraenderung':>20}",
            f"  {'─'*74}",
        ]
        for kk_nr, label in ((4, "Ertraege (KK4)"), (5, "Aufwendungen (KK5)")):
            va = a_kks.get(kk_nr, {}).get("summe", 0)
            vb = b_kks.get(kk_nr, {}).get("summe", 0)
            diff = fmt_diff(va, vb) if va else "—"
            lines.append(f"  {label:<22} {fmt_eur(va):>14} {fmt_eur(vb):>14} {diff:>20}")
        saldo_a = a_kks.get(4, {}).get("summe", 0) - a_kks.get(5, {}).get("summe", 0)
        saldo_b = b_kks.get(4, {}).get("summe", 0) - b_kks.get(5, {}).get("summe", 0)
        lines.append(f"  {'─'*74}")
        lines.append(f"  {'Saldo':<22} {fmt_eur(saldo_a):>14} {fmt_eur(saldo_b):>14} {fmt_diff(saldo_a, saldo_b):>20}")
        lines.append("")

    return "\n".join(lines)


def format_steuerung(data, query_text):
    year = data["year"]
    wt = data["wert_typ"]
    sk_code = data["sk_code"]
    items = data["items"]
    total = data["total"]

    sk_labels = {
        "PFLICHT_STRIKT":   "Strikte Pflichtaufgaben (einklagbarer Rechtsanspruch)",
        "PFLICHT_ERMESSEN": "Pflichtaufgaben mit Ermessensspielraum",
        "FREIWILLIG":       "Freiwillige Selbstverwaltungsaufgaben",
        "UEBERTRAGEN":      "Uebertragene Aufgaben (Auftragsangelegenheiten)",
    }

    lines = [
        f'Anfrage: {query_text}', "",
        f"{sk_labels.get(sk_code, sk_code)}",
        f"Haushaltsjahr {year} ({_wt_label(wt)}) — Aufwendungen (KK5)",
        _hr(), "",
        f"  Gesamtvolumen: {fmt_eur(total)}",
        f"  Anzahl Produkte: {len(items)}",
        "",
    ]

    for item in items[:20]:
        lines.append(f"  {fmt_eur(item['summe']):>22}  {item['prod_name']}  (TP: {item['tp_name']})")
        if item.get("rechtsgrundlage"):
            rg = item["rechtsgrundlage"][:110] + ("…" if len(item["rechtsgrundlage"]) > 110 else "")
            lines.append(f"  {'':>22}  → {rg}")

    if len(items) > 20:
        lines.append(f"  ... und {len(items)-20} weitere Produkte")

    return "\n".join(lines)


def format_stellenplan(data, query_text):
    year = data["year"]
    wt   = data["wert_typ"]
    g, b, t = data["gesamt"], data["beamte"], data["tarif"]
    pct_b = f"{b/g*100:.1f}%" if g else "—"
    pct_t = f"{t/g*100:.1f}%" if g else "—"

    lines = [
        f"Anfrage: {query_text}", "",
        f"Stellenplan Stadt Suhl — {year} ({_wt_label(wt)})",
        _hr(), "",
        f"  Planstellen gesamt:         {fmt_stellen(g):>10}",
        f"  davon Beamte:               {fmt_stellen(b):>10}  ({pct_b})",
        f"  davon Tarifbeschäftigte:    {fmt_stellen(t):>10}  ({pct_t})",
        "",
        f"  Stellen je Teilplan:",
        f"  {'Nr':<4} {'Bezeichnung':<36} {'Beamte':>8} {'Tarif':>9} {'Gesamt':>9}",
        f"  {'─'*70}",
    ]
    for tp in data["nach_tp"]:
        lines.append(
            f"  TP{tp['nummer']:<3} {tp['bezeichnung']:<36} "
            f"{fmt_stellen(tp['beamte']):>8} {fmt_stellen(tp['tarif']):>9} {fmt_stellen(tp['gesamt']):>9}"
        )

    beamte_rows = [r for r in data["nach_gruppe"] if r["typ"] == "BEAMTE"]
    tarif_rows  = [r for r in data["nach_gruppe"] if r["typ"] == "TARIF"]
    lines += ["", "  Besoldungs-/Entgeltgruppen:"]
    if beamte_rows:
        gruppen_str = "  ".join(f"{r['kuerzel']} {fmt_stellen(r['planstellen'])}" for r in beamte_rows)
        lines.append(f"  Beamte  :  {gruppen_str}")
    if tarif_rows:
        gruppen_str = "  ".join(f"{r['kuerzel']} {fmt_stellen(r['planstellen'])}" for r in tarif_rows)
        lines.append(f"  Tarif   :  {gruppen_str}")

    return "\n".join(lines)


def format_stellenplan_vergleich(data_a, data_b, query_text):
    ya, yb = data_a["year"], data_b["year"]

    def d(a, b):
        diff = b - a
        sign = "+" if diff >= 0 else ""
        return f"{sign}{fmt_stellen(diff)}"

    lines = [
        f"Anfrage: {query_text}", "",
        f"Stellenplan Stadt Suhl — {ya} vs. {yb}",
        _hr(), "",
        f"  {'Kennzahl':<28} {str(ya):>10} {str(yb):>10} {'Δ':>12}",
        f"  {'─'*65}",
        f"  {'Planstellen gesamt':<28} {fmt_stellen(data_a['gesamt']):>10} "
        f"{fmt_stellen(data_b['gesamt']):>10} {d(data_a['gesamt'], data_b['gesamt']):>12}",
        f"  {'davon Beamte':<28} {fmt_stellen(data_a['beamte']):>10} "
        f"{fmt_stellen(data_b['beamte']):>10} {d(data_a['beamte'], data_b['beamte']):>12}",
        f"  {'davon Tarif':<28} {fmt_stellen(data_a['tarif']):>10} "
        f"{fmt_stellen(data_b['tarif']):>10} {d(data_a['tarif'], data_b['tarif']):>12}",
        "",
        f"  Stellen je Teilplan:",
        f"  {'Nr':<4} {'Bezeichnung':<32} {str(ya):>8} {str(yb):>8} {'Δ':>10}",
        f"  {'─'*68}",
    ]
    tp_a = {r["nummer"]: r for r in data_a["nach_tp"]}
    tp_b = {r["nummer"]: r for r in data_b["nach_tp"]}
    for nr in sorted(set(list(tp_a) + list(tp_b))):
        name = (tp_a.get(nr) or tp_b.get(nr) or {}).get("bezeichnung", f"TP{nr}")
        ga = (tp_a.get(nr) or {}).get("gesamt", 0)
        gb = (tp_b.get(nr) or {}).get("gesamt", 0)
        lines.append(
            f"  TP{nr:<3} {name:<32} {fmt_stellen(ga):>8} {fmt_stellen(gb):>8} {d(ga, gb):>10}"
        )
    return "\n".join(lines)


def format_verfuegbare_jahre(con, query_text):
    years = get_available_years(con)
    lines = [f'Anfrage: {query_text}', "", "Verfuegbare Haushaltsdaten — Stadt Suhl", _hr(), ""]
    for year in years:
        wt = get_best_wert_typ(year, con)
        lines.append(f"  {year}  ({_wt_label(wt)})")
    lines += ["", "Fuer Details: z.B. 'Haushalt 2025' oder 'Soziales 2023 vs 2025'"]
    return "\n".join(lines)


def format_hilfe(query_text):
    return """Anfrage: {q}

Ich kann den Haushaltsplan der Stadt Suhl beantworten.

Beispiel-Abfragen:
  "Gesamthaushalt 2025"
  "Aufwendungen fuer Soziales 2025"
  "Top 5 Ausgaben 2025"
  "Kultur und Sport 2024"
  "Soziales 2023 vs 2025"   (Jahresvergleich)
  "Welche Ausgaben sind Pflichtaufgaben?"
  "Freiwillige Leistungen 2025"
  "Welche Jahre sind verfuegbar?"

Verfuegbare Teilplaene (Stichworte):
  verwaltung, kultur, tourismus, sport, personal, strasse, verkehr,
  ordnung, sicherheit, feuerwehr, umwelt, sozial, gesundheit,
  schule, kinder, jugend, kita, famili, einrichtung

Verfuegbare Jahre: 2021-2028 (IST 2021-2023, Plan 2023-2025, FP 2026-2028)

Stellenplan (Personalstellen / Headcount):
  "Wie viele Planstellen hat Suhl 2025?"
  "Wie viele Beamte gibt es 2025?"
  "Stellenplan 2024 vs 2025"
  "Wie viele Stellen hat die Feuerwehr?"
  "Besoldungsgruppen Beamte 2025"
""".format(q=query_text)


# ── Haupt-Dispatcher ──────────────────────────────────────────────────────────

def dispatch(query_text, json_mode, con):
    t = query_text.lower().strip()

    # Hilfe
    if any(w in t for w in ("hilfe", "help", "was kannst", "was kann")):
        return {"type": "hilfe", "text": format_hilfe(query_text)}, None

    # Verfuegbare Jahre
    if any(w in t for w in ("verfuegbar", "welche jahre", "welche daten", "datenstand")):
        text = format_verfuegbare_jahre(con, query_text)
        return {"type": "jahre", "text": text}, None

    years = detect_years(query_text)
    tp_nrs = detect_teilplaene(query_text)
    topn = detect_topn(query_text)
    is_comparison = detect_comparison(query_text)
    sk_code = detect_sk(query_text)
    kk = detect_kk(query_text)

    # Stellenplan (Headcount) — VOR Jahresvergleich, damit "Stellenplan 2024 vs 2025"
    # nicht in den allgemeinen Finanz-Vergleich fällt
    if detect_stellenplan(query_text) and has_stellenplan_tables(con):
        if is_comparison and len(years) >= 2:
            ya, yb = years[0], years[-1]
            data_a = query_stellenplan(con, ya, "PLAN_ANSATZ", tp_nrs or None)
            data_b = query_stellenplan(con, yb, "PLAN_ANSATZ", tp_nrs or None)
            text = format_stellenplan_vergleich(data_a, data_b, query_text)
            return {"type": "stellenplan_vergleich", "text": text,
                    "data": {"a": data_a, "b": data_b}}, None
        else:
            sp_year = years[0] if years else 2025
            sp_wt = "IST" if "ist" in query_text.lower() and sp_year == 2024 else "PLAN_ANSATZ"
            data = query_stellenplan(con, sp_year, sp_wt, tp_nrs or None)
            if data["gesamt"] == 0:
                avail = get_stellenplan_years(con)
                text = (f"Fuer {sp_year} ({sp_wt}) liegen keine Stellenplan-Daten vor.\n"
                        f"Verfuegbare Jahre im Stellenplan: {', '.join(str(y) for y in avail)}")
                return {"type": "stellenplan_leer", "text": text}, None
            text = format_stellenplan(data, query_text)
            return {"type": "stellenplan", "data": data, "text": text}, None

    # Jahresvergleich (Finanz)
    if is_comparison and len(years) >= 2:
        year_a, year_b = years[0], years[-1]
        if tp_nrs:
            data = query_vergleich_tp(con, tp_nrs, year_a, year_b)
            text = format_vergleich_tp(data, query_text)
        else:
            data = query_vergleich_gesamt(con, year_a, year_b)
            text = format_vergleich_gesamt(data, query_text)
        return {"type": "vergleich", "data": data, "text": text}, None

    # Jahr bestimmen
    year = years[0] if years else get_default_year(con)

    # Steuerungskategorie
    if sk_code:
        data = query_steuerung(con, sk_code, year)
        text = format_steuerung(data, query_text)
        return {"type": "steuerung", "data": data, "text": text}, None

    # Top-N
    if topn:
        kk_use = kk if kk else 5
        data = query_topn(con, topn, year, kk_use)
        text = format_topn(data, query_text)
        return {"type": "topn", "data": data, "text": text}, None

    # Teilplan-Abfrage
    if tp_nrs:
        data = query_teilplan(con, tp_nrs, year)
        text = format_teilplan(data, query_text)
        return {"type": "teilplan", "data": data, "text": text}, None

    # Jahressumme (Fallback)
    data = query_jahressumme(con, year)
    text = format_jahressumme(data, query_text)
    return {"type": "jahressumme", "data": data, "text": text}, None


# ── Einstiegspunkt ────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args:
        print(format_hilfe("(kein Argument)"))
        sys.exit(0)

    json_mode = "--json" in args
    args = [a for a in args if a != "--json"]

    if not args:
        print(format_hilfe("--json (kein Query)"))
        sys.exit(0)

    query_text = " ".join(args)

    con = get_con()
    try:
        result, err = dispatch(query_text, json_mode, con)
        if err:
            print(f"FEHLER: {err}", file=sys.stderr)
            sys.exit(1)

        if json_mode:
            out = {"query": query_text, "type": result["type"]}
            if "data" in result:
                out["data"] = result["data"]
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print(result["text"])
    finally:
        con.close()


if __name__ == "__main__":
    main()
