"""
Patch-Skript: Stellenplan-Abschnitt in Personal-Tab + JS einbinden.
CRLF-aware (Windows index.html).
"""

path = "index.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

CRLF = "\r\n"


def apply(c, old, new, label):
    if old not in c:
        raise ValueError(f"NICHT GEFUNDEN: {label!r}")
    c2 = c.replace(old, new, 1)
    print(f"  [OK] {label}")
    return c2


# ── 1: Hinweis-Notiz ersetzen + Stellenplan-HTML darunter ─────────────────
OLD_NOTE = (
    '    <div class="note mt-3">Hinweis: Kopf- und Stellenzahlen aus Stellenplänen'
    ' sind noch nicht integriert (Stufe 2).</div>' + CRLF +
    '  </div>' + CRLF +
    '' + CRLF +
    '</div>'
)

STELLENPLAN_HTML = CRLF.join([
    '  </div>',
    '',
    '  <!-- Stellenplan -->',
    '  <div id="pers-stellenplan" class="hidden">',
    '',
    '    <!-- Stellen-KPI-Chips -->',
    '    <div class="grid grid-cols-3 gap-4 mb-6">',
    '      <div class="card p-4">',
    '        <div class="kpi-label">Planstellen gesamt</div>',
    '        <div class="kpi-value text-violet-300" id="sp-kpi-gesamt">–</div>',
    '        <div class="note mt-1" id="sp-kpi-gesamt-note"></div>',
    '      </div>',
    '      <div class="card p-4">',
    '        <div class="kpi-label">davon Beamte</div>',
    '        <div class="kpi-value text-blue-300" id="sp-kpi-beamte">–</div>',
    '        <div class="note mt-1" id="sp-kpi-beamte-pct"></div>',
    '      </div>',
    '      <div class="card p-4">',
    '        <div class="kpi-label">davon Tarifbeschäftigte</div>',
    '        <div class="kpi-value text-emerald-300" id="sp-kpi-tarif">–</div>',
    '        <div class="note mt-1" id="sp-kpi-tarif-pct"></div>',
    '      </div>',
    '    </div>',
    '',
    '    <!-- Charts -->',
    '    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">',
    '      <div class="card p-5 flex flex-col">',
    '        <div class="section-title">Stellen je Besoldungs-/Entgeltgruppe</div>',
    '        <div id="chart-sp-gruppen" class="plotly-chart flex-1" style="min-height:400px"></div>',
    '      </div>',
    '      <div class="card p-5 flex flex-col">',
    '        <div class="section-title">Stellen je Teilplan — 2024 vs. 2025</div>',
    '        <div id="chart-sp-tp" class="plotly-chart flex-1" style="min-height:400px"></div>',
    '      </div>',
    '    </div>',
    '',
    '  </div>',
    '',
    '</div>',
])

content = apply(content, OLD_NOTE, STELLENPLAN_HTML, "Stellenplan-HTML im Personal-Tab")


# ── 2: initPersonal: stellenplan-Div ein-/ausblenden ─────────────────────
OLD_INIT = "function initPersonal() { /* nothing to init yet */ }"
NEW_INIT = CRLF.join([
    "function initPersonal() {",
    "  const sp = DATA && DATA.personal && DATA.personal.stellenplan;",
    "  const el = document.getElementById('pers-stellenplan');",
    "  if (el) el.classList.toggle('hidden', !sp);",
    "}",
])
content = apply(content, OLD_INIT, NEW_INIT, "initPersonal() Stellenplan-Toggle")


# ── 3: renderPersonal(): Stellenplan-Charts am Ende der Funktion ──────────
OLD_RENDER_END = '  tbody.innerHTML = rows.join("");' + CRLF + '}'
NEW_RENDER_END = CRLF.join([
    '  tbody.innerHTML = rows.join("");',
    '',
    '  // Stellenplan',
    '  const SP = DATA.personal.stellenplan;',
    '  if (!SP) return;',
    '  const spKey = yr + "_PLAN_ANSATZ";',
    '  const sp = SP.by_year[spKey] || SP.by_year["2025_PLAN_ANSATZ"];',
    '  if (!sp) return;',
    '',
    '  // Stellen-KPIs',
    '  document.getElementById("sp-kpi-gesamt").textContent = fmt(sp.gesamt, 3);',
    '  document.getElementById("sp-kpi-gesamt-note").textContent = "Plan " + yr;',
    '  document.getElementById("sp-kpi-beamte").textContent = fmt(sp.beamte, 3);',
    '  document.getElementById("sp-kpi-beamte-pct").textContent = fmt(sp.beamte/sp.gesamt*100,1) + " %";',
    '  document.getElementById("sp-kpi-tarif").textContent  = fmt(sp.tarif, 3);',
    '  document.getElementById("sp-kpi-tarif-pct").textContent  = fmt(sp.tarif/sp.gesamt*100,1) + " %";',
    '',
    '  // Chart: Stellen je Besoldungsgruppe',
    '  const ng = sp.nach_gruppe || {};',
    '  const beamteKeys = Object.keys(ng).filter(k => ng[k].typ === "BEAMTE").sort((a,b) => ng[b].planstellen-ng[a].planstellen);',
    '  const tarifKeys  = Object.keys(ng).filter(k => ng[k].typ === "TARIF").sort((a,b) => ng[b].planstellen-ng[a].planstellen);',
    '  const allKeys = [...beamteKeys, ...tarifKeys];',
    '  const beamteColors = allKeys.map(k => ng[k].typ === "BEAMTE" ? "#818cf8" : "#34d399");',
    '  Plotly.newPlot("chart-sp-gruppen", [{',
    '    type: "bar", orientation: "h",',
    '    x: allKeys.map(k => ng[k].planstellen),',
    '    y: allKeys,',
    '    marker: { color: beamteColors },',
    '    hovertemplate: "<b>%{y}</b>: %{x:.3f} Stellen<extra></extra>",',
    '  }], {',
    '    paper_bgcolor: "transparent", plot_bgcolor: "transparent",',
    '    font: { color: "#94a3b8", size: 11 },',
    '    xaxis: { color: "#94a3b8", gridcolor: "#334155", title: { text: "Planstellen", font:{size:10} } },',
    '    yaxis: { color: "#94a3b8", automargin: true, tickfont: {size: 10} },',
    '    margin: { l: 10, r: 20, t: 10, b: 40 },',
    '    showlegend: false,',
    '  }, { responsive: true, displayModeBar: false });',
    '',
    '  // Chart: Stellen je TP — 2024 vs 2025',
    '  const sp24 = SP.by_year["2024_PLAN_ANSATZ"];',
    '  const sp25 = SP.by_year["2025_PLAN_ANSATZ"];',
    '  const tpNrs = Object.keys((sp25 || sp24 || {}).nach_tp || {}).sort();',
    '  const tpLabels = tpNrs.map(tp => "TP" + tp);',
    '  const spTpTraces = [];',
    '  if (sp24) spTpTraces.push({',
    '    type:"bar", name:"2024 (Soll)", x:tpLabels,',
    '    y: tpNrs.map(tp => (sp24.nach_tp[tp] || {}).gesamt || 0),',
    '    marker:{color:"#60a5fa"}, opacity:0.7,',
    '    hovertemplate:"<b>%{x}</b> 2024: %{y:.3f} Stellen<extra></extra>",',
    '  });',
    '  if (sp25) spTpTraces.push({',
    '    type:"bar", name:"2025 (Plan)", x:tpLabels,',
    '    y: tpNrs.map(tp => (sp25.nach_tp[tp] || {}).gesamt || 0),',
    '    marker:{color:"#818cf8"},',
    '    hovertemplate:"<b>%{x}</b> 2025: %{y:.3f} Stellen<extra></extra>",',
    '  });',
    '  Plotly.newPlot("chart-sp-tp", spTpTraces, {',
    '    barmode: "group",',
    '    paper_bgcolor:"transparent", plot_bgcolor:"transparent",',
    '    font:{color:"#94a3b8",size:11},',
    '    xaxis:{color:"#94a3b8"},',
    '    yaxis:{color:"#94a3b8",gridcolor:"#334155",title:{text:"Planstellen",font:{size:10}}},',
    '    legend:{font:{size:10,color:"#94a3b8"},orientation:"h",y:-0.18},',
    '    margin:{l:10,r:10,t:10,b:70},',
    '  }, { responsive:true, displayModeBar:false });',
    '}',
])
content = apply(content, OLD_RENDER_END, NEW_RENDER_END, "renderPersonal() Stellenplan-Charts")


# ── Schreiben ─────────────────────────────────────────────────────────────
with open(path, "wb") as f:
    f.write(content.encode("utf-8"))

print(f"\nFertig! {path} geschrieben.")
