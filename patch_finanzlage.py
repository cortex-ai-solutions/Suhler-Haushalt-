#!/usr/bin/env python3
"""
patch_finanzlage.py
A) Haushaltslage im Zeitverlauf: Jahresergebnis + Finanzierungssaldo (2021-2025)
C) Investitionen & Substanzerhalt: AfA vs. Investitions-Auszahlungen + Investitionsquote
ACHTUNG: Kein Unicode in JS-Strings -- nur JS-Escapes (\\uXXXX).
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(BASE, "index.html")

content = open(HTML, "rb").read()
bt_before = content.count(b"\x60")
print(f"Backticks vor Patch: {bt_before}")

# ---------------------------------------------------------------------------
# 1) HTML: Haushaltslage-Karte VOR bestehendem Zeitreihe-Card
# ---------------------------------------------------------------------------
OLD_ZR_OPEN = (
    b'<div id="tab-zeitreihe" class="hidden">\r\n'
    b'  <div class="card p-5 mb-6">'
)
assert content.count(OLD_ZR_OPEN) == 1, f"Anker A nicht eindeutig"

NEW_ZR_OPEN = (
    b'<div id="tab-zeitreihe" class="hidden">\r\n'
    b'  <!-- A) Haushaltslage im Zeitverlauf -->\r\n'
    b'  <div class="card p-5 mb-6">\r\n'
    b'    <div class="section-title">Haushaltslage im Zeitverlauf</div>\r\n'
    b'    <p class="text-slate-400 text-sm mb-4">\r\n'
    b'      Jahresergebnis (Ertr&auml;ge &minus; Aufwendungen) und Finanzierungssaldo\r\n'
    b'      (Einzahlungen &minus; Auszahlungen) 2021&ndash;2025.\r\n'
    b'      Gr&uuml;n&nbsp;= &Uuml;berschuss/positiv &middot; Rot&nbsp;= Fehlbetrag/negativ.\r\n'
    b'      IST 2021&ndash;2023 &middot; Plan 2024&ndash;2025.\r\n'
    b'    </p>\r\n'
    b'    <div class="kpi-row mb-5" id="hl-kpi-row"></div>\r\n'
    b'    <div id="chart-hl" class="plotly-chart" style="min-height:300px;"></div>\r\n'
    b'    <div class="note mt-2">\r\n'
    b'      IST-Werte aus Haushaltsjahresabschluss-Ergebnissen 2021&ndash;2023.\r\n'
    b'      Plan 2024/2025 = Planansatz gem&auml;&szlig; Haushaltsplan.\r\n'
    b'    </div>\r\n'
    b'  </div>\r\n'
    b'  <!-- bestehend: Ertraege & Aufwendungen -->\r\n'
    b'  <div class="card p-5 mb-6">'
)

content = content.replace(OLD_ZR_OPEN, NEW_ZR_OPEN, 1)
print("A) Haushaltslage-Karte eingefuegt")

# ---------------------------------------------------------------------------
# 2) HTML: Investitions-Karte NACH bestehendem Zeitreihe-Card
# ---------------------------------------------------------------------------
OLD_ZR_NOTE = (
    b'    <div class="note mt-2">Schraffiert = Finanzplanung (Prognose).'
    b' Quellen: Haushaltspl\xc3\xa4ne Suhl 2023, 2024 &amp; 2025</div>\r\n'
    b'  </div>\r\n'
    b'</div>\r\n'
)
assert content.count(OLD_ZR_NOTE) == 1, "Anker C nicht eindeutig"

NEW_ZR_NOTE = (
    b'    <div class="note mt-2">Schraffiert = Finanzplanung (Prognose).'
    b' Quellen: Haushaltspl\xc3\xa4ne Suhl 2023, 2024 &amp; 2025</div>\r\n'
    b'  </div>\r\n'
    b'  <!-- C) Investitionen & Substanzerhalt -->\r\n'
    b'  <div class="card p-5 mb-6">\r\n'
    b'    <div class="section-title">Investitionen &amp; Substanzerhalt</div>\r\n'
    b'    <p class="text-slate-400 text-sm mb-4">\r\n'
    b'      Bilanzielle Abschreibungen (AfA, Konten 53xx) vs. Investitions-Auszahlungen\r\n'
    b'      (KK7 Konten 78xx). Eine Investitionsquote &lt;&nbsp;100&nbsp;% bedeutet\r\n'
    b'      Substanzverzehr &mdash; die Stadt investiert weniger als sie abschreibt.\r\n'
    b'    </p>\r\n'
    b'    <div id="chart-invest" class="plotly-chart" style="min-height:340px;"></div>\r\n'
    b'    <div class="note mt-2">\r\n'
    b'      Quelle: Haushaltspl&auml;ne Suhl 2023&ndash;2025'
    b' (IST-Ergebnis 2021&ndash;2023, Planansatz 2024&ndash;2025).\r\n'
    b'      Rote gestrichelte Linie = 100&nbsp;% (Substanzerhalt-Schwelle).\r\n'
    b'    </div>\r\n'
    b'  </div>\r\n'
    b'</div>\r\n'
)

content = content.replace(OLD_ZR_NOTE, NEW_ZR_NOTE, 1)
print("C) Investitions-Karte eingefuegt")

# ---------------------------------------------------------------------------
# 3) JS: Funktionen + Monkey-Patch
#    KRITISCH: Alle Sonderzeichen als JS-Escapes \uXXXX schreiben.
#    In Python-Bytes-Literalen: b'\\u20ac' = 6 ASCII-Bytes € (fuer Browser-JS)
# ---------------------------------------------------------------------------
JS_ANCHOR = b"\r\nfunction setupTabs() {"

# Alle nicht-ASCII Zeichen als \uXXXX -- daher bytes direkt zusammensetzen.
# € = Euro-Zeichen im Browser-JS
# − = Minus-Zeichen im Browser-JS
EUR = b"\\u20ac"   # 6 ASCII-Bytes: \ u 2 0 a c
MIN = b"\\u2212"   # 6 ASCII-Bytes: \ u 2 2 1 2

NEW_JS = (
    b"\r\n"
    b"function _renderHaushaltslage() {\r\n"
    b"  var z = DATA.zeitreihe;\r\n"
    b"  if (!z || !z.length) return;\r\n"
    b"\r\n"
    b"  var pts     = z.filter(function(d) { return !d.ist_prognose; });\r\n"
    b"  var labels  = pts.map(function(d) { return d.label; });\r\n"
    b"  var ergeb   = pts.map(function(d) { return Math.round((d.ertraege - d.aufwendungen) / 1000); });\r\n"
    b"  var finsald = pts.map(function(d) { return Math.round((d.einzahlungen - d.auszahlungen) / 1000); });\r\n"
    b"\r\n"
    b"  var kpiEl = document.getElementById('hl-kpi-row');\r\n"
    b"  if (kpiEl) {\r\n"
    b"    function fmtT(v) {\r\n"
    b"      if (v === null || v === undefined) return '-';\r\n"
    b"      return (v >= 0 ? '+' : '-') + Math.abs(v).toLocaleString('de-DE') + ' T" + EUR + b"';\r\n"
    b"    }\r\n"
    b"    function chip(lbl, val, sub) {\r\n"
    b"      var col = val >= 0 ? '#4ade80' : '#f87171';\r\n"
    b"      return '<div class=\"kpi-card\" style=\"flex:1;min-width:160px\">'\r\n"
    b"        + '<div class=\"kpi-label\">' + lbl + '</div>'\r\n"
    b"        + '<div class=\"kpi-value\" style=\"color:' + col + ';font-size:1.35rem\">' + fmtT(val) + '</div>'\r\n"
    b"        + '<div class=\"kpi-label\" style=\"font-size:0.65rem;margin-top:2px;color:#64748b\">' + sub + '</div>'\r\n"
    b"        + '</div>';\r\n"
    b"    }\r\n"
    b"    var i23 = labels.indexOf('Ist 2023');\r\n"
    b"    var i25 = labels.indexOf('Ansatz 2025');\r\n"
    b"    var html = '';\r\n"
    b"    if (i23 >= 0) html += chip('Jahresergebnis 2023 (Ist)',      ergeb[i23],   'KK4 " + MIN + b" KK5');\r\n"
    b"    if (i25 >= 0) html += chip('Jahresergebnis 2025 (Plan)',     ergeb[i25],   'KK4 " + MIN + b" KK5');\r\n"
    b"    if (i25 >= 0) html += chip('Finanzierungssaldo 2025 (Plan)', finsald[i25], 'KK6 " + MIN + b" KK7');\r\n"
    b"    kpiEl.innerHTML = html;\r\n"
    b"  }\r\n"
    b"\r\n"
    b"  if (typeof Plotly === 'undefined') return;\r\n"
    b"  var colErgeb   = ergeb.map(function(v)  { return v >= 0 ? '#4ade80' : '#f87171'; });\r\n"
    b"  var colFinsald = finsald.map(function(v) { return v >= 0 ? '#38bdf8' : '#94a3b8'; });\r\n"
    b"\r\n"
    b"  Plotly.newPlot('chart-hl', [\r\n"
    b"    {\r\n"
    b"      type: 'bar', name: 'Jahresergebnis (T" + EUR + b")',\r\n"
    b"      x: labels, y: ergeb, marker: { color: colErgeb },\r\n"
    b"      hovertemplate: '%{x}: %{y:,.0f} T" + EUR + b"<extra>Jahresergebnis</extra>'\r\n"
    b"    },\r\n"
    b"    {\r\n"
    b"      type: 'bar', name: 'Finanzierungssaldo (T" + EUR + b")',\r\n"
    b"      x: labels, y: finsald, marker: { color: colFinsald },\r\n"
    b"      hovertemplate: '%{x}: %{y:,.0f} T" + EUR + b"<extra>Finanzierungssaldo</extra>'\r\n"
    b"    }\r\n"
    b"  ], Object.assign({}, DARK_LAYOUT, {\r\n"
    b"    height: 300,\r\n"
    b"    barmode: 'group',\r\n"
    b"    xaxis: { gridcolor: '#334155' },\r\n"
    b"    yaxis: {\r\n"
    b"      gridcolor: '#334155', tickformat: ',d', title: 'T" + EUR + b"',\r\n"
    b"      zeroline: true, zerolinecolor: '#64748b', zerolinewidth: 1\r\n"
    b"    },\r\n"
    b"    legend: { orientation: 'h', y: -0.22 },\r\n"
    b"    margin: { t: 10, b: 60, l: 75, r: 20 },\r\n"
    b"    shapes: [{\r\n"
    b"      type: 'line', xref: 'paper', yref: 'y',\r\n"
    b"      x0: 0, x1: 1, y0: 0, y1: 0,\r\n"
    b"      line: { color: '#475569', width: 1, dash: 'dot' }\r\n"
    b"    }]\r\n"
    b"  }), CFG);\r\n"
    b"}\r\n"
    b"\r\n"
    b"function _renderInvestitionen() {\r\n"
    b"  var inv = DATA.investitionen;\r\n"
    b"  if (!inv || !inv.length) return;\r\n"
    b"  if (typeof Plotly === 'undefined') return;\r\n"
    b"\r\n"
    b"  var labels = inv.map(function(d) { return d.label; });\r\n"
    b"  var afa    = inv.map(function(d) { return d.afa_teur; });\r\n"
    b"  var invest = inv.map(function(d) { return d.invest_teur !== null ? d.invest_teur : null; });\r\n"
    b"  var quote  = inv.map(function(d) { return d.quote; });\r\n"
    b"\r\n"
    b"  var quoteCol = quote.map(function(v) {\r\n"
    b"    if (v === null) return '#94a3b8';\r\n"
    b"    if (v >= 100)   return '#4ade80';\r\n"
    b"    if (v >= 75)    return '#fbbf24';\r\n"
    b"    return '#f87171';\r\n"
    b"  });\r\n"
    b"\r\n"
    b"  Plotly.newPlot('chart-invest', [\r\n"
    b"    {\r\n"
    b"      type: 'bar', name: 'Abschreibungen AfA (T" + EUR + b")',\r\n"
    b"      x: labels, y: afa, marker: { color: '#f59e0b' },\r\n"
    b"      hovertemplate: '%{x}: %{y:,.0f} T" + EUR + b"<extra>Abschreibungen (AfA)</extra>'\r\n"
    b"    },\r\n"
    b"    {\r\n"
    b"      type: 'bar', name: 'Investitions-Auszahlungen (T" + EUR + b")',\r\n"
    b"      x: labels, y: invest, marker: { color: '#0d9488' },\r\n"
    b"      hovertemplate: '%{x}: %{y:,.0f} T" + EUR + b"<extra>Investitions-Auszahlungen</extra>'\r\n"
    b"    },\r\n"
    b"    {\r\n"
    b"      type: 'scatter', mode: 'lines+markers',\r\n"
    b"      name: 'Investitionsquote (%)',\r\n"
    b"      x: labels, y: quote, yaxis: 'y2',\r\n"
    b"      line: { color: '#e2e8f0', width: 2 },\r\n"
    b"      marker: { size: 9, color: quoteCol, line: { color: '#0f172a', width: 1.5 } },\r\n"
    b"      hovertemplate: '%{x}: %{y:.1f} %<extra>Investitionsquote</extra>'\r\n"
    b"    }\r\n"
    b"  ], Object.assign({}, DARK_LAYOUT, {\r\n"
    b"    height: 340,\r\n"
    b"    barmode: 'group',\r\n"
    b"    xaxis: { gridcolor: '#334155' },\r\n"
    b"    yaxis: { gridcolor: '#334155', tickformat: ',d', title: 'T" + EUR + b"' },\r\n"
    b"    yaxis2: {\r\n"
    b"      overlaying: 'y', side: 'right',\r\n"
    b"      title: '%', showgrid: false,\r\n"
    b"      tickformat: '.0f', range: [0, 160], ticksuffix: ' %'\r\n"
    b"    },\r\n"
    b"    legend: { orientation: 'h', y: -0.22 },\r\n"
    b"    margin: { t: 10, b: 60, l: 75, r: 70 },\r\n"
    b"    shapes: [{\r\n"
    b"      type: 'line', xref: 'paper', yref: 'y2',\r\n"
    b"      x0: 0, x1: 1, y0: 100, y1: 100,\r\n"
    b"      line: { color: '#f87171', width: 1.5, dash: 'dash' }\r\n"
    b"    }],\r\n"
    b"    annotations: [{\r\n"
    b"      xref: 'paper', yref: 'y2', x: 1.02, y: 100,\r\n"
    b"      text: '100 %', showarrow: false,\r\n"
    b"      font: { color: '#f87171', size: 10 }, xanchor: 'left'\r\n"
    b"    }]\r\n"
    b"  }), CFG);\r\n"
    b"}\r\n"
    b"\r\n"
    b"(function() {\r\n"
    b"  var _origRZT = renderZeitreihe;\r\n"
    b"  renderZeitreihe = function() {\r\n"
    b"    _origRZT();\r\n"
    b"    _renderHaushaltslage();\r\n"
    b"    _renderInvestitionen();\r\n"
    b"  };\r\n"
    b"})();\r\n"
)

# Non-ASCII pruefen
non_ascii = [(i, b) for i, b in enumerate(NEW_JS) if b > 127]
print(f"Non-ASCII-Bytes im JS: {len(non_ascii)}")
if non_ascii:
    for i, b in non_ascii[:5]:
        print(f"  pos={i}: 0x{b:02x}  ctx={repr(NEW_JS[max(0,i-30):i+15])}")

assert len(non_ascii) == 0, "JS enthaelt Non-ASCII -- Abbruch!"

assert JS_ANCHOR in content, "JS-Anker nicht gefunden"
content = content.replace(JS_ANCHOR, NEW_JS + JS_ANCHOR, 1)
print("JS eingefuegt")

# ---------------------------------------------------------------------------
# Abschlusskontrolle
# ---------------------------------------------------------------------------
bt_after = content.count(b"\x60")
print(f"Backticks: {bt_before} -> {bt_after}")
assert bt_after == bt_before, f"Backtick-Paritat verletzt"
assert bt_after % 2 == 0

assert content.count(b'id="chart-hl"') == 1
assert content.count(b'id="chart-invest"') == 1
assert content.count(b'_renderHaushaltslage') >= 2
assert content.count(b'_renderInvestitionen') >= 2

open(HTML, "wb").write(content)
print(f"OK: index.html ({len(content)//1024} KB)")
