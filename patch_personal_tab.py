"""
Patch-Skript: Personal-Tab in index.html einfügen.
Verwendet CRLF-aware Byte-Operationen (Windows).
"""

path = "index.html"

with open(path, "rb") as f:
    raw = f.read()

content = raw.decode("utf-8")
CRLF = "\r\n"


def apply(c, old, new, label):
    if old not in c:
        raise ValueError(f"NICHT GEFUNDEN: {label!r}")
    c2 = c.replace(old, new, 1)
    if c2 == c:
        raise ValueError(f"KEINE ÄNDERUNG: {label!r}")
    print(f"  [OK] {label}")
    return c2


# ── 1: Tab-Button "Personal" zwischen Details und Jahresvergleich ──────────
OLD_TAB = (
    '  <div class="tab" data-tab="details">Details</div>' + CRLF +
    '  <div class="tab" data-tab="jahresvergleich">Jahresvergleich</div>'
)
NEW_TAB = (
    '  <div class="tab" data-tab="details">Details</div>' + CRLF +
    '  <div class="tab" data-tab="personal">Personal</div>' + CRLF +
    '  <div class="tab" data-tab="jahresvergleich">Jahresvergleich</div>'
)
content = apply(content, OLD_TAB, NEW_TAB, "Tab-Button Personal")


# ── 2: Personal-Tab HTML vor Jahresvergleich einfügen ────────────────────
PERSONAL_HTML = CRLF.join([
    "",
    "<!-- ══════════ TAB: PERSONAL ══════════ -->",
    '<div id="tab-personal" class="hidden">',
    "",
    "  <!-- KPI Row -->",
    '  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">',
    '    <div class="card p-4">',
    '      <div class="kpi-label">Gesamtpersonalkosten</div>',
    '      <div class="kpi-value text-violet-400" id="pers-kpi-gesamt">–</div>',
    '      <div class="note mt-1" id="pers-kpi-gesamt-note"></div>',
    '    </div>',
    '    <div class="card p-4">',
    '      <div class="kpi-label">Beamtenanteil</div>',
    '      <div class="kpi-value text-blue-400" id="pers-kpi-beamte">–</div>',
    '      <div class="note mt-1">Bez\xfcge + Versorgung</div>',
    '    </div>',
    '    <div class="card p-4">',
    '      <div class="kpi-label">Tarifanteil</div>',
    '      <div class="kpi-value text-emerald-400" id="pers-kpi-tarif">–</div>',
    '      <div class="note mt-1">Bez\xfcge + SV + Versorgung</div>',
    '    </div>',
    '    <div class="card p-4">',
    '      <div class="kpi-label">Personalquote</div>',
    '      <div class="kpi-value text-amber-400" id="pers-kpi-quote">–</div>',
    '      <div class="note mt-1">Anteil an Gesamtaufwendungen</div>',
    '    </div>',
    '  </div>',
    "",
    "  <!-- Charts Row -->",
    '  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">',
    '    <div class="card p-5 flex flex-col">',
    '      <div class="section-title">Kostenstruktur</div>',
    '      <div id="chart-pers-donut" class="plotly-chart flex-1" style="min-height:300px"></div>',
    '    </div>',
    '    <div class="card p-5 flex flex-col">',
    '      <div class="section-title">Personalkosten je Teilplan</div>',
    '      <div id="chart-pers-tp" class="plotly-chart flex-1" style="min-height:300px"></div>',
    '    </div>',
    '  </div>',
    "",
    "  <!-- Zeitreihe -->",
    '  <div class="card p-5 mb-6">',
    '    <div class="section-title">Entwicklung 2023 → 2025</div>',
    '    <div id="chart-pers-trend" class="plotly-chart" style="height:280px"></div>',
    '  </div>',
    "",
    "  <!-- Detail-Tabelle -->",
    '  <div class="card p-5">',
    '    <div class="section-title mb-3">Personalkosten nach Teilplan &amp; Kostenart</div>',
    '    <div class="overflow-x-auto">',
    '      <table class="w-full text-sm" id="pers-detail-table">',
    '        <thead></thead>',
    '        <tbody></tbody>',
    '      </table>',
    '    </div>',
    '    <div class="note mt-3">Hinweis: Kopf- und Stellenzahlen aus Stellenpl\xe4nen sind noch nicht integriert (Stufe\xa02).</div>',
    '  </div>',
    "",
    "</div>",
    "",
])

OLD_JV_COMMENT = "<!-- ══════════ TAB: JAHRESVERGLEICH ══════════ -->"
content = apply(
    content,
    OLD_JV_COMMENT,
    PERSONAL_HTML + OLD_JV_COMMENT,
    "Personal-Tab HTML"
)


# ── 3: setupTabs() — "personal" zur TABS-Liste hinzufügen ─────────────────
OLD_TABS_ARR = 'const TABS = ["overview", "details", "jahresvergleich", "zeitreihe", "simulator"];'
NEW_TABS_ARR = 'const TABS = ["overview", "details", "personal", "jahresvergleich", "zeitreihe", "simulator"];'
content = apply(content, OLD_TABS_ARR, NEW_TABS_ARR, "setupTabs TABS-Array")

OLD_TABS_DETAIL = '      if (name === "details") renderDetailProdukte();'
NEW_TABS_DETAIL = (
    '      if (name === "details") renderDetailProdukte();' + CRLF +
    '      if (name === "personal") renderPersonal();'
)
content = apply(content, OLD_TABS_DETAIL, NEW_TABS_DETAIL, "setupTabs personal-Zweig")


# ── 4: switchYear() — renderPersonal() aufrufen ───────────────────────────
OLD_SWITCH_DETAIL = '  if (DATA.details_tp) renderDetailProdukte();'
NEW_SWITCH_DETAIL = (
    '  if (DATA.details_tp) renderDetailProdukte();' + CRLF +
    '  if (DATA.personal) renderPersonal();'
)
content = apply(content, OLD_SWITCH_DETAIL, NEW_SWITCH_DETAIL, "switchYear renderPersonal")


# ── 5: init() — initPersonal() aufrufen ───────────────────────────────────
OLD_INIT_SETUP = '  setupTabs();'
NEW_INIT_SETUP = '  initPersonal();' + CRLF + '  setupTabs();'
content = apply(content, OLD_INIT_SETUP, NEW_INIT_SETUP, "init() initPersonal")


# ── 6: JS-Funktion renderPersonal() vor setupTabs() einfügen ─────────────
PERSONAL_JS = CRLF.join([
    "",
    "// ── PERSONAL ────────────────────────────────────────────────────────────────────────────",
    "function initPersonal() { /* nothing to init yet */ }",
    "",
    "function renderPersonal() {",
    "  const P = DATA.personal;",
    "  if (!P) return;",
    "  const yr = String(activeJahr);",
    "  const y = P.by_year[yr] || P.by_year[\"2025\"];",
    "  const gruppen = P.gruppen_labels;",
    "  const keys = Object.keys(gruppen);",
    "",
    "  // KPIs",
    "  document.getElementById(\"pers-kpi-gesamt\").textContent = fmtMio(y.gesamt);",
    "  document.getElementById(\"pers-kpi-gesamt-note\").textContent = \"Ansatz \" + yr;",
    "  const beamteSum = (y.bez_beamte || 0) + (y.vers_beamte || 0);",
    "  const tarifSum  = (y.bez_tarif  || 0) + (y.vers_tarif  || 0) + (y.sv || 0);",
    "  document.getElementById(\"pers-kpi-beamte\").textContent = fmt(beamteSum / y.gesamt * 100, 1) + \" %\";",
    "  document.getElementById(\"pers-kpi-tarif\").textContent  = fmt(tarifSum  / y.gesamt * 100, 1) + \" %\";",
    "  const ydMeta = getYD() && getYD().meta;",
    "  const quote = ydMeta && ydMeta.aufwendungen_kk5 ? y.gesamt / ydMeta.aufwendungen_kk5 * 100 : null;",
    "  document.getElementById(\"pers-kpi-quote\").textContent = quote !== null ? fmt(quote, 1) + \" %\" : \"–\";",
    "",
    "  // Farben",
    "  const barColors = {",
    "    bez_beamte:  \"#818cf8\", vers_beamte: \"#a78bfa\",",
    "    bez_tarif:   \"#34d399\", vers_tarif:  \"#6ee7b7\",",
    "    sv:          \"#fb923c\", beihilfen:   \"#f472b6\",",
    "    sonstiges:   \"#94a3b8\",",
    "  };",
    "",
    "  // Donut: Kostenstruktur",
    "  Plotly.newPlot(\"chart-pers-donut\", [{",
    "    type: \"pie\", hole: 0.55,",
    "    labels: keys.map(k => gruppen[k]),",
    "    values: keys.map(k => y[k] || 0),",
    "    marker: { colors: keys.map(k => barColors[k] || \"#94a3b8\") },",
    "    textinfo: \"label+percent\", textposition: \"outside\",",
    "    hovertemplate: \"<b>%{label}</b><br>%{value:,.0f} €<br>%{percent}<extra></extra>\",",
    "  }], {",
    "    paper_bgcolor: \"transparent\", plot_bgcolor: \"transparent\",",
    "    font: { color: \"#94a3b8\", size: 11 }, showlegend: false,",
    "    margin: { l: 20, r: 20, t: 20, b: 20 },",
    "  }, { responsive: true, displayModeBar: false });",
    "",
    "  // Stacked horizontal bar: Personalkosten je TP",
    "  const nach_tp = y.nach_tp || {};",
    "  const tpKeys  = Object.keys(nach_tp).sort();",
    "  const tpNames = tpKeys.map(k => nach_tp[k].name || (\"TP\" + k));",
    "  const tpTraces = keys.map(k => ({",
    "    type: \"bar\", orientation: \"h\",",
    "    name: gruppen[k],",
    "    x: tpKeys.map(tp => nach_tp[tp][k] || 0),",
    "    y: tpNames,",
    "    marker: { color: barColors[k] || \"#94a3b8\" },",
    "    hovertemplate: \"<b>%{y}</b><br>\" + gruppen[k] + \": %{x:,.0f} €<extra></extra>\",",
    "  }));",
    "  Plotly.newPlot(\"chart-pers-tp\", tpTraces, {",
    "    barmode: \"stack\",",
    "    paper_bgcolor: \"transparent\", plot_bgcolor: \"transparent\",",
    "    font: { color: \"#94a3b8\", size: 11 },",
    "    xaxis: { tickformat: \",.0f\", color: \"#94a3b8\", gridcolor: \"#334155\", title: { text: \"EUR\", font: { size: 10 } } },",
    "    yaxis: { color: \"#94a3b8\", automargin: true },",
    "    legend: { font: { size: 10, color: \"#94a3b8\" }, orientation: \"h\", y: -0.12 },",
    "    margin: { l: 10, r: 10, t: 10, b: 60 },",
    "  }, { responsive: true, displayModeBar: false });",
    "",
    "  // Trend-Chart (immer 2023–2025)",
    "  const tYears = [\"2023\", \"2024\", \"2025\"];",
    "  const trendTraces = keys.map(k => ({",
    "    type: \"bar\",",
    "    name: gruppen[k],",
    "    x: tYears,",
    "    y: tYears.map(y2 => (P.by_year[y2] || {})[k] || 0),",
    "    marker: { color: barColors[k] || \"#94a3b8\" },",
    "    hovertemplate: \"<b>\" + gruppen[k] + \"</b><br>%{x}: %{y:,.0f} €<extra></extra>\",",
    "  }));",
    "  Plotly.newPlot(\"chart-pers-trend\", trendTraces, {",
    "    barmode: \"stack\",",
    "    paper_bgcolor: \"transparent\", plot_bgcolor: \"transparent\",",
    "    font: { color: \"#94a3b8\", size: 11 },",
    "    xaxis: { color: \"#94a3b8\" },",
    "    yaxis: { tickformat: \",.0f\", color: \"#94a3b8\", gridcolor: \"#334155\" },",
    "    legend: { font: { size: 10, color: \"#94a3b8\" }, orientation: \"h\", y: -0.22 },",
    "    margin: { l: 10, r: 10, t: 10, b: 100 },",
    "  }, { responsive: true, displayModeBar: false });",
    "",
    "  // Detail-Tabelle",
    "  const thead = document.querySelector(\"#pers-detail-table thead\");",
    "  const tbody = document.querySelector(\"#pers-detail-table tbody\");",
    "  const thCells = keys.map(k => `<th class=\"pr-3 py-2 font-medium text-right\" style=\"white-space:nowrap\">${gruppen[k].replace(\" & \",\"&amp;\")}</th>`).join(\"\");",
    "  thead.innerHTML = `<tr class=\"text-left text-slate-400 text-xs border-b border-slate-700\">",
    "    <th class=\"pr-4 py-2 font-medium\">Teilplan</th>${thCells}",
    "    <th class=\"py-2 font-medium text-right\">Gesamt</th></tr>`;",
    "",
    "  const rows = tpKeys.map(tp => {",
    "    const d = nach_tp[tp];",
    "    const cells = keys.map(k => `<td class=\"pr-3 py-1.5 text-right text-slate-300\">${(d[k]||0) > 0 ? fmtMio(d[k]) : \"<span class=\\\"text-slate-600\\\">–</span>\"}</td>`).join(\"\");",
    "    return `<tr class=\"border-b border-slate-800 hover:bg-slate-800/40\">",
    "      <td class=\"pr-4 py-1.5 text-slate-300 whitespace-nowrap\"><span class=\"text-xs text-slate-500 mr-1\">TP${tp}</span>${d.name}</td>",
    "      ${cells}",
    "      <td class=\"py-1.5 text-right font-semibold text-violet-300\">${fmtMio(d.gesamt)}</td>",
    "    </tr>`;",
    "  });",
    "  const totalCells = keys.map(k => `<td class=\"pr-3 py-2 text-right font-semibold text-slate-100\">${fmtMio(y[k] || 0)}</td>`).join(\"\");",
    "  rows.push(`<tr class=\"bg-slate-800/60 border-t border-slate-600\">",
    "    <td class=\"pr-4 py-2 font-bold text-slate-100\">Gesamt</td>",
    "    ${totalCells}",
    "    <td class=\"py-2 text-right font-bold text-violet-300\">${fmtMio(y.gesamt)}</td>",
    "  </tr>`);",
    "  tbody.innerHTML = rows.join(\"\");",
    "}",
    "",
])

OLD_SETUP_TABS = "function setupTabs() {"
content = apply(content, OLD_SETUP_TABS, PERSONAL_JS + OLD_SETUP_TABS, "renderPersonal() JS")


# ── Schreiben ─────────────────────────────────────────────────────────────
with open(path, "wb") as f:
    f.write(content.encode("utf-8"))

print(f"\nFertig! {path} geschrieben.")
