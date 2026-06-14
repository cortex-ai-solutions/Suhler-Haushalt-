#!/usr/bin/env python3
"""
patch_bet_fix.py
Ersetzt _initBeteiligungen() durch eine bereinigte Version
ohne non-ASCII in JS-Strings.
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(BASE, "index.html")

content = open(HTML, "rb").read()
bt_before = content.count(b"\x60")
print(f"Backticks vor Fix: {bt_before}")

# ---------------------------------------------------------------------------
# Alte Funktion finden
# ---------------------------------------------------------------------------
OLD_START = b"function _initBeteiligungen() {"
OLD_END   = b"\r\nfunction setupTabs() {"

idx_start = content.find(OLD_START)
idx_end   = content.find(OLD_END, idx_start)
assert idx_start > 0 and idx_end > idx_start, "Funktion nicht gefunden"
OLD_FUNC = content[idx_start:idx_end]
print(f"Alte Funktion: {len(OLD_FUNC)} Bytes")

# ---------------------------------------------------------------------------
# Neue Funktion — komplett ASCII in JS-Strings
# Umlaute in Plotly-Labels: JS-Unicode-Escapes (\\uXXXX in Python)
# Umlaute in innerHTML: HTML-Entities (&uuml; etc.)
# ---------------------------------------------------------------------------
NEW_FUNC_STR = r"""function _initBeteiligungen() {
  if (window._betInit) return;
  window._betInit = true;

  var sanEl = document.getElementById('chart-bet-sankey');
  var tblEl = document.getElementById('bet-table');
  var jeEl  = document.getElementById('chart-bet-je');

  var D = (typeof DATA !== 'undefined' && DATA && DATA.beteiligungen)
          ? DATA.beteiligungen : null;
  if (!D) {
    var msg = '<p style="color:#f87171;padding:1rem">Daten nicht geladen &ndash; ' +
              'bitte Seite neu laden (Strg+Shift+R).</p>';
    if (sanEl) sanEl.innerHTML = msg;
    console.warn('DATA.beteiligungen fehlt', typeof DATA);
    return;
  }
  console.log('_initBeteiligungen: entities=', D.entities ? D.entities.length : 0);

  // --- KPI-Chips ---
  var kn = D.kennzahlen || {};
  var sw24 = (kn['SWSZ'] && kn['SWSZ']['2024']) ? kn['SWSZ']['2024'] : {};
  var sg24 = (kn['SNG']  && kn['SNG']['2024'])  ? kn['SNG']['2024']  : {};

  function fmtT(v) {
    if (v === null || v === undefined) return '-';
    return (v >= 0 ? '' : '-') + Math.abs(Math.round(v)).toLocaleString('de-DE') + ' T\u20ac';
  }
  var el;
  el = document.getElementById('bet-kpi-swsz');
  if (el) el.textContent = fmtT(sw24.umsatz);
  el = document.getElementById('bet-kpi-sng');
  if (el) el.textContent = fmtT(sg24.je);

  var str24 = (D.stroeme && D.stroeme['2024']) ? D.stroeme['2024'] : [];
  var eavSum = 0, divSum = 0;
  str24.forEach(function(s) {
    if (s.typ === 'EAV_GEWINN'    && s.nach === 'CCS'   && s.betrag) eavSum += s.betrag;
    if (s.typ === 'AUSSCHUETTUNG' && s.nach === 'STADT' && s.betrag) divSum += s.betrag;
  });
  el = document.getElementById('bet-kpi-eav');
  if (el) el.textContent = fmtT(eavSum);
  el = document.getElementById('bet-kpi-div');
  if (el) el.textContent = fmtT(divSum);

  // --- Sankey ---
  var NORDER = ['SWSZ_NETZ','SWSZ','SWB','CCS','SNG',
                'THUERINGEN','BUND','STADT','EBKDS','SSZ',
                'ITM','GEWO','LSIM_EXTERN'];
  var NLABELS = {
    'SWSZ_NETZ':  'SW Netz GmbH',
    'SWSZ':       'Stadtwerke GmbH',
    'SWB':        'SW Beteiligungs-GmbH',
    'CCS':        'CCS Holding',
    'SNG':        'Nahverkehr SNG',
    'THUERINGEN': 'Freistaat Th\u00fcringen',
    'BUND':       'Bundesrepublik',
    'STADT':      'Stadt Suhl',
    'EBKDS':      'EB KDS',
    'SSZ':        'Schie\u00dfsportzentrum',
    'ITM':        'Transfusionsmedizin',
    'GEWO':       'GeWo Wohnen',
    'LSIM_EXTERN':'Zella-Mehlis (LSIM)'
  };
  var FCOLORS = {
    'EAV_GEWINN':           'rgba(234,179,8,0.55)',
    'VERLUSTUEBERNAHME':    'rgba(239,68,68,0.5)',
    'BEIHILFE':             'rgba(99,102,241,0.5)',
    'ZUSCHUSS':             'rgba(239,68,68,0.4)',
    'AUSSCHUETTUNG':        'rgba(34,197,94,0.5)',
    'AUSGLEICH_MINDERHEIT': 'rgba(148,163,184,0.45)'
  };

  var nIdx = {};
  NORDER.forEach(function(k, i) { nIdx[k] = i; });
  var labels = NORDER.map(function(k) { return NLABELS[k] || k; });
  var nColors = NORDER.map(function(k) {
    if (k==='SWSZ_NETZ'||k==='SWSZ'||k==='SWB') return '#1d4ed8';
    if (k==='CCS')   return '#7c3aed';
    if (k==='SNG')   return '#dc2626';
    if (k==='THUERINGEN'||k==='BUND') return '#4338ca';
    if (k==='STADT') return '#0f766e';
    if (k==='ITM'||k==='GEWO') return '#059669';
    return '#64748b';
  });

  var srcs=[], tgts=[], vals=[], lcolors=[], hovs=[];
  str24.forEach(function(s) {
    var si = nIdx[s.von], ti = nIdx[s.nach];
    if (si===undefined||ti===undefined||!s.betrag||s.betrag<=0) return;
    srcs.push(si); tgts.push(ti); vals.push(s.betrag);
    lcolors.push(FCOLORS[s.typ] || 'rgba(148,163,184,0.4)');
    hovs.push((s.bez||s.typ) + '<br>' +
              Math.round(s.betrag).toLocaleString('de-DE') + ' T\u20ac');
  });
  console.log('Sankey links:', srcs.length, 'von', str24.length, 'Stroemen');

  if (sanEl && srcs.length > 0 && typeof Plotly !== 'undefined') {
    Plotly.newPlot(sanEl, [{
      type:'sankey', orientation:'h', arrangement:'snap',
      node:{pad:18, thickness:22, label:labels, color:nColors,
            hovertemplate:'%{label}<extra></extra>'},
      link:{source:srcs, target:tgts, value:vals, color:lcolors,
            customdata:hovs, hovertemplate:'%{customdata}<extra></extra>'}
    }], {
      paper_bgcolor:'#1e293b', plot_bgcolor:'#1e293b',
      font:{color:'#e2e8f0', size:11},
      margin:{l:10,r:10,t:10,b:10}
    }, {responsive:true, displayModeBar:false});
  } else if (sanEl) {
    sanEl.innerHTML = '<p style="color:#94a3b8;padding:1rem">Links: ' +
                      srcs.length + '</p>';
  }

  // --- Tabelle ---
  if (tblEl && D.entities) {
    var SFARBE = {
      'ENERGIE':'#1d4ed8','HOLDING':'#7c3aed','NAHVERKEHR':'#dc2626',
      'WOHNEN':'#0369a1','GESUNDHEIT':'#059669','SOZIAL':'#0d9488',
      'SPORT':'#b45309','IT':'#6b21a8','ENTSORGUNG':'#78716c',
      'INFRASTRUKTUR':'#64748b','SONSTIGES':'#475569','KOMMUNE':'#0f766e'
    };
    var rows = '';
    D.entities.forEach(function(ent) {
      if (ent.kuerzel === 'STADT') return;
      var k24 = D.kennzahlen[ent.kuerzel] ? D.kennzahlen[ent.kuerzel]['2024'] : null;
      var umsatz = k24&&k24.umsatz!=null
                   ? Math.round(k24.umsatz).toLocaleString('de-DE') : '-';
      var je    = k24&&k24.je!=null ? Math.round(k24.je) : null;
      var jeStr = je!=null ? (je>=0?'+':'')+je.toLocaleString('de-DE') : '-';
      var jeCol = je!=null ? (je>=0?'color:#4ade80':'color:#f87171') : '';
      var ekq   = k24&&k24.ek_quote!=null ? k24.ek_quote.toFixed(1)+'&nbsp;%' : '-';
      var ma    = k24&&k24.mitarbeiter!=null ? k24.mitarbeiter : '-';
      var f     = SFARBE[ent.sektor] || '#64748b';
      var sfx   = ent.status==='liquidation'?' (i.L.)':ent.status==='fiskalisiert'?'*':'';
      var via   = ent.via&&ent.via!=='STADT'?'via '+ent.via:'direkt';
      rows += '<tr style="border-bottom:1px solid #334155">'
        +'<td style="padding:5px 8px"><span style="background:'+f+'22;color:'+f+';'
        +'padding:1px 6px;border-radius:4px;font-size:0.7rem">'+ent.kuerzel+'</span></td>'
        +'<td style="padding:5px 8px;font-size:0.8rem">'+ent.name+sfx+'</td>'
        +'<td style="padding:5px 8px;font-size:0.75rem;color:#94a3b8">'+via+'</td>'
        +'<td style="padding:5px 8px;text-align:right;font-size:0.8rem">'+umsatz+'</td>'
        +'<td style="padding:5px 8px;text-align:right;font-size:0.8rem;'+jeCol+'">'+jeStr+'</td>'
        +'<td style="padding:5px 8px;text-align:right;font-size:0.8rem">'+ekq+'</td>'
        +'<td style="padding:5px 8px;text-align:right;font-size:0.8rem">'+ma+'</td>'
        +'</tr>\n';
    });
    tblEl.innerHTML =
      '<table style="width:100%;border-collapse:collapse;font-size:0.8rem">'
      +'<thead><tr style="border-bottom:2px solid #475569;color:#94a3b8;'
      +'font-size:0.7rem;text-transform:uppercase">'
      +'<th style="padding:4px 8px;text-align:left">K&uuml;rzel</th>'
      +'<th style="padding:4px 8px;text-align:left">Gesellschaft</th>'
      +'<th style="padding:4px 8px;text-align:left">Beteiligung</th>'
      +'<th style="padding:4px 8px;text-align:right">Umsatz T&euro;</th>'
      +'<th style="padding:4px 8px;text-align:right">J&Uuml; vor EAV</th>'
      +'<th style="padding:4px 8px;text-align:right">EK-Quote</th>'
      +'<th style="padding:4px 8px;text-align:right">MA</th>'
      +'</tr></thead><tbody>'+rows+'</tbody></table>';
  }

  // --- JUe-Timeline ---
  if (jeEl && D.kennzahlen && typeof Plotly !== 'undefined') {
    var COS = [
      {k:'GEWO',      lbl:'GeWo',          col:'#0369a1'},
      {k:'ITM',       lbl:'ITM',           col:'#059669'},
      {k:'SW',        lbl:'SW Werkst.',    col:'#0d9488'},
      {k:'SWSZ',      lbl:'SWSZ',          col:'#1d4ed8'},
      {k:'SWSZ_NETZ', lbl:'SWSZ Netz',    col:'#3b82f6'},
      {k:'SWB',       lbl:'SWB',           col:'#7c3aed'},
      {k:'SSB',       lbl:'SSB',           col:'#64748b'},
      {k:'SNG',       lbl:'SNG (Defizit)', col:'#dc2626'}
    ];
    var JAHRE = ['2021','2022','2023','2024'];
    var traces = [];
    COS.forEach(function(c) {
      var kdata = D.kennzahlen[c.k];
      if (!kdata) return;
      var y = JAHRE.map(function(yr) {
        var v = kdata[yr] ? kdata[yr].je : null;
        return (v!==null&&v!==undefined) ? Math.round(v) : null;
      });
      traces.push({type:'bar', name:c.lbl, x:JAHRE, y:y,
        marker:{color:c.col},
        hovertemplate:c.lbl+' %{x}: %{y} T\u20ac<extra></extra>'});
    });
    if (traces.length > 0) {
      Plotly.newPlot(jeEl, traces, {
        barmode:'group',
        paper_bgcolor:'#1e293b', plot_bgcolor:'#1e293b',
        font:{color:'#e2e8f0', size:11},
        margin:{l:60,r:20,t:10,b:40},
        legend:{orientation:'h', y:-0.25, font:{size:10}},
        xaxis:{gridcolor:'#334155'},
        yaxis:{gridcolor:'#334155', tickformat:',d',
               title:{text:'T\u20ac', font:{size:10}}}
      }, {responsive:true, displayModeBar:false});
    }
  }
}"""

# Python raw-string hat \uXXXX als Literalzeichen — gut so (JS-Escapes bleiben erhalten).
# CRLF normalisieren
NEW_FUNC = NEW_FUNC_STR.encode("utf-8").replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")

# Non-ASCII pruefen
non_ascii = [b for b in NEW_FUNC if b > 127]
print(f"Non-ASCII-Bytes in neuer Funktion: {len(non_ascii)}")
if non_ascii:
    print("Bytes:", [hex(b) for b in non_ascii[:20]])
    # Zeige Kontext
    for i, b in enumerate(NEW_FUNC):
        if b > 127:
            print(f"  pos={i}: 0x{b:02x}  ctx={repr(NEW_FUNC[max(0,i-20):i+10])}")
            break

# ---------------------------------------------------------------------------
# Ersetzen
# ---------------------------------------------------------------------------
content = content.replace(OLD_FUNC, NEW_FUNC, 1)
assert content.count(b"function _initBeteiligungen") == 1

bt_after = content.count(b"\x60")
print(f"Backticks: {bt_before} -> {bt_after}")
assert bt_after == bt_before and bt_after % 2 == 0

open(HTML, "wb").write(content)
print(f"OK: index.html ({len(content)//1024} KB)")
