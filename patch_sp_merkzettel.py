"""
Patch: Merkzettel für den Stellenplan-Abschnitt im Personal-Tab.
- Pin-Buttons an jeder Besoldungsgruppen-Zeile und jedem Teilplan
- Merkzettel-Kachel mit Jahresvergleich und Δ-Anzeige
- localStorage-Persistenz (Key: 'sp_pins')
"""

path = "index.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

CRLF = "\r\n"


def apply(c, old, new, label):
    if old not in c:
        raise ValueError(f"NICHT GEFUNDEN: {label!r}")
    print(f"  [OK] {label}")
    return c.replace(old, new, 1)


# ── 1: Merkzettel-HTML nach den zwei Stellenplan-Charts einfügen ──────────
OLD_SP_CLOSE = (
    '    </div>' + CRLF +
    '' + CRLF +
    '  </div>' + CRLF +
    '' + CRLF +
    '</div>' + CRLF +
    '<!-- ══════════ TAB: JAHRESVERGLEICH ══════════ -->'
)

MERKZETTEL_HTML = CRLF.join([
    '    </div>',
    '',
    '    <!-- Stellenplan-Tabelle (pinnable) -->',
    '    <div class="card p-5 mb-6">',
    '      <div class="flex items-center justify-between mb-3">',
    '        <div class="section-title">Stellen je Besoldungs-/Entgeltgruppe</div>',
    '        <button onclick="clearSpPins()" class="text-xs text-slate-500 hover:text-slate-300 transition">',
    '          Alle Pins entfernen',
    '        </button>',
    '      </div>',
    '      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">',
    '        <div class="lg:col-span-2 overflow-x-auto">',
    '          <table class="w-full text-sm" id="sp-gruppe-table">',
    '            <thead></thead>',
    '            <tbody></tbody>',
    '          </table>',
    '        </div>',
    '        <div id="sp-merkzettel-card" class="card bg-slate-800/60 p-4 hidden">',
    '          <div class="section-title text-sm mb-3">',
    '            📌 Gepinnte Gruppen',
    '          </div>',
    '          <div id="sp-merkzettel-body"></div>',
    '        </div>',
    '      </div>',
    '    </div>',
    '',
    '  </div>',
    '',
    '</div>',
    '<!-- ══════════ TAB: JAHRESVERGLEICH ══════════ -->',
])

content = apply(content, OLD_SP_CLOSE, MERKZETTEL_HTML, "Merkzettel-HTML Stellenplan")


# ── 2: JS für Merkzettel ans Ende von renderPersonal() ───────────────────
# Suche den Ende-Block (nach den Plotly-Charts, vor der schliessenden Klammer)
OLD_RENDER_LAST = (
    '  }, { responsive:true, displayModeBar:false });' + CRLF +
    '}'
)

NEW_RENDER_LAST = CRLF.join([
    '  }, { responsive:true, displayModeBar:false });',
    '',
    '  renderSpGruppeTable(sp, SP);',
    '}',
    '',
    '// ── Stellenplan-Merkzettel ─────────────────────────────────────────────────',
    'let spPins = new Set(JSON.parse(localStorage.getItem("sp_pins") || "[]"));',
    '',
    'function saveSpPins() {',
    '  localStorage.setItem("sp_pins", JSON.stringify([...spPins]));',
    '}',
    '',
    'function clearSpPins() {',
    '  spPins.clear(); saveSpPins();',
    '  const SP = DATA.personal && DATA.personal.stellenplan;',
    '  const yr = String(activeJahr);',
    '  const spKey = yr + "_PLAN_ANSATZ";',
    '  const sp = SP && (SP.by_year[spKey] || SP.by_year["2025_PLAN_ANSATZ"]);',
    '  if (sp) renderSpGruppeTable(sp, SP);',
    '}',
    '',
    'function toggleSpPin(kuerzel) {',
    '  if (spPins.has(kuerzel)) spPins.delete(kuerzel); else spPins.add(kuerzel);',
    '  saveSpPins();',
    '  const SP = DATA.personal && DATA.personal.stellenplan;',
    '  const yr = String(activeJahr);',
    '  const spKey = yr + "_PLAN_ANSATZ";',
    '  const sp = SP && (SP.by_year[spKey] || SP.by_year["2025_PLAN_ANSATZ"]);',
    '  if (sp) renderSpGruppeTable(sp, SP);',
    '}',
    '',
    'function renderSpGruppeTable(sp, SP) {',
    '  const ng = sp.nach_gruppe || {};',
    '  const years = Object.keys(SP.by_year)',
    '    .filter(k => k.endsWith("_PLAN_ANSATZ"))',
    '    .sort();',
    '  // Jahres-Labels (z.B. "2024", "2025")',
    '  const yrLabels = years.map(k => k.replace("_PLAN_ANSATZ",""));',
    '',
    '  const thead = document.querySelector("#sp-gruppe-table thead");',
    '  const tbody = document.querySelector("#sp-gruppe-table tbody");',
    '  if (!thead || !tbody) return;',
    '',
    '  // Kopfzeile',
    '  thead.innerHTML = `<tr class="text-left text-slate-400 text-xs border-b border-slate-700">',
    '    <th class="py-2 pr-3 font-medium">Gruppe</th>',
    '    <th class="py-2 pr-3 font-medium">Typ</th>',
    '    ${yrLabels.map(y => `<th class="py-2 pr-3 font-medium text-right">${y}</th>`).join("")}',
    '    ${yrLabels.length > 1 ? `<th class="py-2 pr-3 font-medium text-right">Δ</th>` : ""}',
    '    <th class="py-2 font-medium text-center w-8">📌</th>',
    '  </tr>`;',
    '',
    '  // Alle Gruppen, Beamte zuerst, dann Tarif; je Typ nach Planstellen desc',
    '  const sorted = Object.keys(ng).sort((a, b) => {',
    '    if (ng[a].typ !== ng[b].typ) return ng[a].typ === "BEAMTE" ? -1 : 1;',
    '    return ng[b].planstellen - ng[a].planstellen;',
    '  });',
    '',
    '  const rows = sorted.map(kg => {',
    '    const pinned = spPins.has(kg);',
    '    const typColor = ng[kg].typ === "BEAMTE" ? "text-blue-300" : "text-emerald-300";',
    '    const typLabel = ng[kg].typ === "BEAMTE" ? "Beamte" : "Tarif";',
    '    const vals = yrLabels.map(y => {',
    '      const ysp = SP.by_year[y + "_PLAN_ANSATZ"] || {};',
    '      return (ysp.nach_gruppe || {})[kg]?.planstellen ?? null;',
    '    });',
    '    const valCells = vals.map(v =>`<td class="py-1.5 pr-3 text-right">${v !== null ? fmt(v,3) : "–"}</td>`).join("");',
    '    let deltaTd = "";',
    '    if (yrLabels.length > 1) {',
    '      const first = vals[0], last = vals[vals.length-1];',
    '      if (first !== null && last !== null) {',
    '        const d = last - first;',
    '        const sign = d >= 0 ? "+" : "";',
    '        const col = d > 0 ? "text-emerald-400" : d < 0 ? "text-rose-400" : "text-slate-400";',
    '        deltaTd = `<td class="py-1.5 pr-3 text-right ${col}">${sign}${fmt(d,3)}</td>`;',
    '      } else {',
    '        deltaTd = `<td class="py-1.5 pr-3 text-right text-slate-500">–</td>`;',
    '      }',
    '    }',
    '    return `<tr class="border-b border-slate-800 hover:bg-slate-800/40 ${pinned ? "bg-blue-950/30" : ""}">',
    '      <td class="py-1.5 pr-3 font-mono font-medium text-slate-200">${kg}</td>',
    '      <td class="py-1.5 pr-3"><span class="text-xs ${typColor}">${typLabel}</span></td>',
    '      ${valCells}${deltaTd}',
    '      <td class="py-1.5 text-center cursor-pointer select-none" onclick="toggleSpPin(\'${kg}\')"',
    '          title="${pinned ? \'Pin entfernen\' : \'Pinnen\'}">${pinned ? "\U0001F4CC" : \'<span class="text-slate-600 hover:text-slate-400">\U0001F4CC</span>\'}</td>',
    '    </tr>`;',
    '  });',
    '  tbody.innerHTML = rows.join("");',
    '',
    '  // Merkzettel-Kachel',
    '  const mc = document.getElementById("sp-merkzettel-card");',
    '  const mb = document.getElementById("sp-merkzettel-body");',
    '  if (!mc || !mb) return;',
    '  if (spPins.size === 0) { mc.classList.add("hidden"); return; }',
    '  mc.classList.remove("hidden");',
    '',
    '  let mhtml = `<table class="w-full text-xs mb-2">',
    '    <thead><tr class="text-slate-400 border-b border-slate-700">',
    '      <th class="text-left py-1 pr-2">Gruppe</th>',
    '      ${yrLabels.map(y => `<th class="text-right py-1 pr-2">${y}</th>`).join("")}',
    '      ${yrLabels.length > 1 ? `<th class="text-right py-1">Δ</th>` : ""}',
    '    </tr></thead><tbody>`;',
    '  [...spPins].forEach(kg => {',
    '    if (!ng[kg]) return;',
    '    const vals = yrLabels.map(y => {',
    '      const ysp = SP.by_year[y + "_PLAN_ANSATZ"] || {};',
    '      return (ysp.nach_gruppe || {})[kg]?.planstellen ?? null;',
    '    });',
    '    const valCells = vals.map(v => `<td class="py-1 pr-2 text-right text-slate-200">${v !== null ? fmt(v,3) : "–"}</td>`).join("");',
    '    let dTd = "";',
    '    if (yrLabels.length > 1) {',
    '      const d = (vals[vals.length-1] ?? 0) - (vals[0] ?? 0);',
    '      const sign = d >= 0 ? "+" : "";',
    '      const col = d > 0 ? "text-emerald-400" : d < 0 ? "text-rose-400" : "text-slate-400";',
    '      dTd = `<td class="py-1 text-right ${col}">${sign}${fmt(d,3)}</td>`;',
    '    }',
    '    mhtml += `<tr class="border-b border-slate-800">',
    '      <td class="py-1 pr-2 font-mono font-medium text-slate-300">${kg}',
    '        <button class="ml-1 text-slate-600 hover:text-slate-300" onclick="toggleSpPin(\'${kg}\')">✕</button></td>',
    '      ${valCells}${dTd}`,',
    '    </tr>`;',
    '  });',
    '  mhtml += "</tbody></table>";',
    '  mb.innerHTML = mhtml;',
    '}',
])
content = apply(content, OLD_RENDER_LAST, NEW_RENDER_LAST, "Merkzettel JS")


with open(path, "wb") as f:
    f.write(content.encode("utf-8"))

print(f"\nFertig! {path}")
