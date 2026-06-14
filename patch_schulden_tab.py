"""
patch_schulden_tab.py
Fuegt Schuldenentwicklung-Karte (2013-2026) in den Vermoegen-Tab (Bilanz-Subtab) ein.
Quelle: HH-Plan 2025 S. 83. Keine Neuverschuldung seit 2013.
"""

INDEX = "index.html"

HTML_ANCHOR_OLD = (
    b'bilanz-entwicklung-body" class="text-sm mt-2"></div>\r\n'
    b'      </div>\r\n'
    b'      </div>\r\n'
    b'    </div>\r\n'
    b'\r\n'
    b'    <div id="vtab-ebkds"'
)

HTML_ANCHOR_NEW = (
    b'bilanz-entwicklung-body" class="text-sm mt-2"></div>\r\n'
    b'      </div>\r\n'
    b'      </div>\r\n'
    b'      <div class="card p-5 mt-4">\r\n'
    b'        <div class="section-title">Schuldenentwicklung 2013&#8211;2026</div>\r\n'
    b'        <p class="text-slate-400 text-xs mb-3">Investitionskredite per 31.12. in T&#8364;&nbsp;&mdash; '
    b'Quelle: HH-Plan 2025 S.&nbsp;83. Keine Neuverschuldung seit 2013.</p>\r\n'
    b'        <div class="kpi-row mb-4" id="schulden-kpi-row"></div>\r\n'
    b'        <div id="chart-schulden" style="height:300px"></div>\r\n'
    b'      </div>\r\n'
    b'    </div>\r\n'
    b'\r\n'
    b'    <div id="vtab-ebkds"'
)

JS_ANCHOR = b'\r\nfunction setupTabs() {'

# All special chars as JS \uXXXX escapes (6 ASCII bytes each)
EUR  = b'\\u20ac'   # €
DASH = b'\\u2212'   # − (minus sign)
EDSH = b'\\u2013'   # – (en dash)

NEW_JS = (
    b'// \xe2\x80\x94 Schuldenentwicklung 2013-2026 \xe2\x80\x94\r\n'
    b'function _renderSchulden() {\r\n'
    b'  var el = document.getElementById(\'chart-schulden\');\r\n'
    b'  var kpiEl = document.getElementById(\'schulden-kpi-row\');\r\n'
    b'  if (!el || !kpiEl || !DATA.schulden || !DATA.schulden.length) return;\r\n'
    b'  var S = DATA.schulden;\r\n'
    b'\r\n'
    b'  // KPI-Werte ermitteln\r\n'
    b'  var s2013 = S[0].schuldenstand_teur;\r\n'
    b'  var s2025 = 0, pk2025 = 0;\r\n'
    b'  for (var i = 0; i < S.length; i++) {\r\n'
    b'    if (S[i].jahr === 2025) { s2025 = S[i].schuldenstand_teur; pk2025 = S[i].prokopf_eur; }\r\n'
    b'  }\r\n'
    b'  var abbau = Math.round(s2013 - s2025);\r\n'
    b'  var abbauPct = s2013 > 0 ? Math.round(abbau / s2013 * 100) : 0;\r\n'
    b'\r\n'
    b'  // KPI-Chips rendern\r\n'
    b'  function fmtT(n) { return n.toLocaleString(\'de-DE\') + \' T\' + \'' + EUR + b'\'; }\r\n'
    b'  var kpiData = [\r\n'
    b'    { label: \'Schuldenstand 2025 (Plan)\', val: fmtT(s2025), color: \'#10b981\' },\r\n'
    b'    { label: \'Pro-Kopf-Verschuldung 2025\', val: pk2025.toLocaleString(\'de-DE\') + \' \' + \'' + EUR + b'\' + \'/EW\', color: \'#3b82f6\' },\r\n'
    b'    { label: \'Schuldenabbau seit 2013\', val: \'' + DASH + b'\' + fmtT(abbau) + \' (\' + \'' + DASH + b'\' + abbauPct + \'%)\', color: \'#059669\' },\r\n'
    b'  ];\r\n'
    b'  kpiEl.innerHTML = kpiData.map(function(c) {\r\n'
    b'    return \'<div class="kpi-card" style="border-top:3px solid \' + c.color + \'">\'  \r\n'
    b'      + \'<div class="kpi-label">\' + c.label + \'</div>\'\r\n'
    b'      + \'<div class="kpi-value">\' + c.val + \'</div></div>\';\r\n'
    b'  }).join(\'\');\r\n'
    b'\r\n'
    b'  // Chart\r\n'
    b'  var years  = S.map(function(r) { return r.jahr; });\r\n'
    b'  var stands = S.map(function(r) { return r.schuldenstand_teur; });\r\n'
    b'  var prokpf = S.map(function(r) { return r.prokopf_eur; });\r\n'
    b'  var colors = S.map(function(r) {\r\n'
    b'    return r.ist_prognose ? \'rgba(59,130,246,0.35)\' : \'#1e40af\';\r\n'
    b'  });\r\n'
    b'\r\n'
    b'  var traces = [\r\n'
    b'    {\r\n'
    b'      type: \'bar\', name: \'Schuldenstand T\' + \'' + EUR + b'\',\r\n'
    b'      x: years, y: stands,\r\n'
    b'      marker: { color: colors },\r\n'
    b'      yaxis: \'y\',\r\n'
    b'    },\r\n'
    b'    {\r\n'
    b'      type: \'scatter\', mode: \'lines+markers\',\r\n'
    b'      name: \'Pro-Kopf \' + \'' + EUR + b'\' + \'/EW\',\r\n'
    b'      x: years, y: prokpf,\r\n'
    b'      line:   { color: \'#f97316\', width: 2 },\r\n'
    b'      marker: { color: \'#f97316\', size: 6 },\r\n'
    b'      yaxis: \'y2\',\r\n'
    b'    },\r\n'
    b'  ];\r\n'
    b'\r\n'
    b'  var layout = Object.assign({}, DARK_LAYOUT, {\r\n'
    b'    height: 280,\r\n'
    b'    margin: { t: 10, b: 40, l: 55, r: 60 },\r\n'
    b'    bargap: 0.25,\r\n'
    b'    yaxis: {\r\n'
    b'      title: { text: \'T\' + \'' + EUR + b'\', font: { size: 11 } },\r\n'
    b'      gridcolor: \'#334155\',\r\n'
    b'      tickfont: { size: 10 },\r\n'
    b'    },\r\n'
    b'    yaxis2: {\r\n'
    b'      title: { text: \'' + EUR + b'\' + \'/EW\', font: { size: 11 } },\r\n'
    b'      overlaying: \'y\', side: \'right\',\r\n'
    b'      gridcolor: \'rgba(0,0,0,0)\',\r\n'
    b'      tickfont: { size: 10 },\r\n'
    b'    },\r\n'
    b'    legend: { x: 0.01, y: 0.99, bgcolor: \'transparent\', font: { size: 10 } },\r\n'
    b'    annotations: [{\r\n'
    b'      x: 2014, y: 20903, yref: \'y\', xref: \'x\',\r\n'
    b'      text: \'Inkl. Sondertilgung 2013/14\',\r\n'
    b'      showarrow: true, arrowhead: 2, ax: 60, ay: -30,\r\n'
    b'      font: { size: 9, color: \'#94a3b8\' }, arrowcolor: \'#94a3b8\',\r\n'
    b'    }],\r\n'
    b'  });\r\n'
    b'\r\n'
    b'  Plotly.newPlot(el, traces, layout, { responsive: true, displayModeBar: false });\r\n'
    b'}\r\n'
    b'\r\n'
    b'(function() {\r\n'
    b'  var _origRVS = renderVermoegen;\r\n'
    b'  renderVermoegen = function() {\r\n'
    b'    _origRVS();\r\n'
    b'    _renderSchulden();\r\n'
    b'  };\r\n'
    b'})();\r\n'
    b'\r\n'
)


def run():
    content = open(INDEX, "rb").read()
    assert content.count(b"\r\n") > 1000, "CRLF erwartet"

    # 1. HTML einfuegen
    assert HTML_ANCHOR_OLD in content, "HTML-Anker nicht gefunden — Abbruch"
    content = content.replace(HTML_ANCHOR_OLD, HTML_ANCHOR_NEW, 1)
    print("HTML: Schuldenentwicklung-Karte eingefuegt")

    # 2. JS einfuegen
    js_anchor = JS_ANCHOR
    assert js_anchor in content, "JS-Anker (setupTabs) nicht gefunden"
    content = content.replace(js_anchor, NEW_JS + js_anchor, 1)
    print("JS:   _renderSchulden() + Monkey-Patch eingefuegt")

    # 3. Validierung
    bt = content.count(b"\x60")
    assert bt == 132, f"Backtick-Paritaet verletzt: {bt} (erwartet 132)"
    js_start = content.rfind(b"<script>", 0, len(content) - 50000)
    js_end   = content.find(b"</script>", js_start)
    js_block = content[js_start:js_end]
    non_ascii_in_strs = []
    in_str = False
    str_char = b""
    for i, b in enumerate(js_block):
        c = bytes([b])
        if not in_str and c in (b'"', b"'"):
            in_str = True
            str_char = c
        elif in_str and c == str_char:
            in_str = False
        elif in_str and b > 127:
            non_ascii_in_strs.append(i)
    if non_ascii_in_strs:
        print(f"WARNUNG: {len(non_ascii_in_strs)} non-ASCII in JS-Strings (erste Offsets: {non_ascii_in_strs[:5]})")
    else:
        print("OK: Keine non-ASCII-Bytes in JS-Strings")
    print(f"OK: Backticks = {bt}")

    open(INDEX, "wb").write(content)
    size_kb = len(content) // 1024
    print(f"[OK] index.html geschrieben ({size_kb} KB)")


if __name__ == "__main__":
    run()
