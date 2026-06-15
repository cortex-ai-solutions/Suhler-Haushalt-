"""
patch_personalquote.py
Fixes:
  1. pers-kpi-quote: nutzt jetzt y.personalquote_pct aus DATA.personal.by_year
  2. Neue Karte "Personalquote im Zeitverlauf" (2021-2025) nach chart-pers-trend
"""

INDEX = "index.html"

# ── 1. JS-Fix: alte fehlerhafte Berechnung ersetzen ──────────────────────────
JS_OLD = (
    b'  const ydMeta = getYD() && getYD().meta;\r\n'
    b'  const quote = ydMeta && ydMeta.aufwendungen_kk5 ? y.gesamt / ydMeta.aufwendungen_kk5 * 100 : null;\r\n'
    b'  document.getElementById("pers-kpi-quote").textContent = '
    b'quote !== null ? fmt(quote, 1) + "\xc2\xa0%" : "\xe2\x80\x93";'
)
JS_NEW = (
    b'  const quote = (y.personalquote_pct != null) ? y.personalquote_pct : null;\r\n'
    b'  document.getElementById("pers-kpi-quote").textContent = '
    b'quote !== null ? fmt(quote, 1) + "\xc2\xa0%" : "\xe2\x80\x93";'
)

# ── 2. HTML: neue Karte nach chart-pers-trend ─────────────────────────────────
HTML_ANCHOR_OLD = (
    b'chart-pers-trend" class="plotly-chart" style="height:280px"></div>\r\n'
    b'  </div>\r\n'
    b'\r\n'
    b'  <!-- Detail-Tabelle -->'
)
HTML_ANCHOR_NEW = (
    b'chart-pers-trend" class="plotly-chart" style="height:280px"></div>\r\n'
    b'  </div>\r\n'
    b'\r\n'
    b'  <!-- Personalquote Zeitreihe -->\r\n'
    b'  <div class="card p-5 mb-6">\r\n'
    b'    <div class="section-title">Personalquote im Zeitverlauf 2021&#8211;2025</div>\r\n'
    b'    <p class="text-slate-400 text-xs mb-3">'
    b'Personalaufwand (Konten 50xx) als Anteil an Gesamtaufwendungen (KK5). '
    b'IST 2021&#8211;2023, Plan 2024/2025.</p>\r\n'
    b'    <div id="chart-pers-quote-trend" style="height:220px"></div>\r\n'
    b'  </div>\r\n'
    b'\r\n'
    b'  <!-- Detail-Tabelle -->'
)

# ── 3. JS: _renderPersonalquote + Monkey-Patch ─────────────────────────────────
JS_ANCHOR = b'\r\nfunction setupTabs() {'

PCTPCT = b'%'

NEW_JS = (
    b'// \xe2\x80\x94 Personalquote-Zeitreihe \xe2\x80\x94\r\n'
    b'function _renderPersonalquote() {\r\n'
    b'  var el = document.getElementById(\'chart-pers-quote-trend\');\r\n'
    b'  if (!el || !DATA.personal || !DATA.personal.personalquote_zeitreihe) return;\r\n'
    b'  var pqz = DATA.personal.personalquote_zeitreihe;\r\n'
    b'  var years  = pqz.map(function(r) { return r.label; });\r\n'
    b'  var quotes = pqz.map(function(r) { return r.quote_pct; });\r\n'
    b'  var mcolors = pqz.map(function(r) {\r\n'
    b'    return r.ist_prognose ? \'rgba(251,146,60,0.6)\' : \'#f97316\';\r\n'
    b'  });\r\n'
    b'\r\n'
    b'  Plotly.newPlot(el, [\r\n'
    b'    {\r\n'
    b'      type: \'scatter\', mode: \'lines+markers\',\r\n'
    b'      name: \'Personalquote\',\r\n'
    b'      x: years, y: quotes,\r\n'
    b'      line:   { color: \'#f97316\', width: 2.5 },\r\n'
    b'      marker: { color: mcolors, size: 8, line: { color: \'#f97316\', width: 1 } },\r\n'
    b'      hovertemplate: \'<b>%{x}</b><br>Personalquote: %{y:.1f} %<extra></extra>\',\r\n'
    b'    },\r\n'
    b'    {\r\n'
    b'      type: \'bar\',\r\n'
    b'      name: \'Personalaufwand T\\u20ac\',\r\n'
    b'      x: years,\r\n'
    b'      y: pqz.map(function(r) { return r.personal_teur; }),\r\n'
    b'      marker: { color: pqz.map(function(r) {\r\n'
    b'        return r.ist_prognose ? \'rgba(129,140,248,0.35)\' : \'rgba(129,140,248,0.7)\';\r\n'
    b'      }) },\r\n'
    b'      yaxis: \'y2\',\r\n'
    b'      hovertemplate: \'<b>%{x}</b><br>%{y:,.0f} T\\u20ac<extra></extra>\',\r\n'
    b'    },\r\n'
    b'  ], Object.assign({}, DARK_LAYOUT, {\r\n'
    b'    height: 200,\r\n'
    b'    margin: { t: 10, b: 50, l: 45, r: 55 },\r\n'
    b'    yaxis: {\r\n'
    b'      title: { text: \'% von KK5\', font: { size: 11 } },\r\n'
    b'      range: [20, 32],\r\n'
    b'      gridcolor: \'#334155\', tickfont: { size: 10 },\r\n'
    b'      ticksuffix: \' %\',\r\n'
    b'    },\r\n'
    b'    yaxis2: {\r\n'
    b'      title: { text: \'T\\u20ac\', font: { size: 11 } },\r\n'
    b'      overlaying: \'y\', side: \'right\',\r\n'
    b'      gridcolor: \'rgba(0,0,0,0)\', tickfont: { size: 10 },\r\n'
    b'    },\r\n'
    b'    legend: { x: 0.01, y: 0.99, bgcolor: \'transparent\', font: { size: 10 } },\r\n'
    b'    barmode: \'group\',\r\n'
    b'  }), { responsive: true, displayModeBar: false });\r\n'
    b'}\r\n'
    b'\r\n'
    b'(function() {\r\n'
    b'  var _origRP = renderPersonal;\r\n'
    b'  renderPersonal = function() { _origRP(); _renderPersonalquote(); };\r\n'
    b'})();\r\n'
    b'\r\n'
)


def run():
    content = open(INDEX, "rb").read()
    assert content.count(b"\r\n") > 1000, "CRLF erwartet"

    # 1. JS-Fix
    assert JS_OLD in content, "JS_OLD nicht gefunden — Abbruch"
    content = content.replace(JS_OLD, JS_NEW, 1)
    print("JS-Fix: pers-kpi-quote verwendet jetzt y.personalquote_pct")

    # 2. HTML neue Karte
    assert HTML_ANCHOR_OLD in content, "HTML_ANCHOR_OLD nicht gefunden"
    content = content.replace(HTML_ANCHOR_OLD, HTML_ANCHOR_NEW, 1)
    print("HTML: Personalquote-Karte eingefuegt")

    # 3. JS Funktion + Monkey-Patch
    assert JS_ANCHOR in content, "JS_ANCHOR (setupTabs) nicht gefunden"
    content = content.replace(JS_ANCHOR, NEW_JS + JS_ANCHOR, 1)
    print("JS:   _renderPersonalquote() + Monkey-Patch eingefuegt")

    # Validierung
    bt = content.count(b"\x60")
    assert bt == 132, f"Backtick-Paritaet verletzt: {bt}"
    print(f"OK: Backticks = {bt}")

    open(INDEX, "wb").write(content)
    size_kb = len(content) // 1024
    print(f"[OK] index.html ({size_kb} KB)")


if __name__ == "__main__":
    run()
