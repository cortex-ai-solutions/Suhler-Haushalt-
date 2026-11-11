# -*- coding: utf-8 -*-
"""
patch_investitionen_foerderpotenzial.py - Baustein 3 des "Drei-Wege-Explorers"
(siehe Feedback-Memory feedback_no_auto_optimizer.md): Filter im Investitionen-Tab,
der Massnahmen mit unterdurchschnittlicher Foerderquote als Kandidaten fuer
zusaetzliche Foerdermittel-Akquise hervorhebt.

Bewusst KEINE Automatik/Bewertung - nur eine sortierte Kandidatenliste mit
Kontext-Hinweistext. Die Auswahl/Priorisierung bleibt beim Stadtrat/der Verwaltung.

Datenbasis (foerderquote_pct, eigenanteil_gesamt) existiert bereits pro Massnahme
in budget_data.json (siehe generate_json.py::make_investitionsprojekte), keine
neue Pipeline noetig.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "index.html")

with open(HTML_PATH, "rb") as f:
    content = f.read().decode("utf-8")

backticks_before = content.count("`")


def nl(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\n", "\r\n")


def must_replace(old, new, label):
    global content
    n = content.count(old)
    if n != 1:
        raise SystemExit(f"[FEHLER] Anker '{label}' kommt {n}x vor (erwartet 1x). Abbruch ohne Aenderung.")
    content = content.replace(old, new, 1)


# ─────────────────────────────────────────────────────────────────────────
# 1) Neuer Filter-Button "Förderpotenzial"
# ─────────────────────────────────────────────────────────────────────────
must_replace(
    nl(
        '        <button onclick="setInvFilter(\'neu\')"\n'
        '          class="inv-filter-btn px-3 py-1 rounded-full text-xs border border-slate-600 text-slate-400"\n'
        '          data-filter="neu">Neu</button>\n'
        '      </div>'
    ),
    nl(
        '        <button onclick="setInvFilter(\'neu\')"\n'
        '          class="inv-filter-btn px-3 py-1 rounded-full text-xs border border-slate-600 text-slate-400"\n'
        '          data-filter="neu">Neu</button>\n'
        '        <button onclick="setInvFilter(\'foerderpotenzial\')"\n'
        '          class="inv-filter-btn px-3 py-1 rounded-full text-xs border border-emerald-700 text-emerald-400"\n'
        '          data-filter="foerderpotenzial"\n'
        '          title="Ma&szlig;nahmen mit unterdurchschnittlicher F&ouml;rderquote &ndash; Kandidaten zur Pr&uuml;fung, keine Automatik">F&ouml;rderpotenzial</button>\n'
        '      </div>'
    ),
    "filter-button",
)

# ─────────────────────────────────────────────────────────────────────────
# 2) Info-Banner (analog zum bestehenden TP-Filter-Banner), erklaert das
#    Konzept und zeigt den berechneten Durchschnitt - nur Kontext, keine
#    Wertung.
# ─────────────────────────────────────────────────────────────────────────
must_replace(
    nl(
        '          &times; Filter entfernen\n'
        '        </button>\n'
        '      </div>\n'
        '      <input id="inv-search" type="text" placeholder="Ma&szlig;nahme suchen&hellip;"'
    ),
    nl(
        '          &times; Filter entfernen\n'
        '        </button>\n'
        '      </div>\n'
        '      <div id="inv-foerder-info" class="hidden w-full flex items-center\n'
        '           gap-2 px-3 py-1.5 rounded-lg bg-emerald-900/20 border border-emerald-700/50 text-xs">\n'
        '        <span class="text-emerald-300">&#x1F4A1; F&ouml;rderpotenzial:</span>\n'
        '        <span id="inv-foerder-info-text" class="text-emerald-200 flex-1"></span>\n'
        '      </div>\n'
        '      <input id="inv-search" type="text" placeholder="Ma&szlig;nahme suchen&hellip;"'
    ),
    "foerder-banner",
)

# ─────────────────────────────────────────────────────────────────────────
# 3) JS: renderInvTable() - Foerderpotenzial-Filter + eigener Sort + Banner
# ─────────────────────────────────────────────────────────────────────────
must_replace(
    nl(
        '  var filtered = (IP.massnahmen || []).filter(function(m) {\n'
        '    if (m.letzte_edition !== IP.aktuelles_jahr) return false;\n'
        '    if (_invFilter !== "alle" && m.status !== _invFilter) return false;\n'
        '    if (_invTpFilter && m.tp_nr !== _invTpFilter) return false;\n'
        '    if (query && m.bezeichnung.toLowerCase().indexOf(query) === -1 && m.investitionsnummer.indexOf(query) === -1) return false;\n'
        '    return true;\n'
        '  }).sort(function(a, b) { return b.aus_ansatz_aktuell - a.aus_ansatz_aktuell; });'
    ),
    nl(
        '  var FOERDER_MIN_VOLUMEN = 50000;\n'
        '  var foerderKandidaten = (IP.massnahmen || []).filter(function(m) {\n'
        '    return m.letzte_edition === IP.aktuelles_jahr && m.foerderquote_pct != null && m.aus_gesamt >= FOERDER_MIN_VOLUMEN;\n'
        '  });\n'
        '  var foerderAvgQuote = null;\n'
        '  if (foerderKandidaten.length) {\n'
        '    foerderAvgQuote = foerderKandidaten.reduce(function(s, m) { return s + m.foerderquote_pct; }, 0) / foerderKandidaten.length;\n'
        '  }\n'
        '  var foerderInfoEl  = document.getElementById("inv-foerder-info");\n'
        '  var foerderInfoTxt = document.getElementById("inv-foerder-info-text");\n'
        '  if (_invFilter === "foerderpotenzial") {\n'
        '    if (foerderInfoEl) foerderInfoEl.classList.remove("hidden");\n'
        '    if (foerderInfoTxt) foerderInfoTxt.textContent =\n'
        '      "Ma\\u00dfnahmen mit F\\u00f6rderquote unter dem Durchschnitt (" +\n'
        '      (foerderAvgQuote != null ? foerderAvgQuote.toFixed(1) : "\\u2013") +\n'
        '      " %) \\u2013 m\\u00f6gliche Kandidaten f\\u00fcr zus\\u00e4tzliche F\\u00f6rdermittel-Akquise, sortiert nach H\\u00f6he des Eigenanteils. " +\n'
        '      "Keine automatische Bewertung \\u2013 nur Orientierung f\\u00fcr die Pr\\u00fcfung durch Verwaltung/Stadtrat.";\n'
        '  } else if (foerderInfoEl) {\n'
        '    foerderInfoEl.classList.add("hidden");\n'
        '  }\n'
        '\n'
        '  var filtered = (IP.massnahmen || []).filter(function(m) {\n'
        '    if (m.letzte_edition !== IP.aktuelles_jahr) return false;\n'
        '    if (_invFilter === "foerderpotenzial") {\n'
        '      if (foerderAvgQuote == null || m.foerderquote_pct == null || m.aus_gesamt < FOERDER_MIN_VOLUMEN) return false;\n'
        '      if (m.foerderquote_pct >= foerderAvgQuote) return false;\n'
        '    } else if (_invFilter !== "alle" && m.status !== _invFilter) {\n'
        '      return false;\n'
        '    }\n'
        '    if (_invTpFilter && m.tp_nr !== _invTpFilter) return false;\n'
        '    if (query && m.bezeichnung.toLowerCase().indexOf(query) === -1 && m.investitionsnummer.indexOf(query) === -1) return false;\n'
        '    return true;\n'
        '  }).sort(function(a, b) {\n'
        '    if (_invFilter === "foerderpotenzial") return b.eigenanteil_gesamt - a.eigenanteil_gesamt;\n'
        '    return b.aus_ansatz_aktuell - a.aus_ansatz_aktuell;\n'
        '  });'
    ),
    "js-filter-sort",
)

backticks_after = content.count("`")
if backticks_before != backticks_after:
    raise SystemExit(f"[FEHLER] Backtick-Anzahl geaendert: vorher {backticks_before}, nachher {backticks_after}. Abbruch, Datei NICHT geschrieben.")
if backticks_after % 2 != 0:
    raise SystemExit(f"[FEHLER] Backtick-Anzahl ungerade ({backticks_after}). Abbruch, Datei NICHT geschrieben.")

with open(HTML_PATH, "wb") as f:
    f.write(content.encode("utf-8"))

print(f"[OK] index.html gepatcht. Backticks: {backticks_before} -> {backticks_after}")
