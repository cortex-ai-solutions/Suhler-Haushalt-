# -*- coding: utf-8 -*-
"""
patch_investitionen_tab.py - Neuer Dashboard-Tab "Investitionen" (Projekt-Ebene
Investitionsplan-Drilldown: Eigenanteil vs. Foerdermittel, Kostenentwicklung/Drift).

Folgt den Projekt-Konventionen aus CLAUDE.md:
- index.html wird NUR ueber bytes-Patch geschrieben (CRLF-Pflicht, kein Edit-Tool)
- Kein Unicode in JS-Strings (HTML-Entities statt Pfeilzeichen etc., \\uXXXX statt Umlaut)
- Backtick-Paritaet wird vor/nach dem Schreiben geprueft
- Neu eingefuegter mehrzeiliger Text wird auf CRLF normalisiert (nl()-Helper)
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "index.html")

with open(HTML_PATH, "rb") as f:
    content = f.read().decode("utf-8")

backticks_before = content.count("`")


def nl(s: str) -> str:
    """Normalisiert eingebettete Zeilenumbrueche auf CRLF (Datei-Konvention)."""
    return s.replace("\r\n", "\n").replace("\n", "\r\n")


def must_replace(old, new, label):
    global content
    n = content.count(old)
    if n != 1:
        raise SystemExit(f"[FEHLER] Anker '{label}' kommt {n}x vor (erwartet 1x). Abbruch ohne Aenderung.")
    content = content.replace(old, new, 1)


# ─────────────────────────────────────────────────────────────────────────
# 1) Nav-Tab-Buttons (Desktop + Mobile)
# ─────────────────────────────────────────────────────────────────────────
must_replace(
    '  <div class="tab" data-tab="vermoegen">Verm&ouml;gen</div>',
    nl('  <div class="tab" data-tab="vermoegen">Verm&ouml;gen</div>\n'
       '  <div class="tab" data-tab="investitionen">Investitionen</div>'),
    "desktop-tab-vermoegen",
)

must_replace(
    '  <div class="mobile-tab-item" data-tab="vermoegen">Verm&ouml;gen &amp; Beteiligungen</div>',
    nl('  <div class="mobile-tab-item" data-tab="vermoegen">Verm&ouml;gen &amp; Beteiligungen</div>\n'
       '  <div class="mobile-tab-item" data-tab="investitionen">Investitionen</div>'),
    "mobile-tab-vermoegen",
)

# ─────────────────────────────────────────────────────────────────────────
# 2) Tab-Inhalt: neues <div id="tab-investitionen"> nach tab-vermoegen einfuegen
# ─────────────────────────────────────────────────────────────────────────
TAB_HTML = nl('''
<!-- \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 TAB: INVESTITIONEN \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 -->
<div id="tab-investitionen" class="hidden">

  <!-- KPI-Chips -->
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
    <div class="card p-4">
      <div class="kpi-label">Investitionsvolumen</div>
      <div class="kpi-value text-slate-200" id="inv-kpi-volumen">&ndash;</div>
      <div class="note mt-1"><span id="inv-kpi-n" class="text-blue-400"></span> Ma&szlig;nahmen im aktuellen Haushaltsplan</div>
    </div>
    <div class="card p-4">
      <div class="kpi-label">F&ouml;rdermittel akquiriert</div>
      <div class="kpi-value text-emerald-300" id="inv-kpi-foerderung">&ndash;</div>
      <div class="note mt-1"><span id="inv-kpi-foerderquote" class="text-emerald-400"></span> F&ouml;rderquote am Gesamtvolumen</div>
    </div>
    <div class="card p-4">
      <div class="kpi-label">Gesperrte Ma&szlig;nahmen</div>
      <div class="kpi-value text-rose-300" id="inv-kpi-gesperrt">&ndash;</div>
      <div class="note mt-1">Bewirtschaftungssperre per Stadtratsbeschluss</div>
    </div>
    <div class="card p-4">
      <div class="kpi-label">Neue Ma&szlig;nahmen</div>
      <div class="kpi-value text-violet-300" id="inv-kpi-neu">&ndash;</div>
      <div class="note mt-1"><span id="inv-kpi-kredit" class="text-slate-400"></span> mit Kreditkontingent (Th&uuml;rKIpG)</div>
    </div>
  </div>

  <!-- Kostenentwicklung / Drift-Ranking -->
  <div class="card p-5 mb-6">
    <div class="section-title mb-1">Kostenentwicklung &ndash; gr&ouml;&szlig;te Abweichungen vom urspr&uuml;nglichen Plan</div>
    <div class="note mb-3">
      Vergleicht f&uuml;r jedes Kalenderjahr, was in fr&uuml;heren Haushaltspl&auml;nen f&uuml;r eine Ma&szlig;nahme
      vorgesehen war, mit dem heutigen Planungsstand (Jahres-Prognose-Drift &uuml;ber die Editionen 2023&ndash;2026).
      Positive Werte = teurer/sp&auml;ter als urspr&uuml;nglich geplant.
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-slate-400 text-xs border-b border-slate-700">
            <th class="py-2 pr-3 font-medium">Ma&szlig;nahme</th>
            <th class="py-2 pr-3 font-medium text-right w-28">Ver&auml;nderung</th>
            <th class="py-2 pr-3 font-medium text-right w-24">davon Eigenanteil</th>
            <th class="py-2 font-medium w-32">Betroffene Jahre</th>
          </tr>
        </thead>
        <tbody id="inv-drift-body"></tbody>
      </table>
    </div>
  </div>

  <!-- Filter + Tabelle -->
  <div class="card p-5">
    <div class="flex flex-wrap items-center gap-3 mb-4">
      <div class="section-title flex-1">Investitionsma&szlig;nahmen (Haushaltsplan 2026)</div>
      <div class="flex gap-2" id="inv-filter-btns">
        <button onclick="setInvFilter('alle')"
          class="inv-filter-btn px-3 py-1 rounded-full text-xs border border-slate-600 text-slate-300 active"
          data-filter="alle">Alle</button>
        <button onclick="setInvFilter('aktiv')"
          class="inv-filter-btn px-3 py-1 rounded-full text-xs border border-slate-600 text-slate-400"
          data-filter="aktiv">Aktiv</button>
        <button onclick="setInvFilter('gesperrt')"
          class="inv-filter-btn px-3 py-1 rounded-full text-xs border border-slate-600 text-slate-400"
          data-filter="gesperrt">Gesperrt</button>
        <button onclick="setInvFilter('neu')"
          class="inv-filter-btn px-3 py-1 rounded-full text-xs border border-slate-600 text-slate-400"
          data-filter="neu">Neu</button>
      </div>
      <div id="inv-tp-filter-info" class="hidden w-full flex items-center
           gap-2 px-3 py-1.5 rounded-lg bg-blue-900/30 border border-blue-700/60 text-xs">
        <span class="text-blue-300">&#x1F50D; TP-Filter aktiv:</span>
        <span id="inv-tp-filter-label" class="text-blue-200 font-medium flex-1"></span>
        <button onclick="clearInvTPFilter()"
                class="text-blue-400 hover:text-white px-2 py-0.5 rounded border border-blue-700
                       hover:bg-blue-700 transition-colors text-[10px]">
          &times; Filter entfernen
        </button>
      </div>
      <input id="inv-search" type="text" placeholder="Ma&szlig;nahme suchen&hellip;"
        class="bg-slate-800 border border-slate-600 rounded px-3 py-1 text-xs text-slate-300
               placeholder:text-slate-500 focus:outline-none focus:border-slate-400 w-48"
        oninput="renderInvTable()">
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-sm" id="inv-tabelle">
        <thead>
          <tr class="text-left text-slate-400 text-xs border-b border-slate-700">
            <th class="py-2 pr-3 font-medium">Ma&szlig;nahme</th>
            <th class="py-2 pr-3 font-medium w-14">TP</th>
            <th class="py-2 pr-3 font-medium text-right w-28">Gesamt (Invest.)</th>
            <th class="py-2 pr-3 font-medium w-40">Eigenanteil / F&ouml;rderung</th>
            <th class="py-2 font-medium w-20">Status</th>
          </tr>
        </thead>
        <tbody id="inv-tabelle-body"></tbody>
      </table>
    </div>
  </div>

</div>
''')

must_replace(
    '<div id="drilldown-overlay" class="hidden" onclick="if(event.target===this)closeDrillDown()">',
    TAB_HTML.strip("\r\n") + nl("\n") + '<div id="drilldown-overlay" class="hidden" onclick="if(event.target===this)closeDrillDown()">',
    "insert-tab-investitionen",
)

# ─────────────────────────────────────────────────────────────────────────
# 3) setupTabs(): TABS-Array + Dispatch-Zeile ergaenzen
# ─────────────────────────────────────────────────────────────────────────
must_replace(
    '  const TABS = ["overview", "details", "personal", "jahresvergleich", "zeitreihe", "hsk", "simulator", "vermoegen"];',
    '  const TABS = ["overview", "details", "personal", "jahresvergleich", "zeitreihe", "hsk", "simulator", "vermoegen", "investitionen"];',
    "tabs-array",
)

must_replace(
    '      if (name === "vermoegen") renderVermoegen();',
    nl('      if (name === "vermoegen") renderVermoegen();\n'
       '      if (name === "investitionen") renderInvestitionen();'),
    "dispatch-vermoegen",
)

# ─────────────────────────────────────────────────────────────────────────
# 4) initHsk()-Aufruf beim Boot um initInvestitionen() ergaenzen
# ─────────────────────────────────────────────────────────────────────────
must_replace(
    "  initHsk();",
    nl("  initHsk();\n  initInvestitionen();"),
    "boot-initHsk",
)

# ─────────────────────────────────────────────────────────────────────────
# 5) JS-Logik am Ende des <script>-Blocks anhaengen (vor </script>)
#    Keine Backticks/Template-Literals -> String-Konkatenation mit '+'.
#    Keine rohen Umlaute in JS-Strings -> \\uXXXX-Escapes.
# ─────────────────────────────────────────────────────────────────────────
JS_BLOCK = nl('''
// \u2500\u2500 TAB: Investitionen (Projekt-Ebene Investitionsplan) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
var _invFilter = "alle";
var _invRendered = false;
var _invTpFilter = null;

function initInvestitionen() {
  var el = document.getElementById("tab-investitionen");
  if (el && !DATA.investitionsprojekte) el.classList.add("hidden");
}

function setInvFilter(f) {
  _invFilter = f;
  document.querySelectorAll(".inv-filter-btn").forEach(function(b) {
    var isActive = b.dataset.filter === f;
    b.classList.toggle("active", isActive);
    b.classList.toggle("text-white", isActive);
    b.classList.toggle("border-blue-500", isActive);
    b.classList.toggle("text-slate-300", isActive);
    b.classList.toggle("text-slate-400", !isActive);
    b.classList.toggle("border-slate-600", !isActive);
  });
  renderInvTable();
}

function setInvTPFilter(tpNr, tpLabel) {
  _invTpFilter = tpNr;
  var info = document.getElementById("inv-tp-filter-info");
  var label = document.getElementById("inv-tp-filter-label");
  if (info) info.classList.remove("hidden");
  if (label) label.textContent = "TP " + tpNr + (tpLabel ? " \\u2013 " + tpLabel : "");
  var tab = document.querySelector("#tabbar .tab[data-tab=\\"investitionen\\"]");
  if (tab) tab.click();
  renderInvTable();
}

function clearInvTPFilter() {
  _invTpFilter = null;
  var info = document.getElementById("inv-tp-filter-info");
  if (info) info.classList.add("hidden");
  renderInvTable();
}

function invFmtEur(v) {
  return fmt(Math.round(v), 0) + " \\u20ac";
}

function invFmtSigned(v) {
  if (!v) return "<span class=\\"text-slate-600\\">\\u2013</span>";
  var col = v > 0 ? "text-rose-400" : "text-emerald-400";
  var sign = v > 0 ? "+" : "";
  return "<span class=\\"" + col + "\\">" + sign + invFmtEur(v) + "</span>";
}

function renderInvestitionen() {
  var IP = DATA.investitionsprojekte;
  if (!IP) return;
  if (_invRendered) return;
  _invRendered = true;

  var k = IP.kpis;
  setText("inv-kpi-volumen", invFmtEur(k.gesamtvolumen));
  setText("inv-kpi-n", k.anzahl_aktuell);
  setText("inv-kpi-foerderung", invFmtEur(k.foerderung_summe));
  setText("inv-kpi-foerderquote", (k.foerderquote_pct != null ? k.foerderquote_pct : "\\u2013") + " %");
  setText("inv-kpi-gesperrt", k.anzahl_gesperrt);
  setText("inv-kpi-neu", k.anzahl_neu);
  setText("inv-kpi-kredit", k.anzahl_mit_kreditkontingent + " Ma\\u00dfnahmen");

  renderInvDrift();
  renderInvTable();
}

function renderInvDrift() {
  var IP = DATA.investitionsprojekte;
  if (!IP) return;
  var rows = (IP.kostenentwicklung || []).map(function(m) {
    var pctTxt = m.drift_aus_pct != null
      ? " (" + (m.drift_aus_pct > 0 ? "+" : "") + m.drift_aus_pct + " %)"
      : " (neu hinzugekommen)";
    return "<tr class=\\"border-b border-slate-800 hover:bg-slate-800/40 cursor-pointer\\" onclick=\\"jumpToInvMassnahme(\'" + m.investitionsnummer + "\')\\">" +
      "<td class=\\"py-2 pr-3\\"><div class=\\"text-slate-200 text-sm\\">" + escHtml(m.bezeichnung) + "</div>" +
      "<div class=\\"text-xs text-slate-500 font-mono\\">" + m.investitionsnummer + "</div></td>" +
      "<td class=\\"py-2 pr-3 text-right font-mono text-xs\\">" + invFmtSigned(m.drift_aus_eur) + pctTxt + "</td>" +
      "<td class=\\"py-2 pr-3 text-right font-mono text-xs\\">" + invFmtSigned(m.drift_eigenanteil_eur) + "</td>" +
      "<td class=\\"py-2 text-xs text-slate-400\\">" + m.drift_jahre.join(", ") + "</td>" +
      "</tr>";
  });
  document.getElementById("inv-drift-body").innerHTML = rows.join("") ||
    "<tr><td colspan=\\"4\\" class=\\"py-3 text-slate-500 text-xs\\">Keine mehrj\\u00e4hrig vergleichbaren Ver\\u00e4nderungen gefunden.</td></tr>";
}

function renderInvTable() {
  var IP = DATA.investitionsprojekte;
  if (!IP) return;
  var searchEl = document.getElementById("inv-search");
  var query = (searchEl ? searchEl.value : "").toLowerCase();

  var STATUS_COLOR = {
    aktiv:    "text-blue-300  bg-blue-900/30",
    gesperrt: "text-rose-300  bg-rose-900/30",
    neu:      "text-violet-300 bg-violet-900/30",
  };
  var STATUS_LABEL = { aktiv: "aktiv", gesperrt: "gesperrt", neu: "neu" };

  var filtered = (IP.massnahmen || []).filter(function(m) {
    if (m.letzte_edition !== IP.aktuelles_jahr) return false;
    if (_invFilter !== "alle" && m.status !== _invFilter) return false;
    if (_invTpFilter && m.tp_nr !== _invTpFilter) return false;
    if (query && m.bezeichnung.toLowerCase().indexOf(query) === -1 && m.investitionsnummer.indexOf(query) === -1) return false;
    return true;
  }).sort(function(a, b) { return b.aus_gesamt - a.aus_gesamt; });

  var rows = filtered.map(function(m) {
    var sc = STATUS_COLOR[m.status] || "text-slate-400";
    var foerderBar;
    if (m.aus_gesamt > 0) {
      var pctF = Math.max(0, Math.min(100, (m.foerderung_gesamt / m.aus_gesamt) * 100));
      foerderBar =
        "<div class=\\"w-full h-1.5 rounded-full bg-slate-700 overflow-hidden flex mt-1\\">" +
        "<div style=\\"width:" + pctF.toFixed(1) + "%;background:#34d399\\"></div>" +
        "<div style=\\"width:" + (100 - pctF).toFixed(1) + "%;background:#3b82f6\\"></div>" +
        "</div>" +
        "<div class=\\"text-[10px] text-slate-500 mt-0.5\\">" +
        "<span class=\\"text-emerald-400\\">" + invFmtEur(m.foerderung_gesamt) + " F\\u00f6rderung</span> \\u00b7 " +
        "<span class=\\"text-blue-400\\">" + invFmtEur(m.eigenanteil_gesamt) + " Eigenanteil</span></div>";
    } else {
      foerderBar = "<span class=\\"text-slate-600 text-xs\\">\\u2013</span>";
    }
    return [
      "<tr data-nr=\\"" + m.investitionsnummer + "\\" class=\\"border-b border-slate-800 hover:bg-slate-800/40 cursor-pointer\\" onclick=\\"toggleInvRow(this,\'" + m.investitionsnummer + "\')\\">" +
      "<td class=\\"py-2 pr-3\\"><div class=\\"text-slate-200 text-sm\\">" + escHtml(m.bezeichnung) + "</div>" +
      "<div class=\\"text-xs text-slate-500 font-mono\\">" + m.investitionsnummer + "</div></td>" +
      "<td class=\\"py-2 pr-3 text-slate-400 font-mono text-xs\\">" + (m.tp_nr || "\\u2013") + "</td>" +
      "<td class=\\"py-2 pr-3 text-right font-mono text-xs text-slate-200\\">" + invFmtEur(m.aus_gesamt) + "</td>" +
      "<td class=\\"py-2 pr-3\\">" + foerderBar + "</td>" +
      "<td class=\\"py-2\\"><span class=\\"text-xs px-1.5 py-0.5 rounded " + sc + "\\">" + (STATUS_LABEL[m.status] || m.status) + "</span></td>" +
      "</tr>",
      "<tr id=\\"inv-detail-" + m.investitionsnummer + "\\" class=\\"hidden bg-slate-900/50\\">" +
      "<td colspan=\\"5\\" class=\\"px-4 py-3\\">" + buildInvDetail(m) + "</td></tr>",
    ];
  });

  document.getElementById("inv-tabelle-body").innerHTML = rows.length ? rows.flat().join("") :
    "<tr><td colspan=\\"5\\" class=\\"py-4 text-center text-slate-500 text-xs\\">Keine Ma\\u00dfnahmen gefunden.</td></tr>";
}

function buildInvDetail(m) {
  var konten = m.konten || [];
  var einK = konten.filter(function(k) { return k.richtung === "EINZAHLUNG"; });
  var ausK = konten.filter(function(k) { return k.richtung === "AUSZAHLUNG"; });

  var kontenHtml = function(list) {
    if (!list.length) return "<div class=\\"text-slate-500 text-xs\\">keine</div>";
    return list.map(function(k) {
      return "<div class=\\"flex justify-between text-xs py-0.5 border-b border-slate-800/60\\">" +
        "<span class=\\"text-slate-400\\">" + escHtml(k.bezeichnung) + " <span class=\\"text-slate-600 font-mono\\">(" + k.konto_nummer + ")</span></span>" +
        "<span class=\\"font-mono text-slate-300\\">" + invFmtEur(k.gesamt) + "</span></div>";
    }).join("");
  };

  var editionenHtml = (m.editionen || []).map(function(e) {
    return "<div class=\\"flex justify-between text-xs py-0.5\\">" +
      "<span class=\\"text-slate-400\\">HH-Plan " + e.jahr + (e.gesperrt ? " <span class=\\"text-rose-400\\">(gesperrt)</span>" : "") + "</span>" +
      "<span class=\\"font-mono text-slate-300\\">Ansatz " + invFmtEur(e.aus_ansatz) + " \\u00b7 Gesamt " + invFmtEur(e.aus_gesamt) + "</span></div>";
  }).join("");

  var driftHtml = "";
  if (m.drift_aus_eur) {
    driftHtml = "<div class=\\"mt-3 p-2 rounded bg-slate-800/60 text-xs\\">" +
      "<span class=\\"text-slate-400\\">Ver\\u00e4nderung seit erster Erfassung (" + m.erste_edition + "): </span>" +
      invFmtSigned(m.drift_aus_eur) +
      (m.drift_aus_pct != null ? " (" + (m.drift_aus_pct > 0 ? "+" : "") + m.drift_aus_pct + " %)" : " (neu hinzugekommen)") +
      ", davon Eigenanteil " + invFmtSigned(m.drift_eigenanteil_eur) +
      "</div>";
  }

  return "<div class=\\"grid grid-cols-1 lg:grid-cols-3 gap-4 text-xs text-slate-300\\">" +
    "<div class=\\"lg:col-span-2\\">" +
    "<div class=\\"font-medium text-slate-200 mb-1\\">Erl\\u00e4uterung</div>" +
    "<p class=\\"text-slate-400 leading-relaxed whitespace-pre-line\\">" + escHtml(m.erlaeuterung || "Keine weitere Erl\\u00e4uterung.") + "</p>" +
    driftHtml +
    "</div>" +
    "<div>" +
    "<div class=\\"font-medium text-slate-200 mb-2\\">Editionen-Verlauf</div>" +
    "<div class=\\"space-y-0.5 mb-3\\">" + editionenHtml + "</div>" +
    "<div class=\\"font-medium text-slate-200 mb-1\\">F\\u00f6rdermittel / Einzahlungen</div>" +
    "<div class=\\"mb-2\\">" + kontenHtml(einK) + "</div>" +
    "<div class=\\"font-medium text-slate-200 mb-1\\">Auszahlungskonten</div>" +
    kontenHtml(ausK) +
    "</div>" +
    "</div>";
}

function toggleInvRow(tr, nr) {
  var detail = document.getElementById("inv-detail-" + nr);
  if (!detail) return;
  var isOpen = !detail.classList.contains("hidden");
  document.querySelectorAll("[id^=inv-detail-]").forEach(function(el) { el.classList.add("hidden"); });
  if (!isOpen) detail.classList.remove("hidden");
}

function jumpToInvMassnahme(nr) {
  var tab = document.querySelector("#tabbar .tab[data-tab=\\"investitionen\\"]");
  if (tab) tab.click();
  setInvFilter("alle");
  clearInvTPFilter();
  var search = document.getElementById("inv-search");
  if (search) { search.value = ""; }
  renderInvTable();
  setTimeout(function() {
    var row = document.querySelector("tr[data-nr=\\"" + nr + "\\"]");
    if (row) {
      row.scrollIntoView({ behavior: "smooth", block: "center" });
      toggleInvRow(row, nr);
    }
  }, 50);
}
''')

SCRIPT_END_ANCHOR = nl(
    "// Monkey-Patch renderHsk: Infothek nach dem HSK-Render aufrufen\n"
    "(function() {\n"
    "  var _rh_infothek_orig = renderHsk;\n"
    "  renderHsk = function() {\n"
    "    _rh_infothek_orig.apply(this, arguments);\n"
    "    renderHskInfothek();\n"
    "  };\n"
    "})();\n"
    "\n"
    "</script>"
)
must_replace(SCRIPT_END_ANCHOR, SCRIPT_END_ANCHOR.replace("</script>", "") + JS_BLOCK + nl("\n") + "</script>", "js-append")

backticks_after = content.count("`")
if backticks_before != backticks_after:
    raise SystemExit(f"[FEHLER] Backtick-Anzahl geaendert: vorher {backticks_before}, nachher {backticks_after}. Abbruch, Datei NICHT geschrieben.")
if backticks_after % 2 != 0:
    raise SystemExit(f"[FEHLER] Backtick-Anzahl ungerade ({backticks_after}). Abbruch, Datei NICHT geschrieben.")

with open(HTML_PATH, "wb") as f:
    f.write(content.encode("utf-8"))

print(f"[OK] index.html gepatcht. Backticks: {backticks_before} -> {backticks_after}")
