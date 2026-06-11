"""
patch_evidenz_detail.py — Ergaenzt Evidenzbasis-UI um Detail-Toggle mit Kosten-Vorteile.

Ersetzt in index.html:
  1. Den Sidebar-Block (openEvSidebar + Monkey-Patch) — Detail-Button per Evidenz-Karte
  2. Den Infothek-Block (renderHskInfothek + Monkey-Patch) — Detail-Toggle pro Zeile

Technisch:
  - _evDetailToggle(btn) liest data-ev-detail / data-ev-open / data-ev-close vom Button
  - Kein Argument-Quoting-Problem: onclick="..." uebergibt nur 'this', Labels in data-Attrs
  - HTML-Entities fuer Symbole (&#9650; &#9660;), kein Unicode im JS-Source

Idempotent: ueberspringt wenn '_evDetailToggle' bereits in Datei vorhanden.
CRLF-Pflicht + Backtick-Parity.
"""

PATCH_FILE  = "index.html"
BACKUP_FILE = "index.html.bak_evidenz_detail"

IIFE_END = "})();\n"

# Anker-Strings werden dynamisch aus der Datei gelesen (vermeidet Box-Drawing-Encoding-Probleme)
def get_comment_line(content, keyword):
    """Gibt die vollstaendige Kommentar-Zeile zurueck, die 'keyword' enthaelt."""
    idx = content.find(keyword)
    if idx == -1:
        raise AssertionError(f"Schluesselwort {keyword!r} nicht in Datei gefunden")
    ls = content.rfind('\n', 0, idx) + 1
    le = content.find('\n', idx)
    return content[ls:le]

# ---------------------------------------------------------------------------
# Neuer Sidebar-Block  (openEvSidebar + closeEvSidebar + Monkey-Patches)
# Funktion _evDetailToggle(btn) liest Labels aus data-Attributen des Buttons.
# ---------------------------------------------------------------------------
NEW_SIDEBAR_BLOCK = (
    "\n"
    "// Hilfsfunktion: Detail-Toggle fuer Kosten-Vorteile-Sektionen\n"
    "// Labels werden aus data-ev-open / data-ev-close des Buttons gelesen\n"
    "function _evDetailToggle(btn) {\n"
    "  var id = btn.getAttribute('data-ev-detail');\n"
    "  var el = id ? document.getElementById(id) : null;\n"
    "  if (!el) return;\n"
    "  var hidden = el.classList.contains('hidden');\n"
    "  el.classList.toggle('hidden');\n"
    "  btn.innerHTML = hidden\n"
    "    ? btn.getAttribute('data-ev-open')\n"
    "    : btn.getAttribute('data-ev-close');\n"
    "}\n"
    "\n"
    "function openEvSidebar(p) {\n"
    "  var sb = document.getElementById('ev-sidebar');\n"
    "  var prodEl = document.getElementById('ev-sidebar-prod');\n"
    "  var content = document.getElementById('ev-sidebar-content');\n"
    "  if (!sb || !content) return;\n"
    "\n"
    "  prodEl.innerHTML = escHtml(p.bezeichnung) +\n"
    "    ' <span class=\"ml-1 font-mono\">' + escHtml(p.produkt_nummer) + '</span>';\n"
    "\n"
    "  var evList = p.evidenz_basis || [];\n"
    "  if (!evList.length) {\n"
    "    content.innerHTML = '<div class=\"text-slate-500\">Keine Evidenz vorhanden.</div>';\n"
    "  } else {\n"
    "    content.innerHTML = evList.map(function(ev, idx) {\n"
    "      var detailId = 'sb-ev-detail-' + idx;\n"
    "\n"
    "      var kvHtml = '';\n"
    "      if (ev.kosten_vorteile && ev.kosten_vorteile.length) {\n"
    "        kvHtml =\n"
    "          '<div id=\"' + detailId + '\" class=\"hidden mt-3 rounded' +\n"
    "          ' bg-slate-900/60 border border-slate-700/50 p-2\">' +\n"
    "            '<div class=\"text-xs text-slate-500 font-medium mb-2' +\n"
    "            ' uppercase tracking-wide\">Kosten-Vorteile</div>' +\n"
    "            ev.kosten_vorteile.map(function(kv) {\n"
    "              return '<div class=\"mb-2 pb-2 border-b border-slate-700/30\">' +\n"
    "                '<div class=\"flex justify-between gap-2 mb-0.5\">' +\n"
    "                  '<span class=\"text-xs font-medium text-slate-300 leading-snug\">' +\n"
    "                    escHtml(kv.beispiel) +\n"
    "                  '</span>' +\n"
    "                  '<span class=\"text-xs text-blue-300 font-semibold' +\n"
    "                  ' whitespace-nowrap shrink-0\">' +\n"
    "                    escHtml(kv.prozent) +\n"
    "                  '</span>' +\n"
    "                '</div>' +\n"
    "                '<div class=\"text-xs text-green-300 mb-0.5\">' +\n"
    "                  escHtml(kv.absolut) +\n"
    "                '</div>' +\n"
    "                '<div class=\"text-xs text-slate-400 leading-relaxed\">' +\n"
    "                  escHtml(kv.beschreibung) +\n"
    "                '</div>' +\n"
    "              '</div>';\n"
    "            }).join('') +\n"
    "          '</div>';\n"
    "      }\n"
    "\n"
    "      var detailBtn = (ev.kosten_vorteile && ev.kosten_vorteile.length)\n"
    "        ? '<button onclick=\"_evDetailToggle(this)\"' +\n"
    "            ' data-ev-detail=\"' + detailId + '\"' +\n"
    "            ' data-ev-open=\"&#9650;&ensp;Kosten-Vorteile\"' +\n"
    "            ' data-ev-close=\"&#9660;&ensp;Kosten-Vorteile\"' +\n"
    "            ' class=\"inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded' +\n"
    "            ' bg-slate-700/50 text-slate-300 hover:bg-slate-600/60' +\n"
    "            ' border border-slate-600/50 transition-colors\">' +\n"
    "            '&#9660;&ensp;Kosten-Vorteile</button>'\n"
    "        : '';\n"
    "\n"
    "      return '<div class=\"rounded border border-slate-700 bg-slate-800/60 p-3\">' +\n"
    "        '<div class=\"text-blue-300 font-medium text-xs mb-2 leading-tight\">' +\n"
    "          escHtml(ev.titel) +\n"
    "        '</div>' +\n"
    "        '<div class=\"text-slate-300 leading-relaxed text-xs mb-3\">' +\n"
    "          escHtml(ev.kernthese) +\n"
    "        '</div>' +\n"
    "        '<div class=\"flex flex-wrap gap-2\">' +\n"
    "          detailBtn +\n"
    "          '<a href=\"' + escHtml(ev.download_url) + '\"' +\n"
    "          ' target=\"_blank\" rel=\"noopener noreferrer\"' +\n"
    "          ' class=\"inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded' +\n"
    "          ' bg-blue-800/60 text-blue-200 hover:bg-blue-700/80' +\n"
    "          ' border border-blue-700/50 transition-colors\">' +\n"
    "            '&#x2913;&ensp;Dokument herunterladen' +\n"
    "          '</a>' +\n"
    "        '</div>' +\n"
    "        kvHtml +\n"
    "      '</div>';\n"
    "    }).join('');\n"
    "  }\n"
    "  sb.classList.remove('hidden');\n"
    "}\n"
    "\n"
    "function closeEvSidebar() {\n"
    "  var sb = document.getElementById('ev-sidebar');\n"
    "  if (sb) sb.classList.add('hidden');\n"
    "}\n"
    "\n"
    "// Schliessen bei Klick ausserhalb der Sidebar\n"
    "document.addEventListener('click', function(e) {\n"
    "  var sb = document.getElementById('ev-sidebar');\n"
    "  if (!sb || sb.classList.contains('hidden')) return;\n"
    "  if (!sb.contains(e.target) && !e.target.classList.contains('ev-btn')) {\n"
    "    closeEvSidebar();\n"
    "  }\n"
    "});\n"
    "\n"
    "// Monkey-Patch renderSimListe: Evidenz-Buttons nach Render hinzufuegen\n"
    "(function() {\n"
    "  var _rsl_ev_orig = renderSimListe;\n"
    "  renderSimListe = function() {\n"
    "    _rsl_ev_orig.apply(this, arguments);\n"
    "    if (!DATA || !DATA.simulator_produkte) return;\n"
    "    DATA.simulator_produkte.forEach(function(p) {\n"
    "      if (!p.evidenz_basis || !p.evidenz_basis.length) return;\n"
    "      var zoneEl = document.getElementById('zone-' + p.produkt_nummer);\n"
    "      if (!zoneEl) return;\n"
    "      var card = zoneEl.closest ? zoneEl.closest('.card') : null;\n"
    "      if (!card) return;\n"
    "      if (card.querySelector('.ev-btn')) return;\n"
    "      var btn = document.createElement('button');\n"
    "      btn.className = 'ev-btn mt-2 flex items-center gap-1 text-xs text-blue-400' +\n"
    "        ' hover:text-blue-200 transition-colors';\n"
    "      btn.title = 'Wissenschaftliche und juristische Grundlagen';\n"
    "      btn.innerHTML = '&#x24D8;&ensp;Evidenzbasis&thinsp;(' +\n"
    "        p.evidenz_basis.length + ' Dok.)';\n"
    "      btn.onclick = function(e) {\n"
    "        e.stopPropagation();\n"
    "        openEvSidebar(p);\n"
    "      };\n"
    "      card.appendChild(btn);\n"
    "    });\n"
    "  };\n"
    "})();\n"
)

# ---------------------------------------------------------------------------
# Neuer Infothek-Block  (renderHskInfothek + Monkey-Patch renderHsk)
# ---------------------------------------------------------------------------
NEW_INFOTHEK_BLOCK = (
    "\n"
    "function renderHskInfothek() {\n"
    "  var tbody = document.getElementById('hsk-infothek-body');\n"
    "  if (!tbody) return;\n"
    "\n"
    "  var seen = {};\n"
    "  (DATA.simulator_produkte || []).forEach(function(p) {\n"
    "    (p.evidenz_basis || []).forEach(function(ev) {\n"
    "      var key = ev.download_url;\n"
    "      if (!seen[key]) {\n"
    "        seen[key] = { ev: ev, produkte: [] };\n"
    "      }\n"
    "      if (p.produkt_nummer.length >= 5 && parseFloat(p.kk5_2025 || 0) > 0) {\n"
    "        seen[key].produkte.push(escHtml(p.bezeichnung));\n"
    "      }\n"
    "    });\n"
    "  });\n"
    "\n"
    "  var entries = Object.keys(seen).map(function(k) { return seen[k]; });\n"
    "  if (!entries.length) {\n"
    "    tbody.innerHTML = '<tr><td colspan=\"4\" class=\"py-4 text-slate-500 text-sm\">' +\n"
    "      'Keine Quellen hinterlegt.</td></tr>';\n"
    "    return;\n"
    "  }\n"
    "\n"
    "  tbody.innerHTML = entries.map(function(item, idx) {\n"
    "    var ev = item.ev;\n"
    "    var detailId = 'hsk-ev-detail-' + idx;\n"
    "\n"
    "    var prodStr = item.produkte.length\n"
    "      ? item.produkte.join('<br>')\n"
    "      : '<span class=\"text-slate-500 italic\">Gesamtquerschnitt</span>';\n"
    "    var these = escHtml(ev.kernthese).substring(0, 140);\n"
    "    if (ev.kernthese.length > 140) these += '&hellip;';\n"
    "\n"
    "    var kvRows = '';\n"
    "    if (ev.kosten_vorteile && ev.kosten_vorteile.length) {\n"
    "      kvRows = ev.kosten_vorteile.map(function(kv) {\n"
    "        return '<tr class=\"border-t border-slate-700/30\">' +\n"
    "          '<td class=\"py-1.5 pr-3 text-xs text-slate-300 align-top w-36' +\n"
    "          ' leading-snug\">' + escHtml(kv.beispiel) + '</td>' +\n"
    "          '<td class=\"py-1.5 pr-3 text-xs text-green-300 align-top' +\n"
    "          ' whitespace-nowrap\">' + escHtml(kv.absolut) + '</td>' +\n"
    "          '<td class=\"py-1.5 pr-3 text-xs text-blue-300 align-top' +\n"
    "          ' font-semibold whitespace-nowrap\">' + escHtml(kv.prozent) + '</td>' +\n"
    "          '<td class=\"py-1.5 text-xs text-slate-400 align-top' +\n"
    "          ' leading-relaxed\">' + escHtml(kv.beschreibung) + '</td>' +\n"
    "        '</tr>';\n"
    "      }).join('');\n"
    "    }\n"
    "\n"
    "    var detailBtn = (ev.kosten_vorteile && ev.kosten_vorteile.length)\n"
    "      ? '<button onclick=\"_evDetailToggle(this)\"' +\n"
    "          ' data-ev-detail=\"' + detailId + '\"' +\n"
    "          ' data-ev-open=\"Detail&thinsp;&#9650;\"' +\n"
    "          ' data-ev-close=\"Detail&thinsp;&#9660;\"' +\n"
    "          ' class=\"inline-flex items-center gap-1 text-xs px-2 py-1 rounded' +\n"
    "          ' bg-slate-700/50 text-slate-300 hover:bg-slate-600/60' +\n"
    "          ' border border-slate-600/50 whitespace-nowrap transition-colors\">' +\n"
    "          'Detail&thinsp;&#9660;</button>'\n"
    "      : '';\n"
    "\n"
    "    var mainRow =\n"
    "      '<tr class=\"border-b border-slate-700/40 hover:bg-slate-800/20\">' +\n"
    "        '<td class=\"py-3 pr-4 align-top w-52\">' +\n"
    "          '<div class=\"font-medium text-blue-300 text-xs leading-snug\">' +\n"
    "            escHtml(ev.titel) +\n"
    "          '</div>' +\n"
    "        '</td>' +\n"
    "        '<td class=\"py-3 pr-4 align-top text-xs text-slate-400 w-48\">' +\n"
    "          prodStr +\n"
    "        '</td>' +\n"
    "        '<td class=\"py-3 pr-4 align-top text-xs text-slate-300 leading-relaxed\">' +\n"
    "          these +\n"
    "        '</td>' +\n"
    "        '<td class=\"py-3 align-top\">' +\n"
    "          '<div class=\"flex flex-col gap-1\">' +\n"
    "            '<a href=\"' + escHtml(ev.download_url) + '\"' +\n"
    "            ' target=\"_blank\" rel=\"noopener noreferrer\"' +\n"
    "            ' class=\"inline-flex items-center gap-1 text-xs px-2 py-1 rounded' +\n"
    "            ' bg-blue-800/40 text-blue-300 hover:bg-blue-700/60' +\n"
    "            ' border border-blue-700/50 whitespace-nowrap transition-colors\">' +\n"
    "              '&#x2913;&ensp;PDF' +\n"
    "            '</a>' +\n"
    "            detailBtn +\n"
    "          '</div>' +\n"
    "        '</td>' +\n"
    "      '</tr>';\n"
    "\n"
    "    var detailRow = kvRows\n"
    "      ? '<tr id=\"' + detailId + '\" class=\"hidden\">' +\n"
    "          '<td colspan=\"4\" class=\"pb-3 pt-0 px-2\">' +\n"
    "            '<div class=\"rounded bg-slate-800/40 border border-slate-700/40 p-3\">' +\n"
    "              '<div class=\"text-xs text-slate-500 font-medium mb-2' +\n"
    "              ' uppercase tracking-wide\">Kosten-Vorteile &ndash; Quellenbelege</div>' +\n"
    "              '<table class=\"w-full\">' +\n"
    "                '<thead><tr class=\"text-left text-slate-500 text-xs\">' +\n"
    "                  '<th class=\"pb-1 pr-3 font-medium w-36\">Beispiel</th>' +\n"
    "                  '<th class=\"pb-1 pr-3 font-medium\">Absolut</th>' +\n"
    "                  '<th class=\"pb-1 pr-3 font-medium\">Prozent</th>' +\n"
    "                  '<th class=\"pb-1 font-medium\">Erl&auml;uterung</th>' +\n"
    "                '</tr></thead>' +\n"
    "                '<tbody>' + kvRows + '</tbody>' +\n"
    "              '</table>' +\n"
    "            '</div>' +\n"
    "          '</td>' +\n"
    "        '</tr>'\n"
    "      : '';\n"
    "\n"
    "    return mainRow + detailRow;\n"
    "  }).join('');\n"
    "}\n"
    "\n"
    "// Monkey-Patch renderHsk: Infothek nach dem HSK-Render aufrufen\n"
    "(function() {\n"
    "  var _rh_infothek_orig = renderHsk;\n"
    "  renderHsk = function() {\n"
    "    _rh_infothek_orig.apply(this, arguments);\n"
    "    renderHskInfothek();\n"
    "  };\n"
    "})();\n"
)

# ---------------------------------------------------------------------------
# Haupt-Patch
# ---------------------------------------------------------------------------
def replace_block(content, start_keyword, new_block_template):
    """
    Findet den Block per Keyword (Zeile wird dynamisch aus content gelesen),
    ersetzt bis zum naechsten })();  (inklusiv).
    new_block_template: erster Zeilenplatz wird durch die echte Kommentar-Zeile ersetzt.
    """
    anchor_line = get_comment_line(content, start_keyword)
    start = content.find(anchor_line)
    end = content.find(IIFE_END, start)
    if end == -1:
        raise AssertionError("IIFE-Ende '})();' nicht gefunden")
    end += len(IIFE_END)
    old = content[start:end]
    # Erste Zeile des Templates durch exakte Anker-Zeile aus Datei ersetzen
    new_block = anchor_line + "\n" + new_block_template
    return content.replace(old, new_block, 1)


def main():
    import shutil, os

    with open(PATCH_FILE, "rb") as f:
        raw = f.read()
    content = raw.decode("utf-8")

    bc_before = content.count("\x60")
    print(f"Backtick-Anzahl vor Patch: {bc_before}")

    shutil.copy2(PATCH_FILE, BACKUP_FILE)
    print(f"Backup: {BACKUP_FILE}")

    if "data-ev-detail" in content:
        print("[SKIP] data-ev-detail bereits vorhanden — kein Patch noetig")
        return

    # LF-normalisieren fuer saubere Suche + Ersetzung
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # ── Patch 1: Sidebar-Block ──────────────────────────────────────────────
    content = replace_block(content, 'Evidenzbasis-Sidebar', NEW_SIDEBAR_BLOCK)
    print("Patch 1 OK: Sidebar-Block (openEvSidebar + _evDetailToggle) ersetzt")

    # ── Patch 2: Infothek-Block ─────────────────────────────────────────────
    content = replace_block(content, 'Evidenzbasis-Infothek (HSK-Tab)', NEW_INFOTHEK_BLOCK)
    print("Patch 2 OK: Infothek-Block (renderHskInfothek) ersetzt")

    # ── Validierung ─────────────────────────────────────────────────────────
    bc_after = content.count("\x60")
    assert bc_after == bc_before, \
        f"FEHLER: Backtick-Anzahl geaendert: {bc_before} -> {bc_after}"
    print(f"Backtick-Anzahl: {bc_after} (unveraendert)")

    assert "_evDetailToggle" in content, "FEHLER: _evDetailToggle fehlt"
    assert "kosten_vorteile" in content,  "FEHLER: kosten_vorteile fehlt"
    assert "data-ev-detail" in content,  "FEHLER: data-ev-detail fehlt"

    # ── Speichern (CRLF) ────────────────────────────────────────────────────
    content = content.replace("\n", "\r\n")
    with open(PATCH_FILE, "wb") as f:
        f.write(content.encode("utf-8"))
    print(f"Gespeichert: {PATCH_FILE} ({os.path.getsize(PATCH_FILE):,} Bytes)")
    print("Fertig.")


if __name__ == "__main__":
    main()
