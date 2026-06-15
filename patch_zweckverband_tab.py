"""
patch_zweckverband_tab.py
Fuegt 4. Subtab "Zweckverbände" im Vermoegen-Tab hinzu.
Daten: DATA["zweckverbände"] aus budget_data.json (13 Eintraege, Kategorien 6)
"""

INDEX = "index.html"

# ── 1. Subtab-Button nach Beteiligungen ──────────────────────────────────────
BTN_OLD = (
    b'      <button class="vermoegen-subtab" data-vtab="beteiligungen" onclick="_switchVTab(\'beteiligungen\')"\r\n'
    b'              style="padding:0.5rem 1.25rem;background:transparent;border:none;\r\n'
    b'                     color:#94a3b8;border-bottom:2px solid transparent;cursor:pointer;font-size:0.875rem;">\r\n'
    b'        Beteiligungen\r\n'
    b'      </button>\r\n'
    b'    </div>\r\n'
)

BTN_NEW = (
    b'      <button class="vermoegen-subtab" data-vtab="beteiligungen" onclick="_switchVTab(\'beteiligungen\')"\r\n'
    b'              style="padding:0.5rem 1.25rem;background:transparent;border:none;\r\n'
    b'                     color:#94a3b8;border-bottom:2px solid transparent;cursor:pointer;font-size:0.875rem;">\r\n'
    b'        Beteiligungen\r\n'
    b'      </button>\r\n'
    b'      <button class="vermoegen-subtab" data-vtab="zvb" onclick="_switchVTab(\'zvb\')"\r\n'
    b'              style="padding:0.5rem 1.25rem;background:transparent;border:none;\r\n'
    b'                     color:#94a3b8;border-bottom:2px solid transparent;cursor:pointer;font-size:0.875rem;">\r\n'
    b'        Zweckverb\xc3\xa4nde\r\n'
    b'      </button>\r\n'
    b'    </div>\r\n'
)

# ── 2. HTML: neues Subtab-Content-Div nach vtab-beteiligungen ─────────────────
HTML_OLD = b'</div><!-- /vtab-beteiligungen -->\r\n\r\n  </div>\r\n</div>\r\n<div id="drilldown-overlay"'

HTML_NEW = (
    b'</div><!-- /vtab-beteiligungen -->\r\n'
    b'\r\n'
    b'    <div id="vtab-zvb" class="hidden">\r\n'
    b'      <p class="text-slate-400 text-sm mb-5">\r\n'
    b'        Suhl ist Mitglied in 13 Zweckverb\xc3\xa4nden f\xc3\xbcr Pflichtaufgaben der Daseinsvorsorge\r\n'
    b'        (Quelle: Beteiligungsbericht GJ\xc2\xa02024, S.\xc2\xa080\xe2\x80\x9386).\r\n'
    b'      </p>\r\n'
    b'\r\n'
    b'      <!-- KPI-Chips -->\r\n'
    b'      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">\r\n'
    b'        <div class="card p-4 text-center">\r\n'
    b'          <div class="text-2xl font-bold text-blue-400">13</div>\r\n'
    b'          <div class="text-xs text-slate-400 mt-1">Zweckverb\xc3\xa4nde gesamt</div>\r\n'
    b'        </div>\r\n'
    b'        <div class="card p-4 text-center">\r\n'
    b'          <div class="text-2xl font-bold text-cyan-400">4</div>\r\n'
    b'          <div class="text-xs text-slate-400 mt-1">Wasser &amp; Abwasser</div>\r\n'
    b'        </div>\r\n'
    b'        <div class="card p-4 text-center">\r\n'
    b'          <div class="text-2xl font-bold text-orange-400">3</div>\r\n'
    b'          <div class="text-xs text-slate-400 mt-1">Gew\xc3\xa4sserunterhaltung</div>\r\n'
    b'        </div>\r\n'
    b'        <div class="card p-4 text-center">\r\n'
    b'          <div class="text-2xl font-bold text-yellow-400">6</div>\r\n'
    b'          <div class="text-xs text-slate-400 mt-1">Kategorien</div>\r\n'
    b'        </div>\r\n'
    b'      </div>\r\n'
    b'\r\n'
    b'      <!-- Tabelle -->\r\n'
    b'      <div class="card p-5">\r\n'
    b'        <div class="section-title mb-3">Mitgliedschaften nach Kategorie</div>\r\n'
    b'        <div id="zvb-table-container"></div>\r\n'
    b'      </div>\r\n'
    b'    </div><!-- /vtab-zvb -->\r\n'
    b'\r\n'
    b'  </div>\r\n'
    b'</div>\r\n'
    b'<div id="drilldown-overlay"'
)

# ── 3. JS: _switchVTab Erweiterung + _renderZweckverbände ────────────────────
JS_ANCHOR = b'\r\nfunction setupTabs() {'

# Note: DATA["zweckverbände"] uses JS Unicode escape for ä in bracket notation
NEW_JS = (
    b'// -- Zweckverb\xc3\xa4nde Subtab --\r\n'
    b'var _zvbRendered = false;\r\n'
    b'function _renderZvb() {\r\n'
    b'  if (_zvbRendered) return;\r\n'
    b'  var el = document.getElementById(\'zvb-table-container\');\r\n'
    b'  var zvb = DATA["zweckverb\\u00e4nde"];\r\n'
    b'  if (!el || !zvb || !zvb.length) return;\r\n'
    b'\r\n'
    b'  var CATS = {\r\n'
    b'    WASSER:    { label: \'Wasser &amp; Abwasser\',      color: \'#3b82f6\' },\r\n'
    b'    GEWAESSER: { label: \'Gew\\u00e4sserunterhaltung\', color: \'#06b6d4\' },\r\n'
    b'    RETTUNG:   { label: \'Rettungsdienst\',            color: \'#ef4444\' },\r\n'
    b'    ABFALL:    { label: \'Abfallwirtschaft\',          color: \'#f97316\' },\r\n'
    b'    ENERGIE:   { label: \'Energie &amp; IT\',           color: \'#eab308\' },\r\n'
    b'    SONSTIGES: { label: \'Sonstiges\',                 color: \'#94a3b8\' },\r\n'
    b'  };\r\n'
    b'  var ORDER = [\'WASSER\',\'GEWAESSER\',\'RETTUNG\',\'ABFALL\',\'ENERGIE\',\'SONSTIGES\'];\r\n'
    b'\r\n'
    b'  var grouped = {};\r\n'
    b'  ORDER.forEach(function(c) { grouped[c] = []; });\r\n'
    b'  zvb.forEach(function(v) {\r\n'
    b'    if (grouped[v.kategorie]) grouped[v.kategorie].push(v);\r\n'
    b'  });\r\n'
    b'\r\n'
    b'  var html = \'\';\r\n'
    b'  ORDER.forEach(function(cat) {\r\n'
    b'    var list = grouped[cat];\r\n'
    b'    if (!list || !list.length) return;\r\n'
    b'    var m = CATS[cat];\r\n'
    b'    html += \'<div class="mb-6">\';\r\n'
    b'    html += \'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">\';\r\n'
    b'    html += \'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:\'+ m.color +\';flex-shrink:0;"></span>\';\r\n'
    b'    html += \'<span class="font-semibold text-sm" style="color:\'+ m.color +\';">\' + m.label + \'</span>\';\r\n'
    b'    html += \'</div>\';\r\n'
    b'    html += \'<table style="width:100%;border-collapse:collapse;font-size:0.8rem;">\';\r\n'
    b'    html += \'<thead><tr style="border-bottom:1px solid #334155;">\';\r\n'
    b'    html += \'<th style="text-align:left;padding:4px 6px;color:#94a3b8;font-weight:500;white-space:nowrap;">K\\u00fcrzel</th>\';\r\n'
    b'    html += \'<th style="text-align:left;padding:4px 6px;color:#94a3b8;font-weight:500;">Name</th>\';\r\n'
    b'    html += \'<th style="text-align:left;padding:4px 6px;color:#94a3b8;font-weight:500;">Anmerkung</th>\';\r\n'
    b'    html += \'</tr></thead><tbody>\';\r\n'
    b'    list.forEach(function(v, i) {\r\n'
    b'      var bg = i % 2 === 0 ? \'rgba(30,41,59,0.5)\' : \'transparent\';\r\n'
    b'      html += \'<tr style="background:\'+ bg +\';border-bottom:1px solid #1e293b;">\';\r\n'
    b'      html += \'<td style="padding:5px 6px;white-space:nowrap;"><span style="font-family:monospace;font-size:0.73rem;background:#1e3a5f;color:#93c5fd;padding:2px 6px;border-radius:4px;">\' + v.kuerzel + \'</span></td>\';\r\n'
    b'      html += \'<td style="padding:5px 6px;">\' + v.name + \'</td>\';\r\n'
    b'      html += \'<td style="padding:5px 6px;color:#94a3b8;font-size:0.75rem;">\' + (v.anmerkung || \'\') + \'</td>\';\r\n'
    b'      html += \'</tr>\';\r\n'
    b'    });\r\n'
    b'    html += \'</tbody></table></div>\';\r\n'
    b'  });\r\n'
    b'  el.innerHTML = html;\r\n'
    b'  _zvbRendered = true;\r\n'
    b'}\r\n'
    b'\r\n'
    b'(function() {\r\n'
    b'  var _origSVT = _switchVTab;\r\n'
    b'  _switchVTab = function(name) {\r\n'
    b'    _origSVT(name);\r\n'
    b'    var zvbEl = document.getElementById(\'vtab-zvb\');\r\n'
    b'    if (zvbEl) {\r\n'
    b'      zvbEl.classList.toggle(\'hidden\', name !== \'zvb\');\r\n'
    b'      if (name === \'zvb\') _renderZvb();\r\n'
    b'    }\r\n'
    b'  };\r\n'
    b'})();\r\n'
    b'\r\n'
)


def run():
    content = open(INDEX, "rb").read()
    assert content.count(b"\r\n") > 1000, "CRLF erwartet"

    # 1. Button einfügen
    assert BTN_OLD in content, "BTN_OLD nicht gefunden"
    content = content.replace(BTN_OLD, BTN_NEW, 1)
    print("HTML: Zweckverbände-Button eingefügt")

    # 2. HTML Div einfügen
    assert HTML_OLD in content, "HTML_OLD nicht gefunden"
    content = content.replace(HTML_OLD, HTML_NEW, 1)
    print("HTML: vtab-zvb-Div eingefügt")

    # 3. JS + Monkey-Patches einfügen
    assert JS_ANCHOR in content, "JS_ANCHOR (setupTabs) nicht gefunden"
    content = content.replace(JS_ANCHOR, NEW_JS + JS_ANCHOR, 1)
    print("JS:   _renderZvb() + _switchVTab-Monkey-Patch eingefügt")

    # Validierung
    bt = content.count(b"\x60")
    assert bt == 132, f"Backtick-Parität verletzt: {bt}"
    print(f"OK: Backticks = {bt}")

    open(INDEX, "wb").write(content)
    size_kb = len(content) // 1024
    print(f"[OK] index.html ({size_kb} KB)")


if __name__ == "__main__":
    run()
