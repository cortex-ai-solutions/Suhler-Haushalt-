"""
patch_vermoegen_tab.py
Fuegt den Tab "Vermoegen & Beteiligungen" (8. Tab) in index.html ein.
Untergeordnete Tabs: "Stadt Suhl Bilanz" (2020/2021) und "EB KDS" (2022-2024).
Daten kommen aus DATA.bilanz und DATA.eb_kds in budget_data.json.
"""
import os, re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "index.html")

CRLF = "\r\n"


def apply_patch():
    raw = open(HTML_PATH, "rb").read()
    c = raw.decode("utf-8")
    orig_len = len(c)
    bt_before = c.count("\x60")

    # ── 1. Tab-Button im Tabbar einfügen (nach Simulator) ─────────────────
    OLD_TAB = ('  <div class="tab" data-tab="simulator">Konsolidierungs-Simulator</div>'
               + CRLF + "</div>")
    NEW_TAB = ('  <div class="tab" data-tab="simulator">Konsolidierungs-Simulator</div>'
               + CRLF
               + '  <div class="tab" data-tab="vermoegen">Verm&ouml;gen</div>'
               + CRLF + "</div>")
    assert OLD_TAB in c, "FEHLER: Tabbar-Anker nicht gefunden"
    c = c.replace(OLD_TAB, NEW_TAB, 1)

    # ── 2. Mobile-Nav-Item einfügen (nach Simulator) ──────────────────────
    OLD_MOB = ('    <div class="mobile-tab-item" data-tab="simulator">Konsolidierungs-Simulator</div>'
               + CRLF + "  </div>")
    NEW_MOB = ('    <div class="mobile-tab-item" data-tab="simulator">Konsolidierungs-Simulator</div>'
               + CRLF
               + '    <div class="mobile-tab-item" data-tab="vermoegen">Verm&ouml;gen &amp; Beteiligungen</div>'
               + CRLF + "  </div>")
    assert OLD_MOB in c, "FEHLER: Mobile-Nav-Anker nicht gefunden"
    c = c.replace(OLD_MOB, NEW_MOB, 1)

    # ── 3. Tab-Content vor dem Drilldown-Modal einfügen ───────────────────
    # ACHTUNG: Box-Drawing-Chars im HTML-Kommentar → Anker dynamisch extrahieren
    raw_c = open(HTML_PATH, "rb").read()  # re-read after first two replacements
    c_for_anchor = raw_c.decode("utf-8")
    anchor_idx = c_for_anchor.find('<div id="drilldown-overlay"')
    assert anchor_idx > 0, "FEHLER: drilldown-overlay nicht gefunden"
    # Gehe zurück bis zum nächsten \r\n vor dem div
    insert_pos = c.rfind("\r\n", 0, c.find('<div id="drilldown-overlay"')) + 2
    DRILL_ANCHOR = CRLF + '<div id="drilldown-overlay"'
    assert DRILL_ANCHOR in c, "FEHLER: Drilldown-Anker nicht gefunden"

    TAB_HTML = (
        CRLF
        + CRLF
        + "<!-- ══════════ TAB: VERMÖGEN & BETEILIGUNGEN ══════════ -->"
        + CRLF
        + '<div id="tab-vermoegen" class="hidden">'
        + CRLF
        + '  <div class="card p-5 mb-6">'
        + CRLF
        # ── Subtab-Leiste
        + "    <!-- Subtab-Leiste -->"
        + CRLF
        + '    <div style="display:flex;gap:0;margin-bottom:1.5rem;border-bottom:1px solid #334155;">'
        + CRLF
        + '      <button class="vermoegen-subtab" data-vtab="bilanz" onclick="_switchVTab(\'bilanz\')"'
        + CRLF
        + '              style="padding:0.5rem 1.25rem;background:transparent;border:none;'
        + CRLF
        + '                     color:#60a5fa;border-bottom:2px solid #60a5fa;font-weight:500;cursor:pointer;font-size:0.875rem;">'
        + CRLF
        + "        Stadt Suhl &ndash; Bilanz"
        + CRLF
        + "      </button>"
        + CRLF
        + '      <button class="vermoegen-subtab" data-vtab="ebkds" onclick="_switchVTab(\'ebkds\')"'
        + CRLF
        + '              style="padding:0.5rem 1.25rem;background:transparent;border:none;'
        + CRLF
        + '                     color:#94a3b8;border-bottom:2px solid transparent;cursor:pointer;font-size:0.875rem;">'
        + CRLF
        + "        EB KDS"
        + CRLF
        + "      </button>"
        + CRLF
        + "    </div>"
        + CRLF
        # ── Bilanz-Subtab
        + CRLF
        + '    <div id="vtab-bilanz">'
        + CRLF
        + '      <p class="text-slate-400 text-sm mb-5">'
        + CRLF
        + "        Gesamtverm&ouml;gen der Stadt Suhl nach kommunaler Doppik (Th&uuml;rGemHV-Doppik)."
        + CRLF
        + "        Stand: Jahresabschluss 31.12.2021 (letzter ver&ouml;ffentlichter Abschluss)."
        + CRLF
        + "      </p>"
        + CRLF
        + '      <div class="kpi-row mb-6">'
        + CRLF
        + '        <div class="kpi-card"><div class="kpi-label">Bilanzsumme 2021</div><div class="kpi-value" id="vm-bilanzsumme">-</div></div>'
        + CRLF
        + '        <div class="kpi-card"><div class="kpi-label">Eigenkapitalquote</div><div class="kpi-value" id="vm-ekquote">-</div></div>'
        + CRLF
        + '        <div class="kpi-card"><div class="kpi-label">Verbindlichkeiten 2021</div><div class="kpi-value" id="vm-vb">-</div></div>'
        + CRLF
        + '        <div class="kpi-card"><div class="kpi-label">Sonderposten 2021</div><div class="kpi-value" id="vm-sp">-</div></div>'
        + CRLF
        + '        <div class="kpi-card"><div class="kpi-label">Jahresergebnis 2021</div><div class="kpi-value" id="vm-je">-</div></div>'
        + CRLF
        + "      </div>"
        + CRLF
        + '      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">'
        + CRLF
        + '        <div class="card p-5">'
        + CRLF
        + '          <div class="section-title">Verm&ouml;gensstruktur (Aktiva) in Mio.&nbsp;&#8364;</div>'
        + CRLF
        + '          <div id="chart-bilanz-aktiva" style="height:240px"></div>'
        + CRLF
        + "        </div>"
        + CRLF
        + '        <div class="card p-5">'
        + CRLF
        + '          <div class="section-title">Finanzierungsstruktur (Passiva) in Mio.&nbsp;&#8364;</div>'
        + CRLF
        + '          <div id="chart-bilanz-passiva" style="height:240px"></div>'
        + CRLF
        + "        </div>"
        + CRLF
        + "      </div>"
        + CRLF
        + '      <div class="card p-5">'
        + CRLF
        + '        <div class="section-title">Hinweise zur kommunalen Bilanz</div>'
        + CRLF
        + '        <p class="text-slate-400 text-sm mt-2">'
        + CRLF
        + '          <strong class="text-slate-300">Sonderposten</strong> spiegeln erhaltene F&ouml;rdermittel wider'
        + CRLF
        + "          und werden parallel zur Abschreibung des gef&ouml;rderten Anlageverm&ouml;gens aufgel&ouml;st"
        + CRLF
        + "          (2021: 89,9&nbsp;Mio.&nbsp;&#8364;, davon 79,1 aus Zuwendungen).&nbsp;"
        + CRLF
        + '          <strong class="text-slate-300">Liquidit&auml;tskredite:</strong> 0&nbsp;&#8364; &ndash;'
        + CRLF
        + "          die Stadt finanziert ausschlie&szlig;lich &uuml;ber Investitionskredite (9,9&nbsp;Mio.&nbsp;&#8364;).&nbsp;"
        + CRLF
        + '          <strong class="text-slate-300">Quelle:</strong> Jahresabschluss der Stadt Suhl, 31.12.2021.'
        + CRLF
        + "        </p>"
        + CRLF
        + "      </div>"
        + CRLF
        + "    </div>"
        + CRLF
        # ── EB KDS Subtab
        + CRLF
        + '    <div id="vtab-ebkds" class="hidden">'
        + CRLF
        + '      <p class="text-slate-400 text-sm mb-5">'
        + CRLF
        + "        Eigenbetrieb Kommunalwirtschaftliche Dienstleistungen Suhl (EB&nbsp;KDS) &ndash;"
        + CRLF
        + "        100&nbsp;% Eigentum der Stadt, zust&auml;ndig f&uuml;r Stra&szlig;en, Gr&uuml;nfl&auml;chen,"
        + CRLF
        + "        Abfallwirtschaft und Friedhofsverwaltung."
        + CRLF
        + "        Stand: Beteiligungsbericht GJ 2024."
        + CRLF
        + "      </p>"
        + CRLF
        + '      <div class="kpi-row mb-6">'
        + CRLF
        + '        <div class="kpi-card"><div class="kpi-label">Bilanzsumme 2024</div><div class="kpi-value" id="kds-bilanzsumme">-</div></div>'
        + CRLF
        + '        <div class="kpi-card"><div class="kpi-label">Eigenkapital 2024</div><div class="kpi-value" id="kds-ek">-</div></div>'
        + CRLF
        + '        <div class="kpi-card"><div class="kpi-label">Jahresverlust 2024</div><div class="kpi-value text-red-400" id="kds-je">-</div></div>'
        + CRLF
        + '        <div class="kpi-card"><div class="kpi-label">Mitarbeiter 2024</div><div class="kpi-value" id="kds-ma">-</div></div>'
        + CRLF
        + '        <div class="kpi-card"><div class="kpi-label">Zuschuss Stadt 2024</div><div class="kpi-value" id="kds-zuschuss">-</div></div>'
        + CRLF
        + "      </div>"
        + CRLF
        + '      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">'
        + CRLF
        + '        <div class="card p-5">'
        + CRLF
        + '          <div class="section-title">Bilanzsumme &amp; Eigenkapital (T&#8364;)</div>'
        + CRLF
        + '          <div id="chart-ebkds-bilanz" style="height:240px"></div>'
        + CRLF
        + "        </div>"
        + CRLF
        + '        <div class="card p-5">'
        + CRLF
        + '          <div class="section-title">Ertragsrechnung (T&#8364;)</div>'
        + CRLF
        + '          <div id="chart-ebkds-guv" style="height:240px"></div>'
        + CRLF
        + "        </div>"
        + CRLF
        + "      </div>"
        + CRLF
        + '      <div class="card p-5 mb-6">'
        + CRLF
        + '        <div class="section-title">Eigenkapitalquote 2021&ndash;2024 (%)</div>'
        + CRLF
        + '        <div id="chart-ebkds-ekquote" style="height:160px"></div>'
        + CRLF
        + "      </div>"
        + CRLF
        + '      <div class="card p-5">'
        + CRLF
        + '        <div class="section-title">Zum Eigenbetrieb KDS</div>'
        + CRLF
        + '        <p class="text-slate-400 text-sm mt-2">'
        + CRLF
        + "          Gegr&uuml;ndet 01.01.2012 &bull; Stammkapital 25.000&nbsp;&#8364; (100&nbsp;% Stadt Suhl)."
        + CRLF
        + "          Der j&auml;hrliche Zuschuss der Stadt betr&auml;gt ca.&nbsp;11,5&nbsp;Mio.&nbsp;&#8364; (2024)"
        + CRLF
        + "          f&uuml;r Leistungen, die als Daseinsvorsorge &uuml;ber Geb&uuml;hren nicht vollst&auml;ndig finanzierbar sind."
        + CRLF
        + "          Der wachsende Instandsetzungsstau &ouml;ffentlicher Stra&szlig;en und Wege (2025: Budget -219&nbsp;T&#8364;"
        + CRLF
        + "          gg&uuml;. Vorjahr) gef&auml;hrdet langfristig die bauliche Substanz der Suhler Infrastruktur."
        + CRLF
        + "        </p>"
        + CRLF
        + "      </div>"
        + CRLF
        + "    </div>"
        + CRLF
        + "  </div>"
        + CRLF
        + "</div>"
    )

    c = c.replace(DRILL_ANCHOR, TAB_HTML + DRILL_ANCHOR, 1)

    # ── 4. TABS-Array erweitern ────────────────────────────────────────────
    OLD_TABS = 'const TABS = ["overview", "details", "personal", "jahresvergleich", "zeitreihe", "hsk", "simulator"];'
    NEW_TABS = 'const TABS = ["overview", "details", "personal", "jahresvergleich", "zeitreihe", "hsk", "simulator", "vermoegen"];'
    assert OLD_TABS in c, "FEHLER: TABS-Array-Anker nicht gefunden"
    c = c.replace(OLD_TABS, NEW_TABS, 1)

    # ── 5. renderVermoegen-Aufruf im Tab-Click-Handler ────────────────────
    OLD_RENDER = 'if (name === "hsk") renderHsk();'
    NEW_RENDER = ('if (name === "hsk") renderHsk();'
                  + CRLF
                  + '      if (name === "vermoegen") renderVermoegen();')
    assert OLD_RENDER in c, "FEHLER: Render-Handler-Anker nicht gefunden"
    c = c.replace(OLD_RENDER, NEW_RENDER, 1)

    # ── 6. JS-Funktionen vor setupTabs einfügen ───────────────────────────
    OLD_SETUP = "function setupTabs() {"
    JS_BLOCK = (
        "var _vmRendered = false;"
        + CRLF
        + CRLF
        + "function renderVermoegen() {"
        + CRLF
        + "  if (!DATA.bilanz) return;"
        + CRLF
        + "  if (_vmRendered) return;"
        + CRLF
        + "  _vmRendered = true;"
        + CRLF
        + "  var BY = DATA.bilanz.by_year;"
        + CRLF
        + "  var yr21 = BY['2021'] || {};"
        + CRLF
        + "  var yr20 = BY['2020'] || {};"
        + CRLF
        + CRLF
        + "  function gb(list, code) {"
        + CRLF
        + "    if (!list) return 0;"
        + CRLF
        + "    for (var i = 0; i < list.length; i++) { if (list[i].code === code) return list[i].betrag; }"
        + CRLF
        + "    return 0;"
        + CRLF
        + "  }"
        + CRLF
        + CRLF
        + "  var a21 = yr21.aktiva || [];"
        + CRLF
        + "  var p21 = yr21.passiva || [];"
        + CRLF
        + "  var a20 = yr20.aktiva || [];"
        + CRLF
        + "  var p20 = yr20.passiva || [];"
        + CRLF
        + CRLF
        + "  var bilanzsumme = gb(a21, 'A1') + gb(a21, 'A2') + gb(a21, 'A3');"
        + CRLF
        + "  var ek  = gb(p21, 'P1');"
        + CRLF
        + "  var sp  = gb(p21, 'P2');"
        + CRLF
        + "  var vb  = gb(p21, 'P4');"
        + CRLF
        + "  var je  = gb(p21, 'P1.3');"
        + CRLF
        + "  var ekq = bilanzsumme > 0 ? (ek / bilanzsumme * 100) : 0;"
        + CRLF
        + CRLF
        + "  setText('vm-bilanzsumme', fmtMio(bilanzsumme));"
        + CRLF
        + "  setText('vm-ekquote',     fmt(ekq, 1) + ' %');"
        + CRLF
        + "  setText('vm-vb',          fmtMio(vb));"
        + CRLF
        + "  setText('vm-sp',          fmtMio(sp));"
        + CRLF
        + "  var jeEl = document.getElementById('vm-je');"
        + CRLF
        + "  if (jeEl) { jeEl.textContent = fmtMio(Math.abs(je)) + (je < 0 ? ' (Verlust)' : ' (Gewinn)'); jeEl.className = 'kpi-value ' + (je < 0 ? 'text-red-400' : 'text-emerald-400'); }"
        + CRLF
        + CRLF
        # Aktiva-Chart
        + "  var aktLabels = ['Anlagevermögen', 'Umlaufvermögen', 'RAP Aktiva'];"
        + CRLF
        + "  var aktCodes  = ['A1', 'A2', 'A3'];"
        + CRLF
        + "  var aktV20 = aktCodes.map(function(c) { return Math.round(gb(a20, c) / 1e4) / 100; });"
        + CRLF
        + "  var aktV21 = aktCodes.map(function(c) { return Math.round(gb(a21, c) / 1e4) / 100; });"
        + CRLF
        + "  Plotly.newPlot('chart-bilanz-aktiva', ["
        + CRLF
        + "    { name: '2020', y: aktLabels, x: aktV20, type: 'bar', orientation: 'h', marker: { color: '#475569' },"
        + CRLF
        + "      text: aktV20.map(function(v){ return v.toFixed(1) + ' Mio.'; }), textposition: 'auto' },"
        + CRLF
        + "    { name: '2021', y: aktLabels, x: aktV21, type: 'bar', orientation: 'h', marker: { color: '#3b82f6' },"
        + CRLF
        + "      text: aktV21.map(function(v){ return v.toFixed(1) + ' Mio.'; }), textposition: 'auto' },"
        + CRLF
        + "  ], Object.assign({}, DARK_LAYOUT, {"
        + CRLF
        + "    barmode: 'group',"
        + CRLF
        + "    margin: { l: 130, r: 20, t: 10, b: 40 },"
        + CRLF
        + "    xaxis: { gridcolor: '#334155' },"
        + CRLF
        + "    yaxis: { gridcolor: '#334155' },"
        + CRLF
        + "    legend: { orientation: 'h', y: 1.1 },"
        + CRLF
        + "  }), CFG);"
        + CRLF
        + CRLF
        # Passiva-Chart
        + "  var pasLabels = ['Eigenkapital', 'Sonderposten', 'Rückstellungen', 'Verbindlichkeiten'];"
        + CRLF
        + "  var pasCodes  = ['P1', 'P2', 'P3', 'P4'];"
        + CRLF
        + "  var pasV20 = pasCodes.map(function(c) { return Math.round(gb(p20, c) / 1e4) / 100; });"
        + CRLF
        + "  var pasV21 = pasCodes.map(function(c) { return Math.round(gb(p21, c) / 1e4) / 100; });"
        + CRLF
        + "  Plotly.newPlot('chart-bilanz-passiva', ["
        + CRLF
        + "    { name: '2020', y: pasLabels, x: pasV20, type: 'bar', orientation: 'h', marker: { color: '#475569' },"
        + CRLF
        + "      text: pasV20.map(function(v){ return v.toFixed(1) + ' Mio.'; }), textposition: 'auto' },"
        + CRLF
        + "    { name: '2021', y: pasLabels, x: pasV21, type: 'bar', orientation: 'h', marker: { color: '#a78bfa' },"
        + CRLF
        + "      text: pasV21.map(function(v){ return v.toFixed(1) + ' Mio.'; }), textposition: 'auto' },"
        + CRLF
        + "  ], Object.assign({}, DARK_LAYOUT, {"
        + CRLF
        + "    barmode: 'group',"
        + CRLF
        + "    margin: { l: 130, r: 20, t: 10, b: 40 },"
        + CRLF
        + "    xaxis: { gridcolor: '#334155' },"
        + CRLF
        + "    yaxis: { gridcolor: '#334155' },"
        + CRLF
        + "    legend: { orientation: 'h', y: 1.1 },"
        + CRLF
        + "  }), CFG);"
        + CRLF
        + CRLF
        # EB KDS
        + "  if (DATA.eb_kds) _renderEbKds(DATA.eb_kds);"
        + CRLF
        + "}"
        + CRLF
        + CRLF
        + "function _renderEbKds(EK) {"
        + CRLF
        + "  var jahre = ['2022', '2023', '2024'];"
        + CRLF
        + "  function gk(yr, bereich, pos) {"
        + CRLF
        + "    return ((EK[yr] || {})[bereich] || {})[pos] || 0;"
        + CRLF
        + "  }"
        + CRLF
        + CRLF
        + "  setText('kds-bilanzsumme', fmt(gk('2024','KENNZAHLEN','vermogen_gesamt'), 0) + ' T€');"
        + CRLF
        + "  setText('kds-ek',          fmt(gk('2024','BILANZ_PASSIVA','eigenkapital'), 0) + ' T€');"
        + CRLF
        + "  setText('kds-je',          fmt(Math.abs(gk('2024','KENNZAHLEN','jahresergebnis')), 0) + ' T€');"
        + CRLF
        + "  setText('kds-ma',          fmt(gk('2024','KENNZAHLEN','mitarbeiter'), 0));"
        + CRLF
        + "  setText('kds-zuschuss',    fmt(gk('2024','KENNZAHLEN','zuschuss_stadt'), 0) + ' T€');"
        + CRLF
        + CRLF
        # Bilanz-Chart
        + "  var bVerm = jahre.map(function(y){ return gk(y,'KENNZAHLEN','vermogen_gesamt'); });"
        + CRLF
        + "  var bEK   = jahre.map(function(y){ return gk(y,'BILANZ_PASSIVA','eigenkapital'); });"
        + CRLF
        + "  var bVB   = jahre.map(function(y){ return gk(y,'BILANZ_PASSIVA','verbindlichkeiten'); });"
        + CRLF
        + "  Plotly.newPlot('chart-ebkds-bilanz', ["
        + CRLF
        + "    { name: 'Bilanzsumme',   x: jahre, y: bVerm, type: 'bar', marker: { color: '#3b82f6' } },"
        + CRLF
        + "    { name: 'Eigenkapital',  x: jahre, y: bEK,   type: 'bar', marker: { color: '#10b981' } },"
        + CRLF
        + "    { name: 'Verbindlichk.', x: jahre, y: bVB,   type: 'bar', marker: { color: '#ef4444' } },"
        + CRLF
        + "  ], Object.assign({}, DARK_LAYOUT, {"
        + CRLF
        + "    barmode: 'group',"
        + CRLF
        + "    margin: { l: 50, r: 10, t: 10, b: 40 },"
        + CRLF
        + "    yaxis: { title: 'T€', gridcolor: '#334155' },"
        + CRLF
        + "    xaxis: { gridcolor: '#334155' },"
        + CRLF
        + "    legend: { orientation: 'h', y: 1.1 },"
        + CRLF
        + "  }), CFG);"
        + CRLF
        + CRLF
        # GuV-Chart
        + "  var gUmsatz = jahre.map(function(y){ return gk(y,'GUV','umsatzerloese'); });"
        + CRLF
        + "  var gMat    = jahre.map(function(y){ return Math.abs(gk(y,'GUV','materialaufwand')); });"
        + CRLF
        + "  var gPers   = jahre.map(function(y){ return Math.abs(gk(y,'GUV','personalaufwand')); });"
        + CRLF
        + "  Plotly.newPlot('chart-ebkds-guv', ["
        + CRLF
        + "    { name: 'Umsatzerlöse',    x: jahre, y: gUmsatz, type: 'bar', marker: { color: '#3b82f6' } },"
        + CRLF
        + "    { name: 'Materialaufwand', x: jahre, y: gMat,    type: 'bar', marker: { color: '#f59e0b' } },"
        + CRLF
        + "    { name: 'Personalaufwand', x: jahre, y: gPers,   type: 'bar', marker: { color: '#8b5cf6' } },"
        + CRLF
        + "  ], Object.assign({}, DARK_LAYOUT, {"
        + CRLF
        + "    barmode: 'group',"
        + CRLF
        + "    margin: { l: 50, r: 10, t: 10, b: 40 },"
        + CRLF
        + "    yaxis: { title: 'T€', gridcolor: '#334155' },"
        + CRLF
        + "    xaxis: { gridcolor: '#334155' },"
        + CRLF
        + "    legend: { orientation: 'h', y: 1.1 },"
        + CRLF
        + "  }), CFG);"
        + CRLF
        + CRLF
        # EK-Quote-Chart
        + "  var alleJahre = ['2021', '2022', '2023', '2024'];"
        + CRLF
        + "  var ekq = alleJahre.map(function(y){ return gk(y,'KENNZAHLEN','ek_quote_pct') || null; });"
        + CRLF
        + "  Plotly.newPlot('chart-ebkds-ekquote', ["
        + CRLF
        + "    { x: alleJahre, y: ekq, type: 'scatter', mode: 'lines+markers',"
        + CRLF
        + "      line: { color: '#10b981', width: 2 }, marker: { color: '#10b981', size: 8 },"
        + CRLF
        + "      name: 'EK-Quote %' },"
        + CRLF
        + "  ], Object.assign({}, DARK_LAYOUT, {"
        + CRLF
        + "    margin: { l: 50, r: 10, t: 10, b: 40 },"
        + CRLF
        + "    yaxis: { title: '%', gridcolor: '#334155', rangemode: 'tozero' },"
        + CRLF
        + "    xaxis: { gridcolor: '#334155' },"
        + CRLF
        + "  }), CFG);"
        + CRLF
        + "}"
        + CRLF
        + CRLF
        + "function _switchVTab(name) {"
        + CRLF
        + "  document.querySelectorAll('.vermoegen-subtab').forEach(function(b) {"
        + CRLF
        + "    var active = b.getAttribute('data-vtab') === name;"
        + CRLF
        + "    b.style.color = active ? '#60a5fa' : '#94a3b8';"
        + CRLF
        + "    b.style.borderBottom = active ? '2px solid #60a5fa' : '2px solid transparent';"
        + CRLF
        + "  });"
        + CRLF
        + "  var bil = document.getElementById('vtab-bilanz');"
        + CRLF
        + "  var kds = document.getElementById('vtab-ebkds');"
        + CRLF
        + "  if (bil) bil.classList.toggle('hidden', name !== 'bilanz');"
        + CRLF
        + "  if (kds) kds.classList.toggle('hidden', name !== 'ebkds');"
        + CRLF
        + "}"
        + CRLF
        + CRLF
    )

    assert OLD_SETUP in c, "FEHLER: setupTabs-Anker nicht gefunden"
    c = c.replace(OLD_SETUP, JS_BLOCK + OLD_SETUP, 1)

    # ── Prüfungen ──────────────────────────────────────────────────────────
    bt_after = c.count("\x60")
    assert bt_after % 2 == 0, f"Backtick-Paritätsfehler: {bt_after}"
    assert bt_after == bt_before, f"Backtick-Anzahl geändert: {bt_before} -> {bt_after}"
    assert "vermoegen" in c, "vermoegen-Tab nicht gefunden"
    assert "vtab-bilanz" in c, "vtab-bilanz nicht gefunden"
    assert "chart-ebkds-bilanz" in c, "chart-ebkds-bilanz nicht gefunden"

    open(HTML_PATH, "wb").write(c.encode("utf-8"))
    print(f"[OK] patch_vermoegen_tab.py angewendet")
    print(f"     HTML-Laenge: {orig_len:,} -> {len(c):,} (+{len(c)-orig_len:,} Zeichen)")
    print(f"     Backticks:   {bt_before} (unveraendert)")


if __name__ == "__main__":
    apply_patch()
