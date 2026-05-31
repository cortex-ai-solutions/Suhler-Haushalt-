"""
Patch: HSK-Subtab (Haushaltssicherungskonzept) in index.html einbinden.
- Tab-Button nach Personal
- Tab-HTML vor Jahresvergleich
- TABS-Array + switchTabs + init() aktualisieren
- renderHsk() und initHsk() einbinden
CRLF-sicher (Windows line endings in index.html).
"""

path = "index.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

CRLF = "\r\n"


def apply(c, old, new, label):
    if old not in c:
        raise ValueError(f"NICHT GEFUNDEN: {label!r}\n  Suchstring: {old!r:.120}")
    print(f"  [OK] {label}")
    return c.replace(old, new, 1)


# ── 1: Tab-Button ──────────────────────────────────────────────────────────
OLD_TAB_BTN = (
    '  <div class="tab" data-tab="personal">Personal</div>' + CRLF +
    '  <div class="tab" data-tab="jahresvergleich">Jahresvergleich</div>'
)
NEW_TAB_BTN = (
    '  <div class="tab" data-tab="personal">Personal</div>' + CRLF +
    '  <div class="tab" data-tab="hsk">HSK</div>' + CRLF +
    '  <div class="tab" data-tab="jahresvergleich">Jahresvergleich</div>'
)
content = apply(content, OLD_TAB_BTN, NEW_TAB_BTN, "Tab-Button HSK")


# ── 2: Tab-HTML ────────────────────────────────────────────────────────────
OLD_BEFORE_JV = (
    '<!-- ══════════ TAB: JAHRESVERGLEICH ══════════ -->'
)

HSK_HTML = CRLF.join([
    '<!-- ══════════ TAB: HSK ══════════ -->',
    '<div id="tab-hsk" class="hidden">',
    '',
    '  <!-- KPI-Chips -->',
    '  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">',
    '    <div class="card p-4">',
    '      <div class="kpi-label">Maßnahmen gesamt</div>',
    '      <div class="kpi-value text-slate-200" id="hsk-kpi-n">–</div>',
    '      <div class="note mt-1">davon <span id="hsk-kpi-aktiv" class="text-blue-400"></span> aktiv</div>',
    '    </div>',
    '    <div class="card p-4">',
    '      <div class="kpi-label">Konsolidiert 2013–2022</div>',
    '      <div class="kpi-value text-emerald-300" id="hsk-kpi-kumulativ">–</div>',
    '      <div class="note mt-1">kumulierter Konsolidierungseffekt</div>',
    '    </div>',
    '    <div class="card p-4">',
    '      <div class="kpi-label">Aktives Potenzial 2024</div>',
    '      <div class="kpi-value text-violet-300" id="hsk-kpi-2024">–</div>',
    '      <div class="note mt-1">laufende Maßnahmen Plan 2024</div>',
    '    </div>',
    '    <div class="card p-4">',
    '      <div class="kpi-label">Aktives Potenzial 2025</div>',
    '      <div class="kpi-value text-violet-300" id="hsk-kpi-2025">–</div>',
    '      <div class="note mt-1">laufende Maßnahmen Plan 2025</div>',
    '    </div>',
    '  </div>',
    '',
    '  <!-- Schmerzskala -->',
    '  <div class="card p-5 mb-6">',
    '    <div class="flex items-center justify-between mb-2">',
    '      <div class="section-title">Konsolidierungs-Fortschritt (Schmerzskala)</div>',
    '      <div class="text-xs text-slate-400" id="hsk-schmerz-label"></div>',
    '    </div>',
    '    <div class="w-full bg-slate-700 rounded-full h-4 overflow-hidden mb-2">',
    '      <div id="hsk-schmerz-bar" class="h-4 rounded-full transition-all duration-500"',
    '           style="width:0%;background:linear-gradient(90deg,#34d399,#f59e0b,#f87171)"></div>',
    '    </div>',
    '    <div class="flex justify-between text-xs text-slate-500 mt-1">',
    '      <span>0 €</span>',
    '      <span id="hsk-schmerz-ziel"></span>',
    '    </div>',
    '    <p class="text-xs text-slate-400 mt-3" id="hsk-schmerz-text"></p>',
    '  </div>',
    '',
    '  <!-- Charts -->',
    '  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">',
    '    <div class="card p-5 flex flex-col lg:col-span-2">',
    '      <div class="section-title mb-1">Kumulativer Konsolidierungseffekt 2013–2025</div>',
    '      <div class="note mb-2">Jährlich umgesetzter Betrag aller Maßnahmen (Einnahmen + / Ausgabenersparnisse +)</div>',
    '      <div id="chart-hsk-timeline" class="plotly-chart flex-1" style="min-height:260px"></div>',
    '    </div>',
    '    <div class="card p-5 flex flex-col">',
    '      <div class="section-title mb-1">Maßnahmen nach Kategorie</div>',
    '      <div id="chart-hsk-donut" class="plotly-chart flex-1" style="min-height:260px"></div>',
    '    </div>',
    '  </div>',
    '',
    '  <!-- Filter + Tabelle -->',
    '  <div class="card p-5">',
    '    <div class="flex flex-wrap items-center gap-3 mb-4">',
    '      <div class="section-title flex-1">Maßnahmen-Katalog</div>',
    '      <div class="flex gap-2" id="hsk-filter-btns">',
    '        <button onclick="setHskFilter(\'alle\')"',
    '          class="hsk-filter-btn px-3 py-1 rounded-full text-xs border border-slate-600 text-slate-300 active"',
    '          data-filter="alle">Alle</button>',
    '        <button onclick="setHskFilter(\'aktiv\')"',
    '          class="hsk-filter-btn px-3 py-1 rounded-full text-xs border border-slate-600 text-slate-400"',
    '          data-filter="aktiv">Aktiv</button>',
    '        <button onclick="setHskFilter(\'erledigt\')"',
    '          class="hsk-filter-btn px-3 py-1 rounded-full text-xs border border-slate-600 text-slate-400"',
    '          data-filter="erledigt">Erledigt</button>',
    '        <button onclick="setHskFilter(\'entfallen\')"',
    '          class="hsk-filter-btn px-3 py-1 rounded-full text-xs border border-slate-600 text-slate-400"',
    '          data-filter="entfallen">Entfallen</button>',
    '      </div>',
    '      <input id="hsk-search" type="text" placeholder="Maßnahme suchen…"',
    '        class="bg-slate-800 border border-slate-600 rounded px-3 py-1 text-xs text-slate-300',
    '               placeholder:text-slate-500 focus:outline-none focus:border-slate-400 w-48"',
    '        oninput="renderHskTable()">',
    '    </div>',
    '    <div class="overflow-x-auto">',
    '      <table class="w-full text-sm" id="hsk-tabelle">',
    '        <thead>',
    '          <tr class="text-left text-slate-400 text-xs border-b border-slate-700">',
    '            <th class="py-2 pr-3 font-medium w-10">Nr.</th>',
    '            <th class="py-2 pr-3 font-medium">Maßnahme</th>',
    '            <th class="py-2 pr-3 font-medium w-24">Kategorie</th>',
    '            <th class="py-2 pr-3 font-medium text-right w-32">Kumulativ<br><span class="text-slate-500">2013–2022</span></th>',
    '            <th class="py-2 pr-3 font-medium text-right w-24">2024</th>',
    '            <th class="py-2 pr-3 font-medium text-right w-24">2025</th>',
    '            <th class="py-2 font-medium w-24">Status</th>',
    '          </tr>',
    '        </thead>',
    '        <tbody id="hsk-tabelle-body"></tbody>',
    '      </table>',
    '    </div>',
    '  </div>',
    '',
    '</div>',
    '',
    '<!-- ══════════ TAB: JAHRESVERGLEICH ══════════ -->',
])

content = apply(content, OLD_BEFORE_JV, HSK_HTML, "HSK Tab-HTML")


# ── 3: TABS-Array ──────────────────────────────────────────────────────────
OLD_TABS = '"overview", "details", "personal", "jahresvergleich", "zeitreihe", "simulator"'
NEW_TABS = '"overview", "details", "personal", "hsk", "jahresvergleich", "zeitreihe", "simulator"'
content = apply(content, OLD_TABS, NEW_TABS, "TABS-Array")


# ── 4: Tab-Switch → renderHsk beim ersten Aufruf ───────────────────────────
OLD_SWITCH = 'if (name === "zeitreihe") renderZeitreihe();'
NEW_SWITCH = (
    'if (name === "zeitreihe") renderZeitreihe();' + CRLF +
    '      if (name === "hsk") renderHsk();'
)
content = apply(content, OLD_SWITCH, NEW_SWITCH, "Tab-Switch renderHsk")


# ── 5: init() → initHsk() aufrufen ─────────────────────────────────────────
OLD_INIT_CALL = 'initPersonal();'
NEW_INIT_CALL = 'initPersonal();' + CRLF + '  initHsk();'
content = apply(content, OLD_INIT_CALL, NEW_INIT_CALL, "init() initHsk-Call")


# ── 6: JS-Funktionen ───────────────────────────────────────────────────────
# Vor setupTabs() einfügen
OLD_SETUP_TABS = 'function setupTabs() {'

HSK_JS = CRLF.join([
    '// ── HSK ─────────────────────────────────────────────────────────────────────',
    'let _hskRendered = false;',
    'let _hskFilter = "alle";',
    '',
    'function initHsk() {',
    '  const el = document.getElementById("tab-hsk");',
    '  if (el) el.classList.toggle("hidden", !DATA.hsk);',
    '}',
    '',
    'function setHskFilter(f) {',
    '  _hskFilter = f;',
    '  document.querySelectorAll(".hsk-filter-btn").forEach(b => {',
    '    const isActive = b.dataset.filter === f;',
    '    b.classList.toggle("active", isActive);',
    '    b.classList.toggle("text-white", isActive);',
    '    b.classList.toggle("border-blue-500", isActive);',
    '    b.classList.toggle("text-slate-300", isActive);',
    '    b.classList.toggle("text-slate-400", !isActive);',
    '    b.classList.toggle("border-slate-600", !isActive);',
    '  });',
    '  renderHskTable();',
    '}',
    '',
    'function renderHsk() {',
    '  const HSK = DATA.hsk;',
    '  if (!HSK) return;',
    '  if (_hskRendered) return;',
    '  _hskRendered = true;',
    '',
    '  const meta = HSK.meta;',
    '  const fmtM = v => fmt(Math.abs(v)/1e6, 3) + " Mio. €";',
    '  const fmtT = v => fmt(v/1000, 0) + " T€";',
    '',
    '  // KPI-Chips',
    '  setText("hsk-kpi-n", meta.n_massnahmen);',
    '  setText("hsk-kpi-aktiv", meta.n_aktiv);',
    '  setText("hsk-kpi-kumulativ", fmtM(meta.gesamt_kumulativ_2013_2022));',
    '  setText("hsk-kpi-2024", fmtT(meta.gesamt_2024));',
    '  setText("hsk-kpi-2025", fmtT(meta.gesamt_2025));',
    '',
    '  // Schmerzskala',
    '  const ziel = meta.gesamt_total;',
    '  const ist  = meta.gesamt_kumulativ_2013_2022;',
    '  const pct  = ziel > 0 ? Math.min(100, ist / ziel * 100) : 0;',
    '  const bar = document.getElementById("hsk-schmerz-bar");',
    '  if (bar) bar.style.width = pct.toFixed(1) + "%";',
    '  setText("hsk-schmerz-label", pct.toFixed(1) + "% des Gesamtziels erreicht");',
    '  setText("hsk-schmerz-ziel", fmtM(ziel) + " Gesamtziel");',
    '  setText("hsk-schmerz-text",',
    '    "Seit 2013 hat die Stadt Suhl durch " + meta.n_massnahmen + " Konsolidierungsmaßnahmen " +',
    '    fmtM(ist) + " eingespart bzw. zusätzlich eingenommen (Stand: vorl. RE 2022). " +',
    '    "Das entspricht " + pct.toFixed(1) + " % des gesamten Konsolidierungsziels von " + fmtM(ziel) + "."',
    '  );',
    '',
    '  // Chart: Kumulativ-Timeline',
    '  const tl = HSK.kumulativ_timeline;',
    '  const tlYears = Object.keys(tl).sort();',
    '  const tlVals  = tlYears.map(y => tl[y]);',
    '  // Kumulierte Summe berechnen',
    '  let cumSum = 0;',
    '  const cumVals = tlVals.map(v => { cumSum += v; return cumSum; });',
    '  Plotly.newPlot("chart-hsk-timeline", [',
    '    {',
    '      type: "bar", name: "Jährlich",',
    '      x: tlYears, y: tlVals,',
    '      customdata: tlVals.map(v => fmt(v/1000,0) + " T€"),',
    '      hovertemplate: "%{x}: %{customdata}<extra></extra>",',
    '      marker: { color: "#60a5fa" }, opacity: 0.6,',
    '    },',
    '    {',
    '      type: "scatter", name: "Kumuliert", mode: "lines+markers",',
    '      x: tlYears, y: cumVals,',
    '      customdata: cumVals.map(v => fmt(v/1e6,3) + " Mio. €"),',
    '      hovertemplate: "%{x} kum.: %{customdata}<extra></extra>",',
    '      line: { color: "#34d399", width: 2 }, yaxis: "y2",',
    '      marker: { size: 4 },',
    '    }',
    '  ], {',
    '    paper_bgcolor: "transparent", plot_bgcolor: "transparent",',
    '    font: { color: "#94a3b8", size: 11 },',
    '    xaxis: { color: "#94a3b8" },',
    '    yaxis:  { color: "#94a3b8", gridcolor: "#334155", title: { text: "Jährlich (€)", font:{size:10} } },',
    '    yaxis2: { color: "#34d399", overlaying: "y", side: "right",',
    '              title: { text: "Kumuliert (€)", font:{size:10}, standoff:8 } },',
    '    legend: { font:{size:10,color:"#94a3b8"}, orientation:"h", y:-0.2 },',
    '    margin: { l:10, r:10, t:10, b:60 },',
    '    barmode: "relative",',
    '  }, { responsive:true, displayModeBar:false });',
    '',
    '  // Chart: Donut Kategorie',
    '  const katLabels = ["ERTRAG", "AUFWAND", "PERSONAL"];',
    '  const katColors = ["#34d399", "#f59e0b", "#818cf8"];',
    '  const katVals   = katLabels.map(k =>',
    '    HSK.massnahmen.filter(m => m.kategorie === k && m.betrag_gesamt > 0)',
    '                  .reduce((s,m) => s + m.betrag_gesamt, 0)',
    '  );',
    '  Plotly.newPlot("chart-hsk-donut", [{',
    '    type: "pie", hole: 0.55,',
    '    labels: ["Ertragssteigerung", "Aufwandsreduzierung", "Personalmaßnahmen"],',
    '    values: katVals,',
    '    customdata: katVals.map(v => fmt(v/1e6,3) + " Mio. €"),',
    '    hovertemplate: "%{label}<br>%{customdata}<extra></extra>",',
    '    marker: { colors: katColors },',
    '    textinfo: "label+percent",',
    '    textfont: { size: 10, color: "#94a3b8" },',
    '    insidetextorientation: "radial",',
    '  }], {',
    '    paper_bgcolor: "transparent",',
    '    font: { color: "#94a3b8", size: 10 },',
    '    showlegend: false,',
    '    margin: { l:10, r:10, t:10, b:10 },',
    '  }, { responsive:true, displayModeBar:false });',
    '',
    '  renderHskTable();',
    '}',
    '',
    'function renderHskTable() {',
    '  const HSK = DATA.hsk;',
    '  if (!HSK) return;',
    '',
    '  const query = (document.getElementById("hsk-search")?.value || "").toLowerCase();',
    '  const fmtE = v => v === 0 ? \'<span class="text-slate-600">–</span>\' :',
    '    \'<span class="\' + (v > 0 ? "text-emerald-400" : "text-rose-400") + \'">\' +',
    '    (v > 0 ? "+" : "") + fmt(v/1000, 0) + " T€</span>";',
    '',
    '  const KAT_COLOR = {',
    '    ERTRAG:    "text-emerald-300 bg-emerald-900/30",',
    '    AUFWAND:   "text-amber-300   bg-amber-900/30",',
    '    PERSONAL:  "text-violet-300  bg-violet-900/30",',
    '  };',
    '  const STATUS_COLOR = {',
    '    aktiv:     "text-blue-300    bg-blue-900/30",',
    '    erledigt:  "text-slate-400   bg-slate-800",',
    '    entfallen: "text-rose-400    bg-rose-900/30",',
    '    geprueft:  "text-yellow-300  bg-yellow-900/30",',
    '  };',
    '  const KAT_LABEL    = { ERTRAG:"Ertrag", AUFWAND:"Aufwand", PERSONAL:"Personal" };',
    '  const STATUS_LABEL = { aktiv:"aktiv", erledigt:"erledigt", entfallen:"entfallen", geprueft:"geprüft" };',
    '',
    '  const filtered = HSK.massnahmen.filter(m => {',
    '    if (_hskFilter !== "alle" && m.status !== _hskFilter) return false;',
    '    if (query && !(m.bezeichnung.toLowerCase().includes(query) ||',
    '                   m.nr.includes(query))) return false;',
    '    return true;',
    '  });',
    '',
    '  const rows = filtered.map(m => {',
    '    const kc = KAT_COLOR[m.kategorie]    || "text-slate-300";',
    '    const sc = STATUS_COLOR[m.status]    || "text-slate-400";',
    '    const prodLinks = m.produkte.length',
    '      ? m.produkte.map(p => `<span class="text-xs font-mono text-slate-500">${p}</span>`).join(" ")',
    '      : "";',
    '    return `<tr class="border-b border-slate-800 hover:bg-slate-800/40 cursor-pointer"',
    '                onclick="toggleHskRow(this,${m.id})">',
    '      <td class="py-2 pr-3 text-slate-400 font-mono text-xs">${m.nr}</td>',
    '      <td class="py-2 pr-3">',
    '        <div class="text-slate-200 text-sm">${m.bezeichnung}</div>',
    '        <div class="mt-0.5">${prodLinks}</div>',
    '      </td>',
    '      <td class="py-2 pr-3">',
    '        <span class="text-xs px-1.5 py-0.5 rounded ${kc}">${KAT_LABEL[m.kategorie]||m.kategorie}</span>',
    '      </td>',
    '      <td class="py-2 pr-3 text-right font-mono text-xs">${fmtE(m.betrag_kumulativ)}</td>',
    '      <td class="py-2 pr-3 text-right font-mono text-xs">${fmtE(m.betrag_2024)}</td>',
    '      <td class="py-2 pr-3 text-right font-mono text-xs">${fmtE(m.betrag_2025)}</td>',
    '      <td class="py-2">',
    '        <span class="text-xs px-1.5 py-0.5 rounded ${sc}">${STATUS_LABEL[m.status]||m.status}</span>',
    '      </td>',
    '    </tr>`,',
    '    `<tr id="hsk-detail-${m.id}" class="hidden bg-slate-900/50">',
    '      <td colspan="7" class="px-4 py-3">',
    '        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 text-xs text-slate-300">',
    '          <div class="lg:col-span-2">',
    '            <div class="font-medium text-slate-200 mb-1">Maßnahmen-Beschreibung</div>',
    '            <p class="text-slate-400 leading-relaxed">${m.beschreibung || "Keine weitere Beschreibung."}</p>',
    '          </div>',
    '          <div>',
    '            <div class="font-medium text-slate-200 mb-2">Jahresverlauf (umgesetzter Betrag)</div>',
    '            <div id="hsk-jw-${m.id}" class="space-y-0.5">',
    '              ${buildHskJahreswerte(m)}',
    '            </div>',
    '          </div>',
    '        </div>',
    '      </td>',
    '    </tr>`',
    '  );',
    '  document.getElementById("hsk-tabelle-body").innerHTML = rows.flat().join("");',
    '}',
    '',
    'function buildHskJahreswerte(m) {',
    '  const years = ["2013","2014","2015","2016","2017","2018","2019","2020","2021","2022","2023","2024","2025"];',
    '  const active = years.filter(y => (m.jahreswerte[y]||0) !== 0);',
    '  if (!active.length) return \'<span class="text-slate-500 text-xs">Keine Jahreswerte</span>\';',
    '  return active.map(y => {',
    '    const v = m.jahreswerte[y] || 0;',
    '    const col = v > 0 ? "text-emerald-400" : "text-rose-400";',
    '    const sign = v > 0 ? "+" : "";',
    '    return `<div class="flex justify-between text-xs">` +',
    '      `<span class="text-slate-400">${y}</span>` +',
    '      `<span class="font-mono ${col}">${sign}${fmt(v/1000,0)} T€</span>` +',
    '      "</div>";',
    '  }).join("");',
    '}',
    '',
    'function toggleHskRow(tr, id) {',
    '  const detail = document.getElementById("hsk-detail-" + id);',
    '  if (!detail) return;',
    '  const isOpen = !detail.classList.contains("hidden");',
    '  // Alle anderen schließen',
    '  document.querySelectorAll("[id^=hsk-detail-]").forEach(el => el.classList.add("hidden"));',
    '  if (!isOpen) detail.classList.remove("hidden");',
    '}',
    '',
    'function setText(id, val) {',
    '  const el = document.getElementById(id);',
    '  if (el) el.textContent = val;',
    '}',
    '',
    'function setupTabs() {',
])

content = apply(content, OLD_SETUP_TABS, HSK_JS, "HSK JS-Funktionen")

with open(path, "wb") as f:
    f.write(content.encode("utf-8"))

print(f"\nFertig! {path}")
