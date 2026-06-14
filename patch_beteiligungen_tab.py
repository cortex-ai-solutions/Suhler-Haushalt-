#!/usr/bin/env python3
"""
patch_beteiligungen_tab.py
Fügt einen dritten Subtab "Beteiligungen" in den Vermögen-Tab ein.
Enthält: KPI-Chips, Plotly-Sankey (Finanzströme 2024), Unternehmenstabelle, JÜ-Chart.
"""
import os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(BASE, "index.html")

content = open(HTML, "rb").read()
orig = content  # für Rollback

# ---------------------------------------------------------------------------
# Sicherheitsprüfungen
# ---------------------------------------------------------------------------
assert content.count(b"vtab-beteiligungen") == 0, "Patch bereits angewendet!"
bt = content.count(b"\x60")
assert bt % 2 == 0, f"Ungerade Backtick-Anzahl vor Patch: {bt}"
print(f"Backticks vor Patch: {bt}")
print(f"CRLF-Zeilen: {content.count(b'\r\n')}")

# ---------------------------------------------------------------------------
# 1. Subtab-Button einfügen (nach EB KDS Button)
# ---------------------------------------------------------------------------
BTN_ANCHOR = (
    b"        EB KDS\r\n"
    b"      </button>\r\n"
    b"    </div>"
)
assert content.count(BTN_ANCHOR) == 1, f"BTN_ANCHOR {content.count(BTN_ANCHOR)}x gefunden"

BTN_NEW = (
    b"        EB KDS\r\n"
    b"      </button>\r\n"
    b"      <button class=\"vermoegen-subtab\" data-vtab=\"beteiligungen\" "
    b"onclick=\"_switchVTab('beteiligungen')\"\r\n"
    b"              style=\"padding:0.5rem 1.25rem;background:transparent;border:none;\r\n"
    b"                     color:#94a3b8;border-bottom:2px solid transparent;"
    b"cursor:pointer;font-size:0.875rem;\">\r\n"
    b"        Beteiligungen\r\n"
    b"      </button>\r\n"
    b"    </div>"
)
content = content.replace(BTN_ANCHOR, BTN_NEW, 1)
assert b"data-vtab=\"beteiligungen\"" in content, "Button nicht eingefügt"

# ---------------------------------------------------------------------------
# 2. Subtab-Inhalt einfügen (nach vtab-ebkds, vor schliessenden Vermoegen-Divs)
# ---------------------------------------------------------------------------
# Eindeutiger Anker: Ende des EB KDS Subtabs → Suhler Infrastruktur-Text
CONTENT_ANCHOR = (
    b"bauliche Substanz der Suhler Infrastruktur.\r\n"
    b"        </p>\r\n"
    b"      </div>\r\n"
    b"    </div>\r\n"
    b"  </div>\r\n"
    b"</div>\r\n"
    b"<div id=\"drilldown-overlay\""
)
assert content.count(CONTENT_ANCHOR) == 1, "CONTENT_ANCHOR nicht eindeutig"

NEW_VTAB = (
    b"bauliche Substanz der Suhler Infrastruktur.\r\n"
    b"        </p>\r\n"
    b"      </div>\r\n"
    b"    </div><!-- /vtab-ebkds -->\r\n"
    b"\r\n"
    b"    <!-- ======= SUBTAB BETEILIGUNGEN ======= -->\r\n"
    b"    <div id=\"vtab-beteiligungen\" class=\"hidden\">\r\n"
    b"      <p class=\"text-slate-400 text-sm mb-5\">\r\n"
    b"        Die Stadt Suhl h&auml;lt direkte und mittelbare Beteiligungen an\r\n"
    b"        14&nbsp;Gesellschaften sowie einem Eigenbetrieb (EB&nbsp;KDS).\r\n"
    b"        Kernbotschaft: Stadtwerke-Gewinne (Energie) quersubventionieren\r\n"
    b"        den defizit&auml;ren &Ouml;PNV &uuml;ber die CCS-Holding.\r\n"
    b"        Quelle: Beteiligungsbericht GJ 2024.\r\n"
    b"      </p>\r\n"
    b"      <div class=\"kpi-row mb-6\">\r\n"
    b"        <div class=\"kpi-card\"><div class=\"kpi-label\">Beteiligungen gesamt</div>"
    b"<div class=\"kpi-value\" id=\"bet-kpi-n\">15</div></div>\r\n"
    b"        <div class=\"kpi-card\"><div class=\"kpi-label\">SWSZ-Umsatz 2024</div>"
    b"<div class=\"kpi-value\" id=\"bet-kpi-swsz\">-</div></div>\r\n"
    b"        <div class=\"kpi-card\"><div class=\"kpi-label\">EAV-Kette an CCS 2024</div>"
    b"<div class=\"kpi-value\" id=\"bet-kpi-eav\">-</div></div>\r\n"
    b"        <div class=\"kpi-card\"><div class=\"kpi-label\">SNG-Defizit 2024</div>"
    b"<div class=\"kpi-value text-red-400\" id=\"bet-kpi-sng\">-</div></div>\r\n"
    b"        <div class=\"kpi-card\"><div class=\"kpi-label\">Dividenden an Stadt</div>"
    b"<div class=\"kpi-value text-green-400\" id=\"bet-kpi-div\">-</div></div>\r\n"
    b"      </div>\r\n"
    b"      <div class=\"card p-5 mb-6\">\r\n"
    b"        <div class=\"section-title\">Finanzstr&ouml;me 2024 (T&#8364;) &ndash; Energie&shy;quersubvention</div>\r\n"
    b"        <p class=\"text-slate-400 text-xs mb-3\">\r\n"
    b"          Stadtwerke-Gewinne (SWSZ-Netz &#8594; SWSZ &#8594; SWB &#8594; CCS) finanzieren\r\n"
    b"          den j&auml;hrlichen &Ouml;PNV-Verlust der SNG. Zus&auml;tzlich Zusch&uuml;sse von\r\n"
    b"          Freistaat und Bund. Stadt Suhl finanziert direkt EB&nbsp;KDS und SSZ.\r\n"
    b"        </p>\r\n"
    b"        <div id=\"chart-bet-sankey\" style=\"height:460px\"></div>\r\n"
    b"      </div>\r\n"
    b"      <div class=\"card p-5 mb-6\">\r\n"
    b"        <div class=\"section-title\">Unternehmen im &Uuml;berblick (GJ 2024)</div>\r\n"
    b"        <p class=\"text-slate-400 text-xs mb-3\">\r\n"
    b"          Jahresergebnis vor EAV. * = Jahresergebnis nach EAV = 0 (Gewinn abgef&uuml;hrt).\r\n"
    b"        </p>\r\n"
    b"        <div id=\"bet-table\" class=\"overflow-x-auto\"></div>\r\n"
    b"      </div>\r\n"
    b"      <div class=\"card p-5 mb-6\">\r\n"
    b"        <div class=\"section-title\">Jahresergebnisse vor EAV (T&#8364;, 2021&ndash;2024)</div>\r\n"
    b"        <div id=\"chart-bet-je\" style=\"height:300px\"></div>\r\n"
    b"      </div>\r\n"
    b"    </div><!-- /vtab-beteiligungen -->\r\n"
    b"\r\n"
    b"  </div>\r\n"
    b"</div>\r\n"
    b"<div id=\"drilldown-overlay\""
)
content = content.replace(CONTENT_ANCHOR, NEW_VTAB, 1)
assert content.count(b"vtab-beteiligungen") == 2  # div id + closing comment

# ---------------------------------------------------------------------------
# 3. _switchVTab erweitern (monkey-patch: neues vtab-beteiligungen)
# ---------------------------------------------------------------------------
VTAB_ANCHOR = (
    b"  if (bil) bil.classList.toggle('hidden', name !== 'bilanz');\r\n"
    b"  if (kds) kds.classList.toggle('hidden', name !== 'ebkds');\r\n"
    b"}"
)
assert content.count(VTAB_ANCHOR) == 1, "VTAB_ANCHOR nicht eindeutig"

VTAB_NEW = (
    b"  if (bil) bil.classList.toggle('hidden', name !== 'bilanz');\r\n"
    b"  if (kds) kds.classList.toggle('hidden', name !== 'ebkds');\r\n"
    b"  var bet = document.getElementById('vtab-beteiligungen');\r\n"
    b"  if (bet) {\r\n"
    b"    bet.classList.toggle('hidden', name !== 'beteiligungen');\r\n"
    b"    if (name === 'beteiligungen') _initBeteiligungen();\r\n"
    b"  }\r\n"
    b"}"
)
content = content.replace(VTAB_ANCHOR, VTAB_NEW, 1)

# ---------------------------------------------------------------------------
# 4. JS-Funktion _initBeteiligungen() nach setupTabs einfügen
# ---------------------------------------------------------------------------
JS_ANCHOR = b"function setupTabs() {"
assert content.count(JS_ANCHOR) == 1, "JS_ANCHOR nicht eindeutig"

BET_JS = r"""function _initBeteiligungen() {
  if (window._betInit) return;
  window._betInit = true;
  var D = (DATA && DATA.beteiligungen) ? DATA.beteiligungen : null;
  if (!D) { console.warn('beteiligungen fehlt in DATA'); return; }

  // ── KPI Chips ──────────────────────────────────────────────────────────
  var kn = D.kennzahlen || {};
  var sw = (kn['SWSZ'] && kn['SWSZ']['2024']) ? kn['SWSZ']['2024'] : {};
  var sg = (kn['SNG']  && kn['SNG']['2024'])  ? kn['SNG']['2024']  : {};
  function tEur(v) {
    if (v === null || v === undefined) return '-';
    return (v >= 0 ? '' : '-') + Math.abs(Math.round(v)).toLocaleString('de-DE') + ' T€';
  }
  var el = document.getElementById('bet-kpi-swsz');
  if (el) el.textContent = tEur(sw.umsatz);
  el = document.getElementById('bet-kpi-sng');
  if (el) el.textContent = tEur(sg.je);

  var stroeme2024 = (D.stroeme && D.stroeme['2024']) ? D.stroeme['2024'] : [];
  var eavSum = 0, divSum = 0;
  stroeme2024.forEach(function(s) {
    if (s.typ === 'EAV_GEWINN' && s.nach === 'CCS' && s.betrag) eavSum += s.betrag;
    if (s.typ === 'AUSSCHUETTUNG' && s.nach === 'STADT' && s.betrag) divSum += s.betrag;
  });
  el = document.getElementById('bet-kpi-eav');
  if (el) el.textContent = tEur(eavSum);
  el = document.getElementById('bet-kpi-div');
  if (el) el.textContent = '+' + tEur(divSum);

  // ── Sankey 2024 ────────────────────────────────────────────────────────
  var NODE_LABELS = {
    'SWSZ_NETZ': 'SW Netz GmbH',
    'SWSZ':      'Stadtwerke GmbH',
    'SWB':       'SW Beteiligungs-GmbH',
    'CCS':       'CCS Holding',
    'SNG':       'Nahverkehr SNG',
    'THUERINGEN':'Freistaat Thüringen',
    'BUND':      'Bundesrepublik',
    'STADT':     'Stadt Suhl',
    'EBKDS':     'EB KDS',
    'SSZ':       'Schießsportzentrum',
    'ITM':       'Transfusionsmedizin',
    'GEWO':      'GeWo Wohnen',
    'LSIM_EXTERN': 'Zella-Mehlis (LSIM)'
  };
  var NODE_ORDER = ['SWSZ_NETZ','SWSZ','SWB','CCS','SNG','THUERINGEN','BUND',
                    'STADT','EBKDS','SSZ','ITM','GEWO','LSIM_EXTERN'];
  var nodeIdx = {};
  NODE_ORDER.forEach(function(k, i) { nodeIdx[k] = i; });
  var labels = NODE_ORDER.map(function(k) { return NODE_LABELS[k] || k; });

  var FLOW_COLORS = {
    'EAV_GEWINN':         'rgba(234,179,8,0.55)',
    'VERLUSTUEBERNAHME':  'rgba(239,68,68,0.5)',
    'BEIHILFE':           'rgba(99,102,241,0.5)',
    'ZUSCHUSS':           'rgba(239,68,68,0.4)',
    'AUSSCHUETTUNG':      'rgba(34,197,94,0.5)',
    'AUSGLEICH_MINDERHEIT': 'rgba(148,163,184,0.45)'
  };
  var NODE_COLORS = labels.map(function(l, i) {
    var k = NODE_ORDER[i];
    if (k === 'SWSZ_NETZ' || k === 'SWSZ' || k === 'SWB') return '#1d4ed8';
    if (k === 'CCS') return '#7c3aed';
    if (k === 'SNG') return '#dc2626';
    if (k === 'THUERINGEN' || k === 'BUND') return '#4338ca';
    if (k === 'STADT') return '#0f766e';
    if (k === 'ITM' || k === 'GEWO') return '#059669';
    return '#64748b';
  });

  var srcs = [], tgts = [], vals = [], colors = [], hovs = [];
  stroeme2024.forEach(function(s) {
    var si = nodeIdx[s.von], ti = nodeIdx[s.nach];
    if (si === undefined || ti === undefined || !s.betrag || s.betrag <= 0) return;
    srcs.push(si); tgts.push(ti); vals.push(s.betrag);
    colors.push(FLOW_COLORS[s.typ] || 'rgba(148,163,184,0.4)');
    hovs.push((s.bez || s.typ) + '<br>' + Math.round(s.betrag).toLocaleString('de-DE') + ' T€');
  });

  if (document.getElementById('chart-bet-sankey') && srcs.length) {
    Plotly.newPlot('chart-bet-sankey', [{
      type: 'sankey',
      orientation: 'h',
      arrangement: 'snap',
      node: {
        pad: 18, thickness: 22,
        label: labels,
        color: NODE_COLORS,
        hovertemplate: '%{label}<extra></extra>'
      },
      link: {
        source: srcs, target: tgts, value: vals,
        color: colors,
        customdata: hovs,
        hovertemplate: '%{customdata}<extra></extra>'
      }
    }], {
      paper_bgcolor: '#1e293b', plot_bgcolor: '#1e293b',
      font: { color: '#e2e8f0', size: 11 },
      margin: { l: 10, r: 10, t: 10, b: 10 }
    }, { responsive: true, displayModeBar: false });
  }

  // ── Unternehmenstabelle ─────────────────────────────────────────────────
  var EL = document.getElementById('bet-table');
  if (EL && D.entities) {
    var SEKTOR_FARBE = {
      'ENERGIE': '#1d4ed8', 'HOLDING': '#7c3aed', 'NAHVERKEHR': '#dc2626',
      'WOHNEN': '#0369a1', 'GESUNDHEIT': '#059669', 'SOZIAL': '#0d9488',
      'SPORT': '#b45309', 'IT': '#6b21a8', 'ENTSORGUNG': '#78716c',
      'INFRASTRUKTUR': '#64748b', 'SONSTIGES': '#475569', 'KOMMUNE': '#0f766e'
    };
    var rows = '';
    D.entities.forEach(function(e) {
      if (e.kuerzel === 'STADT') return;
      var k = D.kennzahlen[e.kuerzel] ? D.kennzahlen[e.kuerzel]['2024'] : null;
      var umsatz = k && k.umsatz != null ? Math.round(k.umsatz).toLocaleString('de-DE') : '-';
      var je     = k && k.je != null ? Math.round(k.je) : null;
      var jeStr  = je != null ? (je >= 0 ? '+' : '') + je.toLocaleString('de-DE') : '-';
      var jeClass = je != null ? (je >= 0 ? 'color:#4ade80' : 'color:#f87171') : '';
      var ek     = k && k.ek_quote != null ? k.ek_quote.toFixed(1) + ' %' : '-';
      var ma     = k && k.mitarbeiter != null ? k.mitarbeiter : '-';
      var farbe  = SEKTOR_FARBE[e.sektor] || '#64748b';
      var status = e.status === 'liquidation' ? ' (i.L.)' : e.status === 'fiskalisiert' ? '*' : '';
      var via    = e.via && e.via !== 'STADT' ? 'via ' + e.via : 'direkt';
      rows += '<tr style="border-bottom:1px solid #334155">'
        + '<td style="padding:6px 8px;font-weight:600;white-space:nowrap">'
        +   '<span style="background:' + farbe + '22;color:' + farbe + ';'
        +   'padding:1px 6px;border-radius:4px;font-size:0.7rem">' + e.kuerzel + '</span></td>'
        + '<td style="padding:6px 8px;font-size:0.8rem">' + e.name + status + '</td>'
        + '<td style="padding:6px 8px;font-size:0.75rem;color:#94a3b8">' + via + '</td>'
        + '<td style="padding:6px 8px;text-align:right;font-size:0.8rem">' + umsatz + '</td>'
        + '<td style="padding:6px 8px;text-align:right;font-size:0.8rem;' + jeClass + '">' + jeStr + '</td>'
        + '<td style="padding:6px 8px;text-align:right;font-size:0.8rem">' + ek + '</td>'
        + '<td style="padding:6px 8px;text-align:right;font-size:0.8rem">' + ma + '</td>'
        + '</tr>\n';
    });
    EL.innerHTML = '<table style="width:100%;border-collapse:collapse;font-size:0.8rem">'
      + '<thead><tr style="border-bottom:2px solid #475569;color:#94a3b8;font-size:0.7rem;text-transform:uppercase">'
      + '<th style="padding:4px 8px;text-align:left">K&uuml;rzel</th>'
      + '<th style="padding:4px 8px;text-align:left">Gesellschaft</th>'
      + '<th style="padding:4px 8px;text-align:left">Beteiligung</th>'
      + '<th style="padding:4px 8px;text-align:right">Umsatz T&euro;</th>'
      + '<th style="padding:4px 8px;text-align:right">J&Uuml; vor EAV</th>'
      + '<th style="padding:4px 8px;text-align:right">EK-Quote</th>'
      + '<th style="padding:4px 8px;text-align:right">MA</th>'
      + '</tr></thead><tbody>' + rows + '</tbody></table>';
  }

  // ── JÜ-Timeline Chart ──────────────────────────────────────────────────
  var JU_EL = document.getElementById('chart-bet-je');
  if (JU_EL && D.entities && D.kennzahlen) {
    var COMPANIES = [
      {k:'GEWO', label:'GeWo', color:'#0369a1'},
      {k:'ITM',  label:'ITM',  color:'#059669'},
      {k:'SW',   label:'SW Werkst.', color:'#0d9488'},
      {k:'SWSZ', label:'SWSZ', color:'#1d4ed8'},
      {k:'SWSZ_NETZ', label:'SWSZ Netz', color:'#3b82f6'},
      {k:'SWB',  label:'SWB',  color:'#7c3aed'},
      {k:'SSB',  label:'SSB',  color:'#64748b'},
      {k:'SNG',  label:'SNG (Defizit)', color:'#dc2626'}
    ];
    var JAHRE = ['2021','2022','2023','2024'];
    var traces = [];
    COMPANIES.forEach(function(c) {
      var kn2 = D.kennzahlen[c.k];
      if (!kn2) return;
      var y = JAHRE.map(function(yr) {
        var v = kn2[yr] ? kn2[yr].je : null;
        return (v !== null && v !== undefined) ? Math.round(v) : null;
      });
      traces.push({
        type: 'bar', name: c.label,
        x: JAHRE, y: y,
        marker: { color: c.color },
        hovertemplate: c.label + ' %{x}: %{y} T€<extra></extra>'
      });
    });
    Plotly.newPlot('chart-bet-je', traces, {
      barmode: 'group',
      paper_bgcolor: '#1e293b', plot_bgcolor: '#1e293b',
      font: { color: '#e2e8f0', size: 11 },
      margin: { l: 60, r: 20, t: 10, b: 40 },
      legend: { orientation: 'h', y: -0.2, font: { size: 10 } },
      xaxis: { gridcolor: '#334155' },
      yaxis: { gridcolor: '#334155', tickformat: ',d',
               title: { text: 'T€', font: { size: 10 } } }
    }, { responsive: true, displayModeBar: false });
  }
}

""".encode("utf-8")

# Zeilenenden auf CRLF normalisieren
BET_JS = BET_JS.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")

content = content.replace(JS_ANCHOR, BET_JS + JS_ANCHOR, 1)

# ---------------------------------------------------------------------------
# 5. Backtick-Prüfung
# ---------------------------------------------------------------------------
bt_new = content.count(b"\x60")
bt_added = bt_new - bt
print(f"Neue Backticks: {bt_new} (hinzugefügt: {bt_added})")
assert bt_new % 2 == 0, f"FEHLER: ungerade Backtick-Anzahl {bt_new}!"
assert bt_new == bt, f"Backtick-Anzahl geändert: {bt} → {bt_new} (sollte gleich bleiben)"

# ---------------------------------------------------------------------------
# 6. Schreiben
# ---------------------------------------------------------------------------
open(HTML, "wb").write(content)
print("OK: index.html aktualisiert")
print(f"Größe: {len(content)//1024} KB")
