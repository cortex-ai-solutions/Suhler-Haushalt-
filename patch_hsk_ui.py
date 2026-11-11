"""
HSK UI-Update: Balkendiagramm fuer Jahresverlauf + verbesserter Soll/Ist-Abgleich.
CRLF-sicher, kein Unicode in JS, keine Template-Literal-Modifikationen.
"""

CRLF = "\r\n"

with open("index.html", "rb") as f:
    content = f.read().decode("utf-8")


def apply(c, old, new, label):
    count = c.count(old)
    if count == 0:
        raise ValueError(f"NICHT GEFUNDEN: {label!r}")
    if count > 1:
        raise ValueError(f"NICHT EINDEUTIG ({count}x): {label!r}")
    print(f"  [OK] {label}")
    return c.replace(old, new, 1)


# Anchor: function setupTabs() { (erscheint genau einmal)
OLD_ANCHOR = "function setupTabs() {"

LINES = [
    "// ── HSK UI: Diagramm + verbesserter Abgleich ────────────────────────────────",
    "",
    "// Ersetzt buildHskJahreswerte: Chart-Container + Metadaten",
    "buildHskJahreswerte = function(m) {",
    "  var nz = Object.entries(m.jahreswerte || {}).filter(function(e){ return e[1] !== 0; });",
    "  if (!nz.length) return '<span class=\"text-slate-500 text-xs\">Keine Jahreswerte erfasst</span>';",
    "  var fT = function(v) {",
    "    return (v >= 0 ? '+' : '') + fmt(Math.abs(v)/1000, Math.abs(v)<100000 ? 1 : 0) + ' T&euro;';",
    "  };",
    "  return '<div id=\"hsk-jw-chart-' + m.id + '\" style=\"height:140px;width:100%\"></div>' +",
    "    '<div class=\"flex flex-wrap gap-x-4 text-[10px] mt-1 text-slate-400\">' +",
    "    (m.wirksam_ab ? '<span>Wirksam ab: <span class=\"text-slate-200\">' + m.wirksam_ab + '</span></span>' : '') +",
    "    '<span>Sparwirkung gesamt: <span class=\"text-emerald-400\">' + fT(m.betrag_gesamt) + '</span></span>' +",
    "    '</div>';",
    "};",
    "",
    "// Rendert Plotly-Balkendiagramm wenn Detailzeile geoeffnet wird",
    "function renderHskJwChart(m) {",
    "  var el = document.getElementById('hsk-jw-chart-' + m.id);",
    "  if (!el || el.dataset.rendered) return;",
    "  el.dataset.rendered = '1';",
    "  var yrs = Object.keys(m.jahreswerte || {}).sort();",
    "  var vals = yrs.map(function(y){ return Math.round((m.jahreswerte[y]||0)/1000); });",
    "  var ws = String(m.wirksam_ab || '');",
    "  var cols = yrs.map(function(y,i){",
    "    if (vals[i] > 0) return y === ws ? '#059669' : '#34d399';",
    "    if (vals[i] < 0) return '#f87171';",
    "    return '#1e293b';",
    "  });",
    "  var anno = ws ? [{",
    "    x: ws, y: 1.1, yref: 'paper',",
    "    text: '&#x25BC; ' + ws,",
    "    font: { color: '#6ee7b7', size: 8 },",
    "    showarrow: false, xanchor: 'center', yanchor: 'bottom'",
    "  }] : [];",
    "  Plotly.newPlot(el,",
    "    [{ type: 'bar', x: yrs, y: vals, marker: { color: cols },",
    "       hovertemplate: '%{x}: %{y:+.0f} T€<extra></extra>' }],",
    "    Object.assign({}, DARK_LAYOUT, {",
    "      margin: { t: 20, b: 32, l: 36, r: 4 },",
    "      xaxis: { color: '#475569', tickfont: { size: 8, color: '#64748b' }, tickangle: -45 },",
    "      yaxis: { color: '#475569', tickfont: { size: 9, color: '#64748b' }, ticksuffix: 'T' },",
    "      annotations: anno",
    "    }),",
    "    { displayModeBar: false, responsive: true }",
    "  );",
    "}",
    "",
    "// toggleHskRow: Chart rendern wenn Zeile geoeffnet wird",
    "var _thr_orig = toggleHskRow;",
    "toggleHskRow = function(tr, mid) {",
    "  _thr_orig(tr, mid);",
    "  var det = document.getElementById('hsk-detail-' + mid);",
    "  if (det && !det.classList.contains('hidden')) {",
    "    var m = (DATA.hsk && DATA.hsk.massnahmen || []).find(function(x){ return x.id === mid; });",
    "    if (m) renderHskJwChart(m);",
    "  }",
    "};",
    "",
    "// buildAbgleichCard: IST/PLAN-Badges, Euro-Zeichen, Gesamt-Delta",
    "buildAbgleichCard = function(m) {",
    "  var prods = Object.entries(m.abgleich || {});",
    "  if (!prods.length) return '';",
    "  var useKK = m.kategorie === 'ERTRAG' ? 'kk4' : 'kk5';",
    "  var kkLbl = m.kategorie === 'ERTRAG' ? 'Ertr&auml;ge (KK4)' : 'Aufwend. (KK5)';",
    "  var fmtV = function(v) { return fmt(Math.abs(v)/1000, Math.abs(v)<100000 ? 1 : 0) + ' T&euro;'; };",
    "  var html = '<div class=\"text-[10px] text-slate-500 italic mb-2\">' +",
    "    'HSK-Einsparziel = Konsolidierungsbeitrag dieser Ma&szlig;nahme &bull; ' +",
    "    'Haushaltsansatz = Gesamtbudget des Produkts</div>';",
    "  for (var pi = 0; pi < prods.length; pi++) {",
    "    var prodNr = prods[pi][0], pd = prods[pi][1];",
    "    var pName = (pd.bezeichnung && pd.bezeichnung !== 'Produkt ' + prodNr) ? pd.bezeichnung : '';",
    "    var tpLbl = pd.tp_nr ? ' &bull; TP' + pd.tp_nr : '';",
    "    html += '<div class=\"text-[10px] text-slate-400 mb-1 font-mono\">' +",
    "      prodNr + (pName ? ' <span class=\"font-sans text-slate-300\">&ndash; ' + pName + '</span>' : '') +",
    "      tpLbl + '</div>';",
    "    html += '<table class=\"w-full text-xs mb-3\">';",
    "    html += '<thead><tr class=\"text-slate-500 border-b border-slate-700 text-[10px]\">';",
    "    html += '<th class=\"text-left py-1 pr-1\">Jahr</th>';",
    "    html += '<th class=\"text-right py-1 pr-2\">HSK-Einsparziel</th>';",
    "    html += '<th class=\"text-right py-1 pr-2\">' + kkLbl + '</th>';",
    "    html += '<th class=\"text-right py-1\">Ver&auml;nd. gg. Vj.</th>';",
    "    html += '</tr></thead><tbody>';",
    "    var YRS = ['2022','2023','2024','2025'];",
    "    var prevKK = null, fKK = null, fYr = null, lKK = null, lYr = null;",
    "    for (var yi = 0; yi < YRS.length; yi++) {",
    "      var yr = YRS[yi];",
    "      var jd = (pd.jahre || {})[yr];",
    "      var kk = jd ? (jd[useKK] || 0) : 0;",
    "      var hsk = jd ? (jd.hsk_ziel || 0) : 0;",
    "      var wt = jd ? (jd.wert_typ || '') : '';",
    "      var badge = wt ? '<span class=\"ml-1 px-1 rounded text-[9px] ' +",
    "        (wt==='IST' ? 'text-teal-400 bg-teal-900/40' : 'text-blue-400 bg-blue-900/40') +",
    "        '\">' + wt + '</span>' : '';",
    "      var hskFmt = hsk ? (hsk>0?'+':'') + fmtV(hsk) : '&ndash;';",
    "      var kkFmt2 = kk ? fmtV(kk) : '&ndash;';",
    "      var entw = '<span class=\"text-slate-600\">&ndash;</span>';",
    "      if (prevKK !== null && kk) {",
    "        var dv = kk - prevKK;",
    "        var good = m.kategorie === 'ERTRAG' ? dv > 0 : dv < 0;",
    "        var cl = good ? 'text-emerald-400' : 'text-rose-400';",
    "        var ar = dv > 0 ? '&uarr;' : (dv < 0 ? '&darr;' : '&rarr;');",
    "        entw = '<span class=\"' + cl + '\">' + ar + '&thinsp;' + fmtV(dv) + '</span>';",
    "      }",
    "      if (kk) { if (fKK===null){fKK=kk;fYr=yr;} lKK=kk; lYr=yr; prevKK=kk; }",
    "      html += '<tr class=\"border-b border-slate-800\">';",
    "      html += '<td class=\"py-1 pr-1 text-slate-400\">' + yr + badge + '</td>';",
    "      html += '<td class=\"py-1 pr-2 text-right text-blue-300 font-mono\">' + hskFmt + '</td>';",
    "      html += '<td class=\"py-1 pr-2 text-right text-slate-200 font-mono\">' + kkFmt2 + '</td>';",
    "      html += '<td class=\"py-1 text-right\">' + entw + '</td>';",
    "      html += '</tr>';",
    "    }",
    "    if (fKK && lKK && fYr !== lYr) {",
    "      var td3 = lKK - fKK;",
    "      var g3 = m.kategorie === 'ERTRAG' ? td3 > 0 : td3 < 0;",
    "      var c3 = g3 ? 'text-emerald-400' : 'text-rose-400';",
    "      var a3 = td3 > 0 ? '&uarr;' : (td3 < 0 ? '&darr;' : '&rarr;');",
    "      html += '<tr class=\"border-t border-slate-600\">';",
    "      html += '<td class=\"py-1 pr-1 text-slate-500 text-[10px]\">' + fYr + '&rarr;' + lYr + '</td>';",
    "      html += '<td class=\"py-1 pr-2\"></td>';",
    "      html += '<td class=\"py-1 pr-2 text-slate-500 text-[10px] text-right\">Gesamt&auml;nd.</td>';",
    "      html += '<td class=\"py-1 text-right\"><span class=\"' + c3 + '\">' +",
    "        a3 + '&thinsp;' + fmtV(td3) + '</span></td>';",
    "      html += '</tr>';",
    "    }",
    "    html += '</tbody></table>';",
    "  }",
    "  return html;",
    "};",
    "",
    "function setupTabs() {",
]

NEW_BLOCK = CRLF.join(LINES)
content = apply(content, OLD_ANCHOR, NEW_BLOCK, "HSK-UI-Block (Chart + Abgleich)")

with open("index.html", "wb") as f:
    f.write(content.encode("utf-8"))

bt = content.count("\x60")
print(f"\nBackticks: {bt} ({'GERADE' if bt%2==0 else 'UNGERADE!'})")
print("Fertig.")
