"""
Patch HSK Stufe 2: Soll/Ist-Abgleich im Dashboard.
- Tendenz-Indikator in der Maßnahmen-Tabelle (Spalte nach Status)
- Abgleich-Karte im Detail-Row: HSK-Ziel vs. tatsächliche Haushaltswerte
- Zusätzlicher KPI: Maßnahmen mit Produktabgleich
- Info-Text unterhalb Schmerzskala mit Abgleich-Statistik
CRLF-sicher.
"""

path = "index.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

CRLF = "\r\n"


def apply(c, old, new, label):
    if old not in c:
        raise ValueError(f"NICHT GEFUNDEN: {label!r}\n  Suche: {old!r:.120}")
    print(f"  [OK] {label}")
    return c.replace(old, new, 1)


# ── 1: KPI-Chips: 5. Chip "Mit Produktabgleich" ───────────────────────────
OLD_KPI_GRID = (
    '  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">'
)
NEW_KPI_GRID = (
    '  <div class="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">'
)
content = apply(content, OLD_KPI_GRID, NEW_KPI_GRID, "KPI-Grid 5 Spalten")

OLD_KPI_LAST = (
    '    <div class="card p-4">' + CRLF +
    '      <div class="kpi-label">Aktives Potenzial 2025</div>' + CRLF +
    '      <div class="kpi-value text-violet-300" id="hsk-kpi-2025">–</div>' + CRLF +
    '      <div class="note mt-1">laufende Maßnahmen Plan 2025</div>' + CRLF +
    '    </div>' + CRLF +
    '  </div>'
)
NEW_KPI_LAST = CRLF.join([
    '    <div class="card p-4">',
    '      <div class="kpi-label">Aktives Potenzial 2025</div>',
    '      <div class="kpi-value text-violet-300" id="hsk-kpi-2025">–</div>',
    '      <div class="note mt-1">laufende Maßnahmen Plan 2025</div>',
    '    </div>',
    '    <div class="card p-4 border border-blue-800/40">',
    '      <div class="kpi-label">Mit Produktabgleich</div>',
    '      <div class="kpi-value text-blue-300" id="hsk-kpi-abgleich">–</div>',
    '      <div class="note mt-1">',
    '        <span class="text-emerald-400" id="hsk-kpi-pos"></span> positiv /',
    '        <span class="text-rose-400" id="hsk-kpi-neg"></span> negativ',
    '      </div>',
    '    </div>',
    '  </div>',
])
content = apply(content, OLD_KPI_LAST, NEW_KPI_LAST, "KPI-Chip Abgleich")


# ── 2: Schmerzskala Info-Text erweitern ────────────────────────────────────
OLD_SCHMERZ_TEXT = (
    '    <p class="text-xs text-slate-400 mt-3" id="hsk-schmerz-text"></p>'
)
NEW_SCHMERZ_TEXT = CRLF.join([
    '    <p class="text-xs text-slate-400 mt-3" id="hsk-schmerz-text"></p>',
    '    <p class="text-xs text-slate-500 mt-1" id="hsk-abgleich-text"></p>',
])
content = apply(content, OLD_SCHMERZ_TEXT, NEW_SCHMERZ_TEXT, "Schmerzskala Abgleich-Text")


# ── 3: Tabellen-Header: Tendenz-Spalte ────────────────────────────────────
OLD_TH_STATUS = (
    '            <th class="py-2 font-medium w-24">Status</th>'
)
NEW_TH_STATUS = CRLF.join([
    '            <th class="py-2 pr-3 font-medium w-16 text-center"',
    '                title="Tendenz: Bewegt sich der Haushalt in Richtung des HSK-Ziels?">Tend.</th>',
    '            <th class="py-2 font-medium w-24">Status</th>',
])
content = apply(content, OLD_TH_STATUS, NEW_TH_STATUS, "TH Tendenz-Spalte")


# ── 4: renderHsk(): KPI-Chips für Abgleich befüllen + Abgleich-Text ────────
OLD_KPI_END = (
    "  setText(\"hsk-kpi-2025\", fmtT(meta.gesamt_2025));"
)
NEW_KPI_END = CRLF.join([
    "  setText(\"hsk-kpi-2025\", fmtT(meta.gesamt_2025));",
    "  setText(\"hsk-kpi-abgleich\", meta.n_mit_abgleich + \" / \" + meta.n_massnahmen);",
    "  setText(\"hsk-kpi-pos\",     meta.n_tendenz_positiv);",
    "  setText(\"hsk-kpi-neg\",     meta.n_tendenz_negativ);",
    "  setText(\"hsk-abgleich-text\",",
    "    meta.n_mit_abgleich + \" Maßnahmen sind über Produktnummern direkt mit den Haushaltsdaten verknüpft. \" +",
    "    meta.n_tendenz_positiv + \" davon zeigen eine Haushalts-Tendenz, die mit dem HSK-Ziel übereinstimmt, \" +",
    "    meta.n_tendenz_negativ + \" zeigen eine gegenläufige Tendenz (2023→2025).\");",
])
content = apply(content, OLD_KPI_END, NEW_KPI_END, "KPI Abgleich befüllen")


# ── 5: renderHskTable(): Tendenz-Zelle + Abgleich-Detail ──────────────────
OLD_TABLE_ROW = (
    '      <td class="py-2">' + CRLF +
    '        <span class="text-xs px-1.5 py-0.5 rounded ${sc}">${STATUS_LABEL[m.status]||m.status}</span>' + CRLF +
    '      </td>' + CRLF +
    '    </tr>`,'
)

NEW_TABLE_ROW = (
    '      <td class="py-2 pr-3 text-center">' + CRLF +
    '        ${m.tendenz === "positiv" ? \'<span title="Tendenz positiv" class="text-emerald-400">↑</span>\'' + CRLF +
    '          : m.tendenz === "negativ" ? \'<span title="Tendenz negativ" class="text-rose-400">↓</span>\'' + CRLF +
    '          : \'<span class="text-slate-600 text-xs">–</span>\'}' + CRLF +
    '      </td>' + CRLF +
    '      <td class="py-2">' + CRLF +
    '        <span class="text-xs px-1.5 py-0.5 rounded ${sc}">${STATUS_LABEL[m.status]||m.status}</span>' + CRLF +
    '      </td>' + CRLF +
    '    </tr>`,'
)
content = apply(content, OLD_TABLE_ROW, NEW_TABLE_ROW, "Tendenz-Zelle in Tabellenzeile")


# ── 6: Detail-Row: Abgleich-Karte einbauen ────────────────────────────────
OLD_DETAIL_END = (
    '          </div>' + CRLF +
    '        </div>' + CRLF +
    '      </td>' + CRLF +
    '    </tr>`'
)

NEW_DETAIL_END = (
    '          </div>' + CRLF +
    '          <div class="lg:col-span-1 mt-3 lg:mt-0">' + CRLF +
    '            ${Object.keys(m.abgleich||{}).length ? buildAbgleichCard(m) : ""}' + CRLF +
    '          </div>' + CRLF +
    '        </div>' + CRLF +
    '      </td>' + CRLF +
    '    </tr>`'
)
content = apply(content, OLD_DETAIL_END, NEW_DETAIL_END, "Abgleich-Karte im Detail-Row")


# ── 7: buildAbgleichCard Funktion ─────────────────────────────────────────
OLD_BUILD_JW = "function buildHskJahreswerte(m) {"

ABGLEICH_CARD_JS = CRLF.join([
    "function buildAbgleichCard(m) {",
    "  const prods = Object.entries(m.abgleich);",
    "  if (!prods.length) return '';",
    "  const katLabel = m.kategorie === 'ERTRAG' ? 'Erträge (KK4)' :",
    "                   m.kategorie === 'PERSONAL' ? 'Aufwend. (KK5)' : 'Aufwend. (KK5)';",
    "  const useKK = m.kategorie === 'ERTRAG' ? 'kk4' : 'kk5';",
    "  const goalDir = m.kategorie === 'ERTRAG' ? '+' : '−';  // + oder −",
    "",
    "  let html = '<div class=\"font-medium text-slate-200 text-xs mb-2\">Soll/Ist-Abgleich (Haushaltsdaten 2022–2025)</div>';",
    "",
    "  for (const [prodNr, pd] of prods) {",
    "    const prodLabel = pd.bezeichnung && pd.bezeichnung !== prodNr",
    "      ? `${prodNr} – ${pd.bezeichnung}` : prodNr;",
    "    const tpLabel = pd.tp_nr ? ` (TP${pd.tp_nr})` : '';",
    "    html += `<div class=\"text-xs text-slate-400 mb-1\">${prodLabel}${tpLabel}</div>`;",
    "    html += '<table class=\"w-full text-xs mb-3\">';",
    "    html += '<thead><tr class=\"text-slate-500 border-b border-slate-700\">';",
    "    html += '<th class=\"text-left py-1 pr-2\">Jahr</th>';",
    "    html += `<th class=\"text-right py-1 pr-2\">HSK-Ziel (jährl.)</th>`;",
    "    html += `<th class=\"text-right py-1 pr-2\">${katLabel}</th>`;",
    "    html += '<th class=\"text-right py-1\">Entw.</th>';",
    "    html += '</tr></thead><tbody>';",
    "",
    "    const years = ['2022','2023','2024','2025'];",
    "    let prevKK = null;",
    "    for (const yr of years) {",
    "      const jd = pd.jahre[yr];",
    "      if (!jd) continue;",
    "      const kk = jd[useKK];",
    "      const hsk = jd.hsk_ziel;",
    "      const kkFmt = kk ? fmt(kk/1000, 0) + ' T€' : '–';",
    "      const hskFmt = hsk ? (hsk > 0 ? '+' : '') + fmt(hsk/1000, 0) + ' T€' : '–';",
    "      let entw = '<span class=\"text-slate-600\">–</span>';",
    "      if (prevKK !== null && kk) {",
    "        const d = kk - prevKK;",
    "        const isGood = m.kategorie === 'ERTRAG' ? d > 0 : d < 0;",
    "        const col = isGood ? 'text-emerald-400' : 'text-rose-400';",
    "        const arrow = d > 0 ? '↑' : d < 0 ? '↓' : '→';",
    "        entw = `<span class=\"${col}\">${arrow} ${fmt(Math.abs(d)/1000,0)} T€</span>`;",
    "      }",
    "      prevKK = kk || prevKK;",
    "      html += `<tr class=\"border-b border-slate-800\">`;",
    "      html += `<td class=\"py-1 pr-2 text-slate-400\">${yr}</td>`;",
    "      html += `<td class=\"py-1 pr-2 text-right text-blue-300 font-mono\">${hskFmt}</td>`;",
    "      html += `<td class=\"py-1 pr-2 text-right text-slate-200 font-mono\">${kkFmt}</td>`;",
    "      html += `<td class=\"py-1 text-right\">${entw}</td>`;",
    "      html += '</tr>';",
    "    }",
    "    html += '</tbody></table>';",
    "  }",
    "  return html;",
    "}",
    "",
    "function buildHskJahreswerte(m) {",
])
content = apply(content, OLD_BUILD_JW, ABGLEICH_CARD_JS, "buildAbgleichCard Funktion")


with open(path, "wb") as f:
    f.write(content.encode("utf-8"))

print(f"\nFertig! {path}")
