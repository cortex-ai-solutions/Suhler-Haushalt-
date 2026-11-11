"""
Stufe C: Drei-Zonen-Visualisierung im Konsolidierungs-Simulator.

Zone 1 (blau):   HSK-Einsparziel - bereits geplante Konsolidierung
Zone 2 (orange): Eigene zusaetzliche Kuerzung im Szenario
Zone 3 (grau):   Ungenutzter Spielraum bis max_kuerzung_pct

Aenderungen:
- Zone-Bar (Farbverlauf-Div) ueber dem Schieberegler
- data-hsk-pct Attribut am Range-Input
- updateSimZoneBar() aktualisiert Farbzonen dynamisch
- onSlider Monkey-Patch: ruft updateSimZoneBar() auf
- Verbesserte Slider-Beschriftung: HSK/Zusatz kontextuell
- Legende im Simulator-Header
CRLF-sicher.
"""

CRLF = "\r\n"

with open("index.html", "rb") as f:
    content = f.read().decode("utf-8")


def apply(c, old, new, label):
    count = c.count(old)
    if count == 0:
        raise ValueError(f"NICHT GEFUNDEN: {label!r}  ('{old[:70]}')")
    if count > 1:
        raise ValueError(f"NICHT EINDEUTIG ({count}x): {label!r}")
    print(f"  [OK] {label}")
    return c.replace(old, new, 1)


# ── Patch 1: Zone-Bar + data-hsk-pct im renderSimListe ───────────────────────
# Ersetzt den Range-Input-Block durch Zone-Bar + verbesserter Input + Label

OLD_SLIDER_BLOCK = CRLF.join([
    "      '<div class=\"slider-row\">' +",
    "        '<input type=\"range\" min=\"0\" max=\"' + p.max_kuerzung_pct + '\" step=\"1\" value=\"' + cur + '\"' +",
    "          (locked ? ' disabled' : '') +",
    "          ' data-pnr=\"' + p.produkt_nummer + '\" oninput=\"onSlider(this)\"' +",
    "          ' class=\"' + (locked ? 'opacity-30 cursor-not-allowed' : '') + '\">' +",
    "        '<div class=\"text-sm text-center\">' +",
    "          '<span id=\"pct-' + p.produkt_nummer + '\" class=\"' +",
    "            (cur > 0 ? 'text-emerald-400' : 'text-slate-400') + '\">' + cur + '%</span>' +",
    "          (locked",
    "            ? '<span class=\"ml-1 text-xs text-slate-600\">gesperrt</span>'",
    "            : '<span class=\"text-xs text-slate-500\"> von max.&nbsp;' + p.max_kuerzung_pct + '%</span>') +",
    "        '</div>' +",
    "        '<div class=\"text-sm text-right\">' +",
    "          '<span id=\"sav-' + p.produkt_nummer + '\" class=\"text-emerald-400\">' +",
    "            (cur > 0 ? '&minus;' + fmtMio(p.kk5_2025 * cur / 100) : '') + '</span>' +",
    "        '</div>' +",
    "      '</div>' +",
])

# hskPct fuer dieses Produkt (schon als var hskSpar und p.kk5_2025 berechnet)
NEW_SLIDER_BLOCK = CRLF.join([
    "      '<div class=\"slider-row\">' +",
    "        // Zone-Bar: zeigt HSK-Zone (blau) und eigene Zusatz-Zone (orange)",
    "        '<div class=\"relative mb-1\">' +",
    "          '<div id=\"zone-' + p.produkt_nummer + '\" class=\"w-full h-2 rounded-full bg-slate-700/50\"></div>' +",
    "          (hskSpar && p.kk5_2025 && p.max_kuerzung_pct > 0",
    "            ? '<span class=\"absolute top-0 h-2 w-px bg-blue-400/80 pointer-events-none\"' +",
    "              ' style=\"left:' + Math.min(hskSpar/p.kk5_2025*100/p.max_kuerzung_pct*100, 100) + '%\"></span>'",
    "            : '') +",
    "        '</div>' +",
    "        '<input type=\"range\" min=\"0\" max=\"' + p.max_kuerzung_pct + '\" step=\"1\" value=\"' + cur + '\"' +",
    "          (locked ? ' disabled' : '') +",
    "          ' data-pnr=\"' + p.produkt_nummer + '\"' +",
    "          ' data-hsk-pct=\"' + (hskSpar && p.kk5_2025 ? (hskSpar/p.kk5_2025*100).toFixed(2) : '0') + '\"' +",
    "          ' oninput=\"onSlider(this)\"' +",
    "          ' class=\"' + (locked ? 'opacity-30 cursor-not-allowed' : '') + '\">' +",
    "        '<div class=\"text-sm text-center\">' +",
    "          '<span id=\"pct-' + p.produkt_nummer + '\" class=\"' +",
    "            (cur > 0 ? 'text-emerald-400' : 'text-slate-400') + '\">' + cur + '%</span>' +",
    "          (locked",
    "            ? '<span class=\"ml-1 text-xs text-slate-600\">gesperrt</span>'",
    "            : '<span class=\"text-xs text-slate-500\"> von max.&nbsp;' + p.max_kuerzung_pct + '%</span>') +",
    "        '</div>' +",
    "        '<div class=\"text-sm text-right\">' +",
    "          '<span id=\"sav-' + p.produkt_nummer + '\" class=\"text-emerald-400\">' +",
    "            (cur > 0 ? '&minus;' + fmtMio(p.kk5_2025 * cur / 100) : '') + '</span>' +",
    "        '</div>' +",
    "      '</div>' +",
])

content = apply(content, OLD_SLIDER_BLOCK, NEW_SLIDER_BLOCK, "Zone-Bar + data-hsk-pct im Slider")

# ── Patch 2: updateSimZoneBar nach liste.appendChild(card) aufrufen ───────────
OLD_APPEND = (
    "    liste.appendChild(card);" + CRLF +
    "  });" + CRLF +
    "};"
)
NEW_APPEND = (
    "    liste.appendChild(card);" + CRLF +
    "    updateSimZoneBar(p.produkt_nummer);" + CRLF +
    "  });" + CRLF +
    "};"
)
content = apply(content, OLD_APPEND, NEW_APPEND, "updateSimZoneBar nach appendChild")

# ── Patch 3: Legende in Simulator-Header ──────────────────────────────────────
OLD_SIM_DESC = (
    '      Verschiebe die Regler, um Kürzungsszenarien zu modellieren. Pflichtaufgaben (strikt) sind gesperrt.' + CRLF +
    '      Das Jahresergebnis aktualisiert sich in Echtzeit.'
)
NEW_SIM_DESC = (
    '      Verschiebe die Regler, um Kürzungsszenarien zu modellieren. Pflichtaufgaben (strikt) sind gesperrt.' + CRLF +
    '      Das Jahresergebnis aktualisiert sich in Echtzeit.' + CRLF +
    '      <span class="inline-flex gap-3 mt-2 text-xs">' + CRLF +
    '        <span><span class="inline-block w-3 h-2 rounded-sm bg-blue-600/70 mr-1"></span>HSK-Einsparziel</span>' + CRLF +
    '        <span><span class="inline-block w-3 h-2 rounded-sm bg-orange-400/70 mr-1"></span>Eigene Zusatz-Kürzung</span>' + CRLF +
    '        <span><span class="inline-block w-3 h-2 rounded-sm bg-slate-600 mr-1"></span>Ungenutzter Spielraum</span>' + CRLF +
    '      </span>'
)
content = apply(content, OLD_SIM_DESC, NEW_SIM_DESC, "Zonen-Legende im Header")

# ── Patch 4: JS-Funktionen (updateSimZoneBar + onSlider-Patch) ────────────────
OLD_JS_ANCHOR = "function setupTabs() {"

JS_LINES = [
    "// ── Stufe C: Drei-Zonen-Visualisierung ─────────────────────────────────────",
    "",
    "function updateSimZoneBar(pnr) {",
    "  var el  = document.querySelector('input[data-pnr=\"' + pnr + '\"]');",
    "  var bar = document.getElementById('zone-' + pnr);",
    "  if (!el || !bar) return;",
    "  var maxV = parseFloat(el.max) || 100;",
    "  var curV = parseFloat(el.value) || 0;",
    "  var hskV = parseFloat(el.dataset.hskPct) || 0;",
    "  if (maxV === 0) { bar.style.background = '#1e293b'; return; }",
    "  var hskPos = Math.min(hskV / maxV * 100, 100);",
    "  var curPos = Math.min(curV / maxV * 100, 100);",
    "  var stops;",
    "  if (hskPos === 0 && curPos === 0) {",
    "    stops = '#1e293b 0%, #1e293b 100%';",
    "  } else if (curPos >= hskPos) {",
    "    // Blau (HSK) | Orange (Zusatz) | Grau (Rest)",
    "    var s = '';",
    "    if (hskPos > 0) s += '#3b82f6 0%, #3b82f6 ' + hskPos + '%, ';",
    "    if (curPos > hskPos) s += '#f97316 ' + hskPos + '%, #f97316 ' + curPos + '%, ';",
    "    s += '#1e293b ' + curPos + '%, #1e293b 100%';",
    "    stops = s;",
    "  } else {",
    "    // Gelb-Orange (teilerfuellt) | Dunkelblau (noch offen bis HSK) | Grau",
    "    var s2 = '';",
    "    if (curPos > 0) s2 += '#f97316 0%, #f97316 ' + curPos + '%, ';",
    "    s2 += '#1d4ed8 ' + curPos + '%, #1d4ed8 ' + hskPos + '%, ';",
    "    s2 += '#1e293b ' + hskPos + '%, #1e293b 100%';",
    "    stops = s2;",
    "  }",
    "  bar.style.background = 'linear-gradient(to right, ' + stops + ')';",
    "}",
    "",
    "// onSlider: Zone-Bar nach jeder Slider-Bewegung aktualisieren",
    "var _onSlider_orig = onSlider;",
    "onSlider = function(el) {",
    "  _onSlider_orig(el);",
    "  updateSimZoneBar(el.dataset.pnr);",
    "};",
    "",
    "function setupTabs() {",
]

NEW_JS_BLOCK = CRLF.join(JS_LINES)
content = apply(content, OLD_JS_ANCHOR, NEW_JS_BLOCK, "Stufe-C JS (updateSimZoneBar + onSlider-Patch)")


with open("index.html", "wb") as f:
    f.write(content.encode("utf-8"))

bt = content.count("\x60")
print(f"\nBackticks: {bt} ({'GERADE' if bt % 2 == 0 else 'UNGERADE!'})")
print("Fertig. index.html aktualisiert.")
