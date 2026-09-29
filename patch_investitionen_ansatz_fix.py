# -*- coding: utf-8 -*-
"""
patch_investitionen_ansatz_fix.py - Klarstellung im Investitionen-Tab:
"Gesamt (Invest.)" ist die Lebenszeit-Summe einer (oft mehrjaehrigen) Massnahme,
nicht die Auszahlung im aktuellen Haushaltsjahr. Nutzer-Rueckfrage (2026-09-29):
"Wie kann ich sehen, was 2026 investiert wurde?" - bisher nirgends klar sichtbar.

Ergaenzt:
- Neue KPI-Kachel "Auszahlung <Jahr> (Ansatz)" als prominenteste erste Kachel
- Neue Tabellenspalte "Ansatz <Jahr>" in der Massnahmen-Tabelle
- Default-Sortierung der Tabelle auf Ansatz <Jahr> (statt Lebenszeit-Gesamt)
- Klarstellender Hinweistext bei der bisherigen "Investitionsvolumen"-Kachel
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "index.html")

with open(HTML_PATH, "rb") as f:
    content = f.read().decode("utf-8")

backticks_before = content.count("`")


def nl(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\n", "\r\n")


def must_replace(old, new, label):
    global content
    n = content.count(old)
    if n != 1:
        raise SystemExit(f"[FEHLER] Anker '{label}' kommt {n}x vor (erwartet 1x). Abbruch ohne Aenderung.")
    content = content.replace(old, new, 1)


# ─────────────────────────────────────────────────────────────────────────
# 1) KPI-Grid: 4 -> 5 Spalten, neue erste Kachel "Auszahlung <Jahr> (Ansatz)"
# ─────────────────────────────────────────────────────────────────────────
KPI_OLD = nl(
    '  <!-- KPI-Chips -->\n'
    '  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">\n'
    '    <div class="card p-4">\n'
    '      <div class="kpi-label">Investitionsvolumen</div>\n'
    '      <div class="kpi-value text-slate-200" id="inv-kpi-volumen">&ndash;</div>\n'
    '      <div class="note mt-1"><span id="inv-kpi-n" class="text-blue-400"></span> Ma&szlig;nahmen im aktuellen Haushaltsplan</div>\n'
    '    </div>\n'
    '    <div class="card p-4">\n'
    '      <div class="kpi-label">F&ouml;rdermittel akquiriert</div>\n'
    '      <div class="kpi-value text-emerald-300" id="inv-kpi-foerderung">&ndash;</div>\n'
    '      <div class="note mt-1"><span id="inv-kpi-foerderquote" class="text-emerald-400"></span> F&ouml;rderquote am Gesamtvolumen</div>\n'
    '    </div>\n'
    '    <div class="card p-4">\n'
    '      <div class="kpi-label">Gesperrte Ma&szlig;nahmen</div>\n'
    '      <div class="kpi-value text-rose-300" id="inv-kpi-gesperrt">&ndash;</div>\n'
    '      <div class="note mt-1">Bewirtschaftungssperre per Stadtratsbeschluss</div>\n'
    '    </div>\n'
    '    <div class="card p-4">\n'
    '      <div class="kpi-label">Neue Ma&szlig;nahmen</div>\n'
    '      <div class="kpi-value text-violet-300" id="inv-kpi-neu">&ndash;</div>\n'
    '      <div class="note mt-1"><span id="inv-kpi-kredit" class="text-slate-400"></span> mit Kreditkontingent (Th&uuml;rKIpG)</div>\n'
    '    </div>\n'
    '  </div>'
)

KPI_NEW = nl(
    '  <!-- KPI-Chips -->\n'
    '  <div class="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">\n'
    '    <div class="card p-4 border border-blue-800/40">\n'
    '      <div class="kpi-label">Auszahlung <span id="inv-kpi-jahr-label"></span> (Ansatz)</div>\n'
    '      <div class="kpi-value text-blue-300" id="inv-kpi-ansatz">&ndash;</div>\n'
    '      <div class="note mt-1">tats&auml;chlich in diesem Haushaltsjahr geplante Investitions-Auszahlung</div>\n'
    '    </div>\n'
    '    <div class="card p-4">\n'
    '      <div class="kpi-label">Gesamtkosten aller Ma&szlig;nahmen</div>\n'
    '      <div class="kpi-value text-slate-200" id="inv-kpi-volumen">&ndash;</div>\n'
    '      <div class="note mt-1"><span id="inv-kpi-n" class="text-blue-400"></span> Ma&szlig;nahmen &uuml;ber deren gesamte (oft mehrj&auml;hrige) Laufzeit</div>\n'
    '    </div>\n'
    '    <div class="card p-4">\n'
    '      <div class="kpi-label">F&ouml;rdermittel akquiriert</div>\n'
    '      <div class="kpi-value text-emerald-300" id="inv-kpi-foerderung">&ndash;</div>\n'
    '      <div class="note mt-1"><span id="inv-kpi-foerderquote" class="text-emerald-400"></span> F&ouml;rderquote &uuml;ber die gesamte Laufzeit</div>\n'
    '    </div>\n'
    '    <div class="card p-4">\n'
    '      <div class="kpi-label">Gesperrte Ma&szlig;nahmen</div>\n'
    '      <div class="kpi-value text-rose-300" id="inv-kpi-gesperrt">&ndash;</div>\n'
    '      <div class="note mt-1">Bewirtschaftungssperre per Stadtratsbeschluss</div>\n'
    '    </div>\n'
    '    <div class="card p-4">\n'
    '      <div class="kpi-label">Neue Ma&szlig;nahmen</div>\n'
    '      <div class="kpi-value text-violet-300" id="inv-kpi-neu">&ndash;</div>\n'
    '      <div class="note mt-1"><span id="inv-kpi-kredit" class="text-slate-400"></span> mit Kreditkontingent (Th&uuml;rKIpG)</div>\n'
    '    </div>\n'
    '  </div>'
)

must_replace(KPI_OLD, KPI_NEW, "kpi-grid")

# ─────────────────────────────────────────────────────────────────────────
# 2) Tabellen-Header: neue Spalte "Ansatz <Jahr>"
# ─────────────────────────────────────────────────────────────────────────
must_replace(
    nl(
        '            <th class="py-2 pr-3 font-medium">Ma&szlig;nahme</th>\n'
        '            <th class="py-2 pr-3 font-medium w-14">TP</th>\n'
        '            <th class="py-2 pr-3 font-medium text-right w-28">Gesamt (Invest.)</th>\n'
        '            <th class="py-2 pr-3 font-medium w-40">Eigenanteil / F&ouml;rderung</th>\n'
        '            <th class="py-2 font-medium w-20">Status</th>'
    ),
    nl(
        '            <th class="py-2 pr-3 font-medium">Ma&szlig;nahme</th>\n'
        '            <th class="py-2 pr-3 font-medium w-14">TP</th>\n'
        '            <th class="py-2 pr-3 font-medium text-right w-24">Ansatz <span id="inv-th-jahr"></span></th>\n'
        '            <th class="py-2 pr-3 font-medium text-right w-28">Gesamt (Invest.)</th>\n'
        '            <th class="py-2 pr-3 font-medium w-40">Eigenanteil / F&ouml;rderung</th>\n'
        '            <th class="py-2 font-medium w-20">Status</th>'
    ),
    "table-header",
)

# ─────────────────────────────────────────────────────────────────────────
# 3) JS: renderInvestitionen() - neue KPI befuellen
# ─────────────────────────────────────────────────────────────────────────
must_replace(
    nl(
        '  var k = IP.kpis;\n'
        '  setText("inv-kpi-volumen", invFmtEur(k.gesamtvolumen));'
    ),
    nl(
        '  var k = IP.kpis;\n'
        '  setText("inv-kpi-jahr-label", IP.aktuelles_jahr);\n'
        '  setText("inv-th-jahr", IP.aktuelles_jahr);\n'
        '  setText("inv-kpi-ansatz", invFmtEur(k.ansatz_summe));\n'
        '  setText("inv-kpi-volumen", invFmtEur(k.gesamtvolumen));'
    ),
    "js-render-kpis",
)

# ─────────────────────────────────────────────────────────────────────────
# 4) JS: renderInvTable() - Default-Sortierung + neue Spalte + colspan-Fix
# ─────────────────────────────────────────────────────────────────────────
must_replace(
    '  }).sort(function(a, b) { return b.aus_gesamt - a.aus_gesamt; });',
    '  }).sort(function(a, b) { return b.aus_ansatz_aktuell - a.aus_ansatz_aktuell; });',
    "js-sort-default",
)

must_replace(
    nl(
        '      "<td class=\\"py-2 pr-3 text-slate-400 font-mono text-xs\\">" + (m.tp_nr || "\\u2013") + "</td>" +\n'
        '      "<td class=\\"py-2 pr-3 text-right font-mono text-xs text-slate-200\\">" + invFmtEur(m.aus_gesamt) + "</td>" +'
    ),
    nl(
        '      "<td class=\\"py-2 pr-3 text-slate-400 font-mono text-xs\\">" + (m.tp_nr || "\\u2013") + "</td>" +\n'
        '      "<td class=\\"py-2 pr-3 text-right font-mono text-xs " + (m.aus_ansatz_aktuell > 0 ? "text-blue-300" : "text-slate-600") + "\\">" + invFmtEur(m.aus_ansatz_aktuell) + "</td>" +\n'
        '      "<td class=\\"py-2 pr-3 text-right font-mono text-xs text-slate-200\\">" + invFmtEur(m.aus_gesamt) + "</td>" +'
    ),
    "js-row-ansatz-cell",
)

must_replace(
    '      "<td colspan=\\"5\\" class=\\"px-4 py-3\\">" + buildInvDetail(m) + "</td></tr>",',
    '      "<td colspan=\\"6\\" class=\\"px-4 py-3\\">" + buildInvDetail(m) + "</td></tr>",',
    "js-detail-colspan",
)

must_replace(
    '    "<tr><td colspan=\\"5\\" class=\\"py-4 text-center text-slate-500 text-xs\\">Keine Ma\\u00dfnahmen gefunden.</td></tr>";',
    '    "<tr><td colspan=\\"6\\" class=\\"py-4 text-center text-slate-500 text-xs\\">Keine Ma\\u00dfnahmen gefunden.</td></tr>";',
    "js-empty-colspan",
)

backticks_after = content.count("`")
if backticks_before != backticks_after:
    raise SystemExit(f"[FEHLER] Backtick-Anzahl geaendert: vorher {backticks_before}, nachher {backticks_after}. Abbruch, Datei NICHT geschrieben.")
if backticks_after % 2 != 0:
    raise SystemExit(f"[FEHLER] Backtick-Anzahl ungerade ({backticks_after}). Abbruch, Datei NICHT geschrieben.")

with open(HTML_PATH, "wb") as f:
    f.write(content.encode("utf-8"))

print(f"[OK] index.html gepatcht. Backticks: {backticks_before} -> {backticks_after}")
