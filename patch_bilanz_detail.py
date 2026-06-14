"""
patch_bilanz_detail.py
Fuegt Level-3-Detailcharts (Sachanlagen, Finanzanlage, Verbindlichkeiten)
und Bilanzentwicklungs-Karte in den Bilanz-Subtab des Vermoegen-Tabs ein.
Patch-Ansatz: String-Replacement (keine Template-Literale), CRLF-sicher.
"""
import os, re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "index.html")

CRLF = "\r\n"


def apply(content: str) -> str:
    # ── 1. HTML: neue Chart-Divs in vtab-bilanz, vor dem schliessenden Div ──
    # Anker: letztes </div> im vtab-bilanz (Hinweis-Karte) + Uebergang zu vtab-ebkds
    HTML_ANCHOR = (
        '      </div>' + CRLF
        + '    </div>' + CRLF
        + CRLF
        + '    <div id="vtab-ebkds"'
    )
    assert HTML_ANCHOR in content, "FEHLER: vtab-bilanz Abschluss-Anker nicht gefunden"

    NEW_HTML = (
        '      <!-- Detail-Charts Ebene 3 -->' + CRLF
        + '      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">' + CRLF
        + '        <div class="card p-5">' + CRLF
        + '          <div class="section-title">Sachanlagen 2021 &ndash; 10 Positionen (Mio.&nbsp;&#8364;)</div>' + CRLF
        + '          <div id="chart-sachanlagen-detail" style="height:340px"></div>' + CRLF
        + '        </div>' + CRLF
        + '        <div class="card p-5">' + CRLF
        + '          <div class="section-title">Finanzanlageverm&ouml;gen 2021 &ndash; Beteiligungen</div>' + CRLF
        + '          <div id="chart-finanzanlage-detail" style="height:340px"></div>' + CRLF
        + '        </div>' + CRLF
        + '      </div>' + CRLF
        + '      <div class="card p-5 mt-4">' + CRLF
        + '        <div class="section-title">Verbindlichkeiten-Aufschl&uuml;sselung 2020 vs. 2021 (Mio.&nbsp;&#8364;)</div>' + CRLF
        + '        <div id="chart-vb-detail" style="height:280px"></div>' + CRLF
        + '      </div>' + CRLF
        + '      <div class="card p-5 mt-4">' + CRLF
        + '        <div class="section-title">Bilanzentwicklung seit 01.01.2013</div>' + CRLF
        + '        <div id="bilanz-entwicklung-body" class="text-sm mt-2"></div>' + CRLF
        + '      </div>' + CRLF
    )

    content = content.replace(HTML_ANCHOR, NEW_HTML + HTML_ANCHOR, 1)

    # ── 2. JS: _renderBilanzDetail() + Monkey-Patch renderVermoegen ──────────
    # Anker: vor setupTabs()  (sicherer, unveraenderlicher Punkt)
    JS_ANCHOR = "  setupTabs();"
    assert JS_ANCHOR in content, "FEHLER: setupTabs()-Anker nicht gefunden"

    JS_CODE = (
        '    // ── Bilanz Detail-Charts (Level 3) ──────────────────────────────────' + CRLF
        + '    var _bilanzDetailRendered = false;' + CRLF
        + '    var _origRenderVermoegenBD = renderVermoegen;' + CRLF
        + '    renderVermoegen = function() {' + CRLF
        + '      _origRenderVermoegenBD();' + CRLF
        + '      if (!_bilanzDetailRendered && DATA && DATA.bilanz) {' + CRLF
        + '        _bilanzDetailRendered = true;' + CRLF
        + '        _renderBilanzDetail();' + CRLF
        + '      }' + CRLF
        + '    };' + CRLF
        + CRLF
        + '    function _renderBilanzDetail() {' + CRLF
        + '      var B = DATA.bilanz;' + CRLF
        + '      if (!B || !B.by_year) return;' + CRLF
        + '      var yr21 = B.by_year["2021"] || {aktiva:[], passiva:[]};' + CRLF
        + '      var yr20 = B.by_year["2020"] || {aktiva:[], passiva:[]};' + CRLF
        + CRLF
        + '      function gc(items, code) {' + CRLF
        + '        for (var i = 0; i < items.length; i++) {' + CRLF
        + '          if (items[i].code === code) return items[i].betrag;' + CRLF
        + '        }' + CRLF
        + '        return 0;' + CRLF
        + '      }' + CRLF
        + '      function mio(v) { return Math.round(v / 10000) / 100; }' + CRLF
        + CRLF
        + '      var CFG2 = {responsive: true, displayModeBar: false};' + CRLF
        + CRLF
        + '      // ── Sachanlagen (A1.2.x) Horizontal Bar ─────────────────────────' + CRLF
        + '      var SACH_CODES = ["A1.2.4","A1.2.3","A1.2.1","A1.2.10","A1.2.7",' + CRLF
        + '                        "A1.2.9","A1.2.8","A1.2.6","A1.2.2","A1.2.5"];' + CRLF
        + '      var SACH_LBL  = ["Infrastruktur","Bebaute Grundst.","Wald, Forsten",' + CRLF
        + '                        "Anlagen im Bau","Maschinen & KFZ","Pflanzen & Tiere",' + CRLF
        + '                        "Betriebs-/GA","Kunst & Denkm.","Unbebaute Grundst.",' + CRLF
        + '                        "Bauten (fremd. Grund)"];' + CRLF
        + '      var sach21 = SACH_CODES.map(function(c){return mio(gc(yr21.aktiva,c));});' + CRLF
        + '      var sach20 = SACH_CODES.map(function(c){return mio(gc(yr20.aktiva,c));});' + CRLF
        + '      var sachLayout = Object.assign({}, DARK_LAYOUT, {' + CRLF
        + '        barmode: "group",' + CRLF
        + '        margin: {l:145, r:20, t:20, b:40},' + CRLF
        + '        xaxis: {title: "Mio. €"},' + CRLF
        + '        yaxis: {tickfont: {size:11}},' + CRLF
        + '        legend: {x:0.5, y:1.05, xanchor:"center", orientation:"h"}' + CRLF
        + '      });' + CRLF
        + '      Plotly.newPlot("chart-sachanlagen-detail", [' + CRLF
        + '        {name:"2020", type:"bar", orientation:"h", x:sach20, y:SACH_LBL,' + CRLF
        + '         marker:{color:"rgba(148,163,184,0.7)"},' + CRLF
        + '         hovertemplate:"%{x:.2f} Mio.<extra>2020</extra>"},' + CRLF
        + '        {name:"2021", type:"bar", orientation:"h", x:sach21, y:SACH_LBL,' + CRLF
        + '         marker:{color:"rgba(56,189,248,0.85)"},' + CRLF
        + '         hovertemplate:"%{x:.2f} Mio.<extra>2021</extra>"}' + CRLF
        + '      ], sachLayout, CFG2);' + CRLF
        + CRLF
        + '      // ── Finanzanlagevermögen (A1.3.x) Donut ─────────────────────────' + CRLF
        + '      var FA_CODES  = ["A1.3.1","A1.3.5","A1.3.3","A1.3.7"];' + CRLF
        + '      var FA_LBL    = ["EB KDS & verbund.Untern.","Sonderverm./Zweckverb.",' + CRLF
        + '                       "Beteiligungen","Wertpapiere AV"];' + CRLF
        + '      var fa21 = FA_CODES.map(function(c){return gc(yr21.aktiva,c);});' + CRLF
        + '      Plotly.newPlot("chart-finanzanlage-detail",' + CRLF
        + '        [{type:"pie", values:fa21, labels:FA_LBL, hole:0.4,' + CRLF
        + '          textinfo:"label+percent",' + CRLF
        + '          marker:{colors:["#38bdf8","#818cf8","#34d399","#fb923c"]},' + CRLF
        + '          hovertemplate:"%{label}<br>%{value:,.0f} €<extra></extra>"}],' + CRLF
        + '        Object.assign({}, DARK_LAYOUT, {' + CRLF
        + '          margin:{l:10,r:10,t:30,b:10}, showlegend:false,' + CRLF
        + '          annotations:[{text:"61,2 Mio.", x:0.5, y:0.5, xanchor:"center",' + CRLF
        + '                        font:{size:13,color:"#e2e8f0"}, showarrow:false}]' + CRLF
        + '        }), CFG2);' + CRLF
        + CRLF
        + '      // ── Verbindlichkeiten (P4.x) Bar ─────────────────────────────────' + CRLF
        + '      var VB_CODES = ["P4.2","P4.5","P4.6","P4.7","P4.8","P4.9","P4.10","P4.11"];' + CRLF
        + '      var VB_LBL   = ["Investitionskredite","Lief. & Leistungen","Transferleistungen",' + CRLF
        + '                       "Verbund.Unternehmen","Beteiligungen","Sondervermögen",' + CRLF
        + '                       "Öff.Bereich sonst.","Sonstige VB"];' + CRLF
        + '      var vb21 = VB_CODES.map(function(c){return mio(gc(yr21.passiva,c));});' + CRLF
        + '      var vb20 = VB_CODES.map(function(c){return mio(gc(yr20.passiva,c));});' + CRLF
        + '      Plotly.newPlot("chart-vb-detail", [' + CRLF
        + '        {name:"2020", type:"bar", x:VB_LBL, y:vb20,' + CRLF
        + '         marker:{color:"rgba(148,163,184,0.7)"},' + CRLF
        + '         hovertemplate:"%{x}<br>%{y:.2f} Mio.<extra>2020</extra>"},' + CRLF
        + '        {name:"2021", type:"bar", x:VB_LBL, y:vb21,' + CRLF
        + '         marker:{color:"rgba(251,146,60,0.85)"},' + CRLF
        + '         hovertemplate:"%{x}<br>%{y:.2f} Mio.<extra>2021</extra>"}' + CRLF
        + '      ], Object.assign({}, DARK_LAYOUT, {' + CRLF
        + '        barmode:"group",' + CRLF
        + '        margin:{l:50, r:20, t:20, b:90},' + CRLF
        + '        yaxis:{title:"Mio. €"},' + CRLF
        + '        xaxis:{tickangle:-35, tickfont:{size:11}},' + CRLF
        + '        legend:{x:0.5, y:1.05, xanchor:"center", orientation:"h"}' + CRLF
        + '      }), CFG2);' + CRLF
        + CRLF
        + '      // ── Bilanzentwicklung seit 2013 ───────────────────────────────────' + CRLF
        + '      var elBE = document.getElementById("bilanz-entwicklung-body");' + CRLF
        + '      if (elBE && B.entwicklung) {' + CRLF
        + '        var e = B.entwicklung;' + CRLF
        + '        var h = "";' + CRLF
        + '        h += "<p class=\\"text-slate-300 mb-3\\">Die Bilanzsumme hat sich vom 01.01.2013"' + CRLF
        + '           + " bis 31.12.2021 um <strong class=\\"text-sky-400\\">+"' + CRLF
        + '           + e.veraenderung_seit_2013_teur.toLocaleString("de-DE") + "\\u00a0T\\u20ac</strong>"' + CRLF
        + '           + " auf " + e.bilanzsumme_2021_teur.toLocaleString("de-DE") + "\\u00a0T\\u20ac erh\\u00f6ht.</p>";' + CRLF
        + '        h += "<div class=\\"grid grid-cols-1 md:grid-cols-2 gap-4\\">";' + CRLF
        + '        var sides = [' + CRLF
        + '          {title:"Aktivseite", key:"aktivseite"},' + CRLF
        + '          {title:"Passivseite", key:"passivseite"}' + CRLF
        + '        ];' + CRLF
        + '        sides.forEach(function(s) {' + CRLF
        + '          h += "<div><div class=\\"text-xs font-semibold text-slate-400 uppercase mb-2\\">"' + CRLF
        + '             + s.title + "</div><ul class=\\"space-y-1\\">";' + CRLF
        + '          (e[s.key] || []).forEach(function(item) {' + CRLF
        + '            var sign = item.delta_teur > 0 ? "+" : "";' + CRLF
        + '            var cls  = item.delta_teur > 0 ? "text-emerald-400" : "text-red-400";' + CRLF
        + '            h += "<li class=\\"flex justify-between items-start\\">"' + CRLF
        + '               + "<span class=\\"text-slate-300\\">" + item.position + "</span>"' + CRLF
        + '               + "<span class=\\"" + cls + " font-mono ml-3 whitespace-nowrap\\">"' + CRLF
        + '               + sign + item.delta_teur.toLocaleString("de-DE") + "\\u00a0T\\u20ac</span></li>";' + CRLF
        + '            if (item.anmerkung) {' + CRLF
        + '              h += "<li class=\\"text-slate-500 text-xs pl-2 pb-1\\">" + item.anmerkung + "</li>";' + CRLF
        + '            }' + CRLF
        + '          });' + CRLF
        + '          h += "</ul></div>";' + CRLF
        + '        });' + CRLF
        + '        h += "</div>";' + CRLF
        + '        h += "<p class=\\"text-slate-500 text-xs mt-3\\">Quelle: Jahresabschluss der Stadt Suhl 31.12.2021,"' + CRLF
        + '           + " Seite " + e.quelle_seite + "</p>";' + CRLF
        + '        elBE.innerHTML = h;' + CRLF
        + '      }' + CRLF
        + '    }' + CRLF
        + CRLF
    )

    content = content.replace(JS_ANCHOR, JS_CODE + JS_ANCHOR, 1)
    return content


def main():
    with open(HTML_PATH, "rb") as f:
        content = f.read().decode("utf-8")

    # Idempotenz-Check
    if "chart-sachanlagen-detail" in content:
        print("[SKIP] patch_bilanz_detail already applied")
        return

    n_bt_before = content.count('\x60')
    assert n_bt_before % 2 == 0, f"Ungerade Backtick-Anzahl vor Patch: {n_bt_before}"

    content = apply(content)

    n_bt_after = content.count('\x60')
    assert n_bt_after % 2 == 0, f"Ungerade Backtick-Anzahl nach Patch: {n_bt_after}"
    assert n_bt_after == n_bt_before, f"Backtick-Anzahl geaendert: {n_bt_before} -> {n_bt_after}"

    with open(HTML_PATH, "wb") as f:
        f.write(content.encode("utf-8"))

    print(f"[OK] patch_bilanz_detail angewendet ({n_bt_after} Backticks, unveraendert)")
    print("     + chart-sachanlagen-detail (10 Positionen, 2020 vs 2021)")
    print("     + chart-finanzanlage-detail (Donut A1.3.x)")
    print("     + chart-vb-detail (Verbindlichkeiten P4.x, 2020 vs 2021)")
    print("     + bilanz-entwicklung-body (Veraenderungen seit 2013)")


if __name__ == "__main__":
    main()
