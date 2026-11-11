"""
Verlinkung Simulator → HSK-Tab:
- TP-Header im Simulator sind anklickbar → öffnen HSK-Tab gefiltert nach TP
- TP-Filter-Info-Zeile im HSK-Tab (mit × zum Entfernen)
- Monkey-patch renderHskTable respektiert _hskTPFilter
- Monkey-patch renderSimListe ergänzt data-Attribute + click-Handler auf TP-Header
CRLF-sicher.
"""

CRLF = "\r\n"

with open("index.html", "rb") as f:
    content = f.read().decode("utf-8")


def apply(c, old, new, label):
    count = c.count(old)
    if count == 0:
        raise ValueError(f"NICHT GEFUNDEN: {label!r}  (Suche: {old[:70]!r})")
    if count > 1:
        raise ValueError(f"NICHT EINDEUTIG ({count}x): {label!r}")
    print(f"  [OK] {label}")
    return c.replace(old, new, 1)


# ── Patch 1: TP-Filter-Info-Zeile im HSK-Tab (vor dem Suchfeld) ───────────────
OLD_HSK_SEARCH = (
    '      <input id="hsk-search" type="text" placeholder="Maßnahme suchen…"'
)
NEW_HSK_SEARCH = CRLF.join([
    '      <div id="hsk-tp-filter-info" class="hidden w-full flex items-center',
    '           gap-2 px-3 py-1.5 rounded-lg bg-blue-900/30 border border-blue-700/60 text-xs">',
    '        <span class="text-blue-300">&#x1F50D; TP-Filter aktiv:</span>',
    '        <span id="hsk-tp-filter-label" class="text-blue-200 font-medium flex-1"></span>',
    '        <button onclick="clearHskTPFilter()"',
    '                class="text-blue-400 hover:text-white px-2 py-0.5 rounded border border-blue-700',
    '                       hover:bg-blue-700 transition-colors text-[10px]">',
    '          &times; Filter entfernen',
    '        </button>',
    '      </div>',
    '      <input id="hsk-search" type="text" placeholder="Maßnahme suchen…"',
])
content = apply(content, OLD_HSK_SEARCH, NEW_HSK_SEARCH, "HSK TP-Filter-Info HTML")


# ── Patch 2: sim-tp-header Klasse + data-Attribute im renderSimListe ──────────
OLD_HDR_CLASS = (
    "      hdr.className = 'flex items-center justify-between mt-3 mb-1 pt-2 border-b ' + pain.bg;"
)
NEW_HDR_CLASS = CRLF.join([
    "      hdr.className = 'sim-tp-header flex items-center justify-between mt-3 mb-1 pt-2 border-b cursor-pointer hover:bg-slate-800/30 rounded-sm px-1 transition-colors ' + pain.bg;",
    "      hdr.dataset.tpNr   = p.tp_nr;",
    "      hdr.dataset.tpName = p.tp_name || '';",
    "      hdr.title = 'HSK-Ma\\u00dfnahmen f\\u00fcr TP ' + p.tp_nr + ' anzeigen';",
])
content = apply(content, OLD_HDR_CLASS, NEW_HDR_CLASS, "sim-tp-header Klasse + data-Attribute")


# ── Patch 3: JS-Block (Navigation + TP-Filter) vor setupTabs ──────────────────
OLD_JS_ANCHOR = "function setupTabs() {"

JS_LINES = [
    "// ── HSK-Navigation vom Simulator ───────────────────────────────────────────",
    "",
    "var _hskTPFilter = null;",
    "",
    "function navigateToHskTP(tpNr, tpName) {",
    "  _hskTPFilter = tpNr;",
    "  // Tab wechseln",
    "  var TABS2 = ['overview','details','personal','jahresvergleich','zeitreihe','hsk','simulator'];",
    "  document.querySelectorAll('#tabbar .tab').forEach(function(t){ t.classList.remove('active'); });",
    "  var hskTab = document.querySelector('[data-tab=\"hsk\"]');",
    "  if (hskTab) hskTab.classList.add('active');",
    "  TABS2.forEach(function(t){",
    "    var el = document.getElementById('tab-' + t);",
    "    if (el) el.classList.toggle('hidden', t !== 'hsk');",
    "  });",
    "  // Filter-Info einblenden",
    "  var info = document.getElementById('hsk-tp-filter-info');",
    "  var lbl  = document.getElementById('hsk-tp-filter-label');",
    "  if (info) info.classList.remove('hidden');",
    "  if (lbl)  lbl.textContent = 'TP ' + tpNr + ' \\u2013 ' + tpName;",
    "  // HSK rendern",
    "  if (typeof initHsk === 'function') initHsk();",
    "  if (typeof renderHsk === 'function') renderHsk();",
    "  // Zur Tabelle scrollen",
    "  var tbl = document.getElementById('hsk-tabelle');",
    "  if (tbl) tbl.scrollIntoView({ behavior: 'smooth', block: 'start' });",
    "}",
    "",
    "function clearHskTPFilter() {",
    "  _hskTPFilter = null;",
    "  var info = document.getElementById('hsk-tp-filter-info');",
    "  if (info) info.classList.add('hidden');",
    "  if (typeof renderHsk === 'function') renderHsk();",
    "}",
    "",
    "// renderHskTable: TP-Filter anwenden (Wrapper uber bestehenden Monkey-Patch)",
    "var _rht_tp_orig = renderHskTable;",
    "renderHskTable = function() {",
    "  if (!_hskTPFilter) { _rht_tp_orig(); return; }",
    "  var allM = DATA.hsk.massnahmen;",
    "  DATA.hsk.massnahmen = allM.filter(function(m) {",
    "    return Object.values(m.abgleich || {}).some(function(pd) {",
    "      return pd.tp_nr === _hskTPFilter;",
    "    });",
    "  });",
    "  _rht_tp_orig();",
    "  DATA.hsk.massnahmen = allM;",
    "};",
    "",
    "// renderSimListe: click-Handler auf TP-Header nachtraglich erganzen",
    "var _rsl_link_orig = renderSimListe;",
    "renderSimListe = function() {",
    "  _rsl_link_orig();",
    "  document.querySelectorAll('.sim-tp-header').forEach(function(hdr) {",
    "    hdr.onclick = function() {",
    "      navigateToHskTP(hdr.dataset.tpNr, hdr.dataset.tpName);",
    "    };",
    "  });",
    "};",
    "",
    "function setupTabs() {",
]

NEW_JS_BLOCK = CRLF.join(JS_LINES)
content = apply(content, OLD_JS_ANCHOR, NEW_JS_BLOCK, "Navigation + TP-Filter JS")


with open("index.html", "wb") as f:
    f.write(content.encode("utf-8"))

bt = content.count("\x60")
print(f"\nBackticks: {bt} ({'GERADE' if bt % 2 == 0 else 'UNGERADE!'})")
print("Fertig. index.html aktualisiert.")
