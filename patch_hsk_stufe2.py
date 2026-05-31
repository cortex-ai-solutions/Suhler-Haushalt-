"""
Patch HSK Stufe 2: Soll/Ist-Abgleich im Dashboard.
Sicherheitshinweise gegenueber vorheriger Version:
- Kein Unicode (Pfeilzeichen etc.) in JS-Strings -> HTML-Entities stattdessen
- Mehrzeilige Ternaries in Template-Literalen vermieden -> Hilfsfunktionen
- Kein direktes Ersetzen von Inline-Template-Literal-Content -> sicherer Ansatz
CRLF-sicher.
"""

path = "index.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

CRLF = "\r\n"


def apply(c, old, new, label):
    if old not in c:
        raise ValueError(f"NICHT GEFUNDEN: {label!r}  (Suche: {old!r:.80})")
    c2 = c.replace(old, new, 1)
    print(f"  [OK] {label}")
    return c2


# ── 1: 5. KPI-Chip "Mit Produktabgleich" ──────────────────────────────────
# Suche das Ende der KPI-Grid (einzigartig: </div> + Leerzeile + Schmerzskala)
OLD_KPI_LAST = (
    '  </div>' + CRLF + CRLF +
    '  <!-- Schmerzskala -->'
)

NEW_KPI_LAST = CRLF.join([
    '    <div class="card p-4 border border-blue-800/40">',
    '      <div class="kpi-label">Mit Produktabgleich</div>',
    '      <div class="kpi-value text-blue-300" id="hsk-kpi-abgleich">–</div>',
    '      <div class="note mt-1">',
    '        <span class="text-emerald-400" id="hsk-kpi-pos"></span> positiv /',
    '        <span class="text-rose-400"    id="hsk-kpi-neg"></span> negativ',
    '      </div>',
    '    </div>',
    '  </div>',
    '',
    '  <!-- Schmerzskala -->',
])


# ── 2: Abgleich-Text unterhalb Schmerzskala ────────────────────────────────
OLD_SCHMERZ_P = (
    '    <p class="text-xs text-slate-400 mt-3" id="hsk-schmerz-text"></p>'
)
NEW_SCHMERZ_P = (
    '    <p class="text-xs text-slate-400 mt-3" id="hsk-schmerz-text"></p>' + CRLF +
    '    <p class="text-xs text-slate-500 mt-1" id="hsk-abgleich-text"></p>'
)


# ── 3: Tabellen-Header Tendenz-Spalte ──────────────────────────────────────
OLD_TH_STATUS = (
    '            <th class="py-2 font-medium w-24">Status</th>'
)
NEW_TH_STATUS = CRLF.join([
    '            <th class="py-2 pr-3 font-medium w-12 text-center" title="Tendenz">&#x21D5;</th>',
    '            <th class="py-2 font-medium w-24">Status</th>',
])


content = apply(content, OLD_KPI_LAST, NEW_KPI_LAST, "KPI-Chip Abgleich")
content = apply(content, OLD_SCHMERZ_P, NEW_SCHMERZ_P, "Schmerzskala Abgleich-Text")
content = apply(content, OLD_TH_STATUS, NEW_TH_STATUS, "TH Tendenz-Spalte")


# ── 4: JS-Erweiterungen (als EINZELNER Block vor setupTabs) ───────────────
OLD_SETUP_TABS = "function setupTabs() {"

# Alle Stufe-2-JS-Erweiterungen in einem einzigen Block
STUFE2_JS = CRLF.join([
    "// ── HSK Stufe 2: Soll/Ist-Abgleich ─────────────────────────────────────────",
    "",
    "// Hilfsfunktion: Tendenz-Icon (keine Unicode-Pfeilzeichen im JS-Source)",
    "function hskTendenzIcon(t) {",
    "  if (t === 'positiv') return '<span class=\"text-emerald-400 font-bold\" title=\"Tendenz: Haushalt bewegt sich in HSK-Richtung\">&uarr;</span>';",
    "  if (t === 'negativ') return '<span class=\"text-rose-400 font-bold\" title=\"Tendenz: Haushalt gegenlaeu-fig zum HSK-Ziel\">&darr;</span>';",
    "  return '<span class=\"text-slate-600\">-</span>';",
    "}",
    "",
    "// Erweitert renderHsk() um Abgleich-KPIs (wird direkt nach renderHsk aufgerufen)",
    "const _renderHsk_orig = renderHsk;",
    "renderHsk = function() {",
    "  _renderHsk_orig();",
    "  if (!DATA.hsk || !DATA.hsk.meta) return;",
    "  const meta = DATA.hsk.meta;",
    "  const el = id => document.getElementById(id);",
    "  if (el('hsk-kpi-abgleich'))",
    "    el('hsk-kpi-abgleich').textContent = (meta.n_mit_abgleich || 0) + ' / ' + (meta.n_massnahmen || 0);",
    "  if (el('hsk-kpi-pos')) el('hsk-kpi-pos').textContent = meta.n_tendenz_positiv || 0;",
    "  if (el('hsk-kpi-neg')) el('hsk-kpi-neg').textContent = meta.n_tendenz_negativ || 0;",
    "  if (el('hsk-abgleich-text'))",
    "    el('hsk-abgleich-text').textContent =",
    "      (meta.n_mit_abgleich || 0) + ' Massnahmen mit Haushalt-Produktverknuepfung. ' +",
    "      (meta.n_tendenz_positiv || 0) + ' zeigen positive Tendenz (Haushalt in HSK-Richtung), ' +",
    "      (meta.n_tendenz_negativ || 0) + ' zeigen negative Tendenz.';",
    "};",
    "",
    "// Erweitert renderHskTable() um Tendenz-Spalte und Abgleich-Detail",
    "const _renderHskTable_orig = renderHskTable;",
    "renderHskTable = function() {",
    "  _renderHskTable_orig();",
    "  const tbody = document.getElementById('hsk-tabelle-body');",
    "  if (!tbody || !DATA.hsk) return;",
    "  // Tendenz-Zellen: in jede Hauptzeile (nicht Detail-Zeilen) eine Spalte einbauen",
    "  tbody.querySelectorAll('tr[onclick]').forEach(tr => {",
    "    const mid = parseInt((tr.getAttribute('onclick') || '').match(/\\d+/)?.[0]);",
    "    const m = DATA.hsk.massnahmen.find(x => x.id === mid);",
    "    if (!m) return;",
    "    // Tendenz-Zelle vor Status-Zelle einfuegen",
    "    const statusTd = tr.querySelector('td:last-child');",
    "    if (!statusTd) return;",
    "    const tendTd = document.createElement('td');",
    "    tendTd.className = 'py-2 pr-3 text-center';",
    "    tendTd.innerHTML = hskTendenzIcon(m.tendenz);",
    "    tr.insertBefore(tendTd, statusTd);",
    "  });",
    "  // Abgleich-Detail: in jede Detailzeile einfuegen wenn Daten vorhanden",
    "  tbody.querySelectorAll('tr[id^=\"hsk-detail-\"]').forEach(detailTr => {",
    "    const mid = parseInt(detailTr.id.replace('hsk-detail-', ''));",
    "    const m = DATA.hsk.massnahmen.find(x => x.id === mid);",
    "    if (!m || !m.abgleich || !Object.keys(m.abgleich).length) return;",
    "    const innerGrid = detailTr.querySelector('.grid');",
    "    if (!innerGrid) return;",
    "    const div = document.createElement('div');",
    "    div.className = 'mt-3';",
    "    div.innerHTML = buildAbgleichCard(m);",
    "    innerGrid.appendChild(div);",
    "  });",
    "};",
    "",
    "function buildAbgleichCard(m) {",
    "  const prods = Object.entries(m.abgleich || {});",
    "  if (!prods.length) return '';",
    "  const useKK = m.kategorie === 'ERTRAG' ? 'kk4' : 'kk5';",
    "  const kkLabel = m.kategorie === 'ERTRAG' ? 'Ertr&#228;ge (KK4)' : 'Aufwend. (KK5)';",
    "  let html = '<div class=\"font-medium text-slate-200 text-xs mb-2\">Soll/Ist-Abgleich 2022-2025</div>';",
    "  for (const [prodNr, pd] of prods) {",
    "    const tpLabel = pd.tp_nr ? ' (TP' + pd.tp_nr + ')' : '';",
    "    html += '<div class=\"text-xs text-slate-400 mb-1\">' + prodNr + tpLabel + '</div>';",
    "    html += '<table class=\"w-full text-xs mb-3\">';",
    "    html += '<thead><tr class=\"text-slate-500 border-b border-slate-700\">';",
    "    html += '<th class=\"text-left py-1 pr-2\">Jahr</th>';",
    "    html += '<th class=\"text-right py-1 pr-2\">HSK-Ziel</th>';",
    "    html += '<th class=\"text-right py-1 pr-2\">' + kkLabel + '</th>';",
    "    html += '<th class=\"text-right py-1\">Entw.</th>';",
    "    html += '</tr></thead><tbody>';",
    "    const years = ['2022','2023','2024','2025'];",
    "    let prevKK = null;",
    "    for (const yr of years) {",
    "      const jd = (pd.jahre || {})[yr];",
    "      if (!jd) continue;",
    "      const kk = jd[useKK] || 0;",
    "      const hsk = jd.hsk_ziel || 0;",
    "      const kkFmt = kk ? fmt(kk/1000, 0) + ' T' : '-';",
    "      const hskFmt = hsk ? (hsk > 0 ? '+' : '') + fmt(hsk/1000, 0) + ' T' : '-';",
    "      let entw = '<span class=\"text-slate-600\">-</span>';",
    "      if (prevKK !== null && kk) {",
    "        const d = kk - prevKK;",
    "        const isGood = m.kategorie === 'ERTRAG' ? d > 0 : d < 0;",
    "        const col = isGood ? 'text-emerald-400' : 'text-rose-400';",
    "        const arr = d > 0 ? '&uarr;' : (d < 0 ? '&darr;' : '&rarr;');",
    "        entw = '<span class=\"' + col + '\">' + arr + ' ' + fmt(Math.abs(d)/1000, 0) + ' T</span>';",
    "      }",
    "      prevKK = kk || prevKK;",
    "      html += '<tr class=\"border-b border-slate-800\">';",
    "      html += '<td class=\"py-1 pr-2 text-slate-400\">' + yr + '</td>';",
    "      html += '<td class=\"py-1 pr-2 text-right text-blue-300 font-mono\">' + hskFmt + '</td>';",
    "      html += '<td class=\"py-1 pr-2 text-right text-slate-200 font-mono\">' + kkFmt + '</td>';",
    "      html += '<td class=\"py-1 text-right\">' + entw + '</td>';",
    "      html += '</tr>';",
    "    }",
    "    html += '</tbody></table>';",
    "  }",
    "  return html;",
    "}",
    "",
    "function setupTabs() {",
])

content = apply(content, OLD_SETUP_TABS, STUFE2_JS, "Stufe-2-JS-Block (Monkey-Patching)")


with open(path, "wb") as f:
    f.write(content.encode("utf-8"))

print(f"\nFertig! {path}")
