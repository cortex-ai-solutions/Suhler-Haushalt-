"""
Simulator + HSK Integration:
  Stufe A: Vorbelastungs-Badge je Teilplan in der Simulator-Liste
  Stufe B: Szenario-Schaltflächen (HSK 2025 / HSK gesamt)
CRLF-sicher, kein Unicode in JS-Strings.
"""

CRLF = "\r\n"

with open("index.html", "rb") as f:
    content = f.read().decode("utf-8")


def apply(c, old, new, label):
    count = c.count(old)
    if count == 0:
        raise ValueError(f"NICHT GEFUNDEN: {label!r}  (Suche: {old[:60]!r})")
    if count > 1:
        raise ValueError(f"NICHT EINDEUTIG ({count}x): {label!r}")
    print(f"  [OK] {label}")
    return c.replace(old, new, 1)


# ── Patch 1: Szenario-Buttons HTML vor der Wechselwirkung-Warnung ─────────────
OLD_WWK = (
    "    <!-- Wechselwirkung Warning -->" + CRLF +
    '    <div class="warn-box mb-6 hidden" id="wwk-warning">'
)
NEW_WWK = CRLF.join([
    "    <!-- HSK-Szenarien -->",
    '    <div class="flex flex-wrap gap-2 items-center mb-5 pb-4 border-b border-slate-700/60">',
    '      <span class="text-sm text-slate-400 mr-1">Szenario&nbsp;laden:</span>',
    '      <button onclick="loadSimSzenario(\'hsk_aktiv\')"',
    '              class="text-xs px-3 py-1.5 rounded-lg border border-blue-700 bg-blue-900/30',
    '                     text-blue-300 hover:bg-blue-800/50 transition-colors">',
    '        &#x25B6; HSK-Ma&szlig;nahmen 2025 (aktiv)',
    '      </button>',
    '      <button onclick="loadSimSzenario(\'hsk_max\')"',
    '              class="text-xs px-3 py-1.5 rounded-lg border border-violet-700 bg-violet-900/30',
    '                     text-violet-300 hover:bg-violet-800/50 transition-colors">',
    '        &#x25B6; HSK vollst&auml;ndig (aktiv + erledigt)',
    '      </button>',
    '      <button onclick="loadSimSzenario(\'reset\')"',
    '              class="text-xs px-3 py-1.5 rounded-lg border border-slate-600 bg-slate-700',
    '                     text-slate-400 hover:bg-slate-600 transition-colors">',
    '        &#x21BA; Zur&uuml;cksetzen',
    '      </button>',
    '      <span class="text-xs text-slate-500 italic" id="sim-szenario-label"></span>',
    '    </div>',
    "",
    "    <!-- Wechselwirkung Warning -->",
    '    <div class="warn-box mb-6 hidden" id="wwk-warning">',
])
content = apply(content, OLD_WWK, NEW_WWK, "Szenario-Buttons HTML")


# ── Patch 2: JS-Block vor setupTabs ──────────────────────────────────────────
OLD_JS_ANCHOR = "function setupTabs() {"

JS_LINES = [
    "// ── Simulator + HSK-Integration ────────────────────────────────────────────",
    "",
    "// HSK-Vorbelastung je Teilplan (kumulierte Einsparungen betrag_gesamt)",
    "function getHskVorbelastungByTP() {",
    "  if (!DATA.hsk) return {};",
    "  var map = {};",
    "  DATA.hsk.massnahmen.forEach(function(m) {",
    "    var seen = {};",
    "    Object.values(m.abgleich || {}).forEach(function(pd) {",
    "      if (!pd.tp_nr || seen[pd.tp_nr]) return;",
    "      seen[pd.tp_nr] = true;",
    "      if (!map[pd.tp_nr]) map[pd.tp_nr] = { gesamt: 0, count: 0 };",
    "      map[pd.tp_nr].gesamt += (m.betrag_gesamt || 0);",
    "      map[pd.tp_nr].count++;",
    "    });",
    "  });",
    "  return map;",
    "}",
    "",
    "// HSK-Einsparziel 2025 je Produkt (nur für aktive/geprueft Maßnahmen)",
    "function getHskSparByProdukt(includeErledigt) {",
    "  if (!DATA.hsk) return {};",
    "  var map = {};",
    "  DATA.hsk.massnahmen.forEach(function(m) {",
    "    if (m.status === 'entfallen') return;",
    "    if (!includeErledigt && m.status === 'erledigt') return;",
    "    // Verknüpfte Produkte zählen für gleichmäßige Verteilung",
    "    var prods = Object.keys(m.abgleich || {});",
    "    if (!prods.length) return;",
    "    var share = (m.betrag_2025 || 0) / prods.length;",
    "    prods.forEach(function(prodNr) {",
    "      map[prodNr] = (map[prodNr] || 0) + share;",
    "    });",
    "  });",
    "  return map;",
    "}",
    "",
    "// Stufe B: Szenario in Schieberegler laden",
    "function loadSimSzenario(type) {",
    "  DATA.simulator_produkte.forEach(function(p) { simState[p.produkt_nummer] = 0; });",
    "  var label = '';",
    "  if (type !== 'reset') {",
    "    var sparMap = getHskSparByProdukt(type === 'hsk_max');",
    "    var n = 0;",
    "    DATA.simulator_produkte.forEach(function(p) {",
    "      if (!p.kk5_2025 || p.max_kuerzung_pct === 0) return;",
    "      var spar = sparMap[p.produkt_nummer] || 0;",
    "      if (!spar) return;",
    "      var pct = Math.round(spar / p.kk5_2025 * 100);",
    "      pct = Math.max(0, Math.min(pct, p.max_kuerzung_pct));",
    "      if (pct > 0) { simState[p.produkt_nummer] = pct; n++; }",
    "    });",
    "    label = type === 'hsk_aktiv'",
    "      ? 'HSK 2025 aktiv — ' + n + ' Produkte mit Zielwert belegt'",
    "      : 'HSK vollst. — ' + n + ' Produkte mit Zielwert belegt';",
    "  }",
    "  var lbl = document.getElementById('sim-szenario-label');",
    "  if (lbl) lbl.textContent = label;",
    "  renderSimListe();",
    "  updateSimErgebnis();",
    "  checkWechselwirkungen();",
    "}",
    "",
    "// Stufe A: renderSimListe mit TP-Trenner + Vorbelastungs-Badge",
    "renderSimListe = function() {",
    "  var filterTP = (document.getElementById('sim-filter-tp') || {}).value || '';",
    "  var filterSK = (document.getElementById('sim-filter-sk') || {}).value || '';",
    "  var liste = document.getElementById('sim-liste');",
    "  liste.innerHTML = '';",
    "  var produkte = DATA.simulator_produkte.slice();",
    "  if (filterTP) produkte = produkte.filter(function(p){ return p.tp_nr === filterTP; });",
    "  if (filterSK) produkte = produkte.filter(function(p){ return p.steuerungs_code === filterSK; });",
    "  if (!produkte.length) {",
    "    liste.innerHTML = '<div class=\"text-slate-500 text-sm\">Keine Produkte f&uuml;r diesen Filter.</div>';",
    "    return;",
    "  }",
    "  var vorb = getHskVorbelastungByTP();",
    "  var hskProdMap = getHskSparByProdukt(true);  // alle Maßnahmen für Badge",
    "  var lastTP = null;",
    "  var PAIN = [",
    "    { min: 0,       col: 'text-emerald-400', bg: 'border-emerald-800/40', bar: '&#x25E6;&#x25E6;&#x25E6;', lbl: 'kaum vorbelastet' },",
    "    { min: 500000,  col: 'text-yellow-400',  bg: 'border-yellow-800/40',  bar: '&#x25CF;&#x25E6;&#x25E6;', lbl: 'leicht vorbelastet' },",
    "    { min: 2000000, col: 'text-orange-400',  bg: 'border-orange-800/40',  bar: '&#x25CF;&#x25CF;&#x25E6;', lbl: 'stark vorbelastet' },",
    "    { min: 5000000, col: 'text-rose-400',    bg: 'border-rose-800/40',    bar: '&#x25CF;&#x25CF;&#x25CF;', lbl: 'sehr stark vorbelastet' }",
    "  ];",
    "  produkte.forEach(function(p) {",
    "    // TP-Trennzeile",
    "    if (p.tp_nr !== lastTP) {",
    "      lastTP = p.tp_nr;",
    "      var vd = vorb[p.tp_nr] || { gesamt: 0, count: 0 };",
    "      var pl = 0;",
    "      for (var pi2 = PAIN.length - 1; pi2 >= 0; pi2--) {",
    "        if (vd.gesamt >= PAIN[pi2].min) { pl = pi2; break; }",
    "      }",
    "      var pain = PAIN[pl];",
    "      var badgeHtml = '';",
    "      if (vd.gesamt > 0) {",
    "        badgeHtml = '<span class=\"text-[10px] ' + pain.col + '\" title=\"' + pain.lbl + '\">' +",
    "          pain.bar + '&ensp;bereits +' + fmt(vd.gesamt/1000000, 1) + ' Mio&euro; konsolidiert' +",
    "          ' (' + vd.count + ' Ma&szlig;n.)</span>';",
    "      }",
    "      var hdr = document.createElement('div');",
    "      hdr.className = 'flex items-center justify-between mt-3 mb-1 pt-2 border-b ' + pain.bg;",
    "      hdr.innerHTML = '<span class=\"text-sm font-semibold text-slate-300\">TP ' + p.tp_nr +",
    "        ' &ndash; ' + escHtml(p.tp_name || '') + '</span>' + badgeHtml;",
    "      liste.appendChild(hdr);",
    "    }",
    "    // Produkt-Karte",
    "    var locked = p.max_kuerzung_pct === 0;",
    "    var cur = simState[p.produkt_nummer] || 0;",
    "    var hskSpar = hskProdMap[p.produkt_nummer] || 0;",
    "    var hskBadge = '';",
    "    if (hskSpar && p.kk5_2025) {",
    "      var hskPct = hskSpar / p.kk5_2025 * 100;",
    "      hskBadge = '<span class=\"text-[9px] ml-1 px-1 py-0.5 rounded bg-blue-900/30 text-blue-300\"' +",
    "        ' title=\"HSK-Einsparziel (aktiv+erl.): +' + fmt(hskSpar/1000, 1) + ' T€\">' +",
    "        'HSK&thinsp;' + hskPct.toFixed(hskPct < 1 ? 1 : 0) + '%</span>';",
    "    }",
    "    var card = document.createElement('div');",
    "    card.className = 'card p-3 mb-1';",
    "    card.innerHTML =",
    "      '<div class=\"flex items-start justify-between gap-2 mb-2\">' +",
    "        '<div>' +",
    "          '<span class=\"font-medium text-sm text-slate-200\">' + escHtml(p.bezeichnung) + '</span>' +",
    "          '<span class=\"ml-2 text-xs text-slate-500\">' + p.produkt_nummer + '</span>' +",
    "          '<span class=\"ml-1 tag ' + skTagClass(p.steuerungs_code) + '\">' +",
    "            (SK_LABEL[p.steuerungs_code] || p.steuerungs_code) + '</span>' +",
    "          hskBadge +",
    "        '</div>' +",
    "        '<div class=\"text-right text-sm shrink-0 text-slate-400\">' + fmtMio(p.kk5_2025) + '</div>' +",
    "      '</div>' +",
    "      '<div class=\"slider-row\">' +",
    "        '<input type=\"range\" min=\"0\" max=\"' + p.max_kuerzung_pct + '\" step=\"1\" value=\"' + cur + '\"' +",
    "          (locked ? ' disabled' : '') +",
    "          ' data-pnr=\"' + p.produkt_nummer + '\" oninput=\"onSlider(this)\"' +",
    "          ' class=\"' + (locked ? 'opacity-30 cursor-not-allowed' : '') + '\">' +",
    "        '<div class=\"text-sm text-center\">' +",
    "          '<span id=\"pct-' + p.produkt_nummer + '\" class=\"' +",
    "            (cur > 0 ? 'text-emerald-400' : 'text-slate-400') + '\">' + cur + '%</span>' +",
    "          (locked",
    "            ? '<span class=\"ml-1 text-xs text-slate-600\">gesperrt</span>'",
    "            : '<span class=\"text-xs text-slate-500\"> von max.&nbsp;' + p.max_kuerzung_pct + '%</span>') +",
    "        '</div>' +",
    "        '<div class=\"text-sm text-right\">' +",
    "          '<span id=\"sav-' + p.produkt_nummer + '\" class=\"text-emerald-400\">' +",
    "            (cur > 0 ? '&minus;' + fmtMio(p.kk5_2025 * cur / 100) : '') + '</span>' +",
    "        '</div>' +",
    "      '</div>' +",
    "      (p.rechtsgrundlage",
    "        ? '<details class=\"mt-2\"><summary class=\"text-xs text-slate-500 cursor-pointer hover:text-slate-300 select-none py-0.5\">&sect; Rechtsgrundlage</summary>' +",
    "          '<div class=\"mt-1 text-xs text-slate-400 leading-relaxed border-l-2 border-slate-600 pl-2\">' +",
    "          escHtml(p.rechtsgrundlage) + '</div></details>'",
    "        : '');",
    "    liste.appendChild(card);",
    "  });",
    "};",
    "",
    "function setupTabs() {",
]

NEW_JS_BLOCK = CRLF.join(JS_LINES)
content = apply(content, OLD_JS_ANCHOR, NEW_JS_BLOCK, "Simulator+HSK JS-Block")


with open("index.html", "wb") as f:
    f.write(content.encode("utf-8"))

bt = content.count("\x60")
print(f"\nBackticks: {bt} ({'GERADE' if bt % 2 == 0 else 'UNGERADE!'})")
print("Fertig. index.html aktualisiert.")
