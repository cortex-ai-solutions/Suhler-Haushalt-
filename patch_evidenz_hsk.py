"""
patch_evidenz_hsk.py — Fuegt Evidenzbasis-Infothek als permanenten Abschnitt
im HSK-Tab ein.

Patcht index.html mit:
  1. HTML: Neues Card-Element #hsk-infothek am Ende des tab-hsk-Divs
     (Tabelle: Quelle | Betroffene Produkte | Kernthese | Download)
  2. JS:   renderHskInfothek() + Monkey-Patch renderHsk um Aufruf zu erganzen

Idempotent: Prueft ob #hsk-infothek bereits vorhanden, ueberspringt dann.
CRLF-Pflicht + Backtick-Parity wie alle anderen Patch-Skripte.
"""

PATCH_FILE  = "index.html"
BACKUP_FILE = "index.html.bak_evidenz_hsk"

# ---------------------------------------------------------------------------
# Patch 1 — HTML-Abschnitt (wird vor </div> des tab-hsk eingefuegt)
# Anker: einzigartiger Abschluss des Massnahmen-Katalog-Blocks
# ---------------------------------------------------------------------------
# Achtung: Anker-String enthaelt Unicode-Box-Zeichen (== in Comment) —
# daher raw-String und utf-8 Datei-IO.
HTML_ANCHOR = (
    "        <tbody id=\"hsk-tabelle-body\"></tbody>\r\n"
    "      </table>\r\n"
    "    </div>\r\n"
    "  </div>\r\n"
    "\r\n"
    "</div>"
)

INFOTHEK_HTML = (
    "        <tbody id=\"hsk-tabelle-body\"></tbody>\r\n"
    "      </table>\r\n"
    "    </div>\r\n"
    "  </div>\r\n"
    "\r\n"
    "  <!-- Evidenzbasis & Quellennachweis -->\r\n"
    "  <div class=\"card p-5 mt-6\" id=\"hsk-infothek\">\r\n"
    "    <div class=\"flex items-center justify-between mb-4\">\r\n"
    "      <div>\r\n"
    "        <div class=\"section-title\">&#x24D8;&ensp;Evidenzbasis &amp; Quellennachweis</div>\r\n"
    "        <div class=\"note mt-1\">Wissenschaftliche und juristische Grundlagen"
    " f&uuml;r Konsolidierungsma&szlig;nahmen im Simulator</div>\r\n"
    "      </div>\r\n"
    "    </div>\r\n"
    "    <div class=\"overflow-x-auto\">\r\n"
    "      <table class=\"w-full text-sm\">\r\n"
    "        <thead>\r\n"
    "          <tr class=\"text-left text-slate-400 text-xs border-b border-slate-700\">\r\n"
    "            <th class=\"py-2 pr-4 font-medium\">Quelle</th>\r\n"
    "            <th class=\"py-2 pr-4 font-medium\">Betroffene Produkte</th>\r\n"
    "            <th class=\"py-2 pr-4 font-medium\">Kernthese</th>\r\n"
    "            <th class=\"py-2 font-medium\">Dokument</th>\r\n"
    "          </tr>\r\n"
    "        </thead>\r\n"
    "        <tbody id=\"hsk-infothek-body\"></tbody>\r\n"
    "      </table>\r\n"
    "    </div>\r\n"
    "  </div>\r\n"
    "\r\n"
    "</div>"
)

# ---------------------------------------------------------------------------
# Patch 2 — JavaScript (renderHskInfothek + Monkey-Patch renderHsk)
# ---------------------------------------------------------------------------
INFOTHEK_JS = r"""
// ── Evidenzbasis-Infothek (HSK-Tab) ─────────────────────────────────────

function renderHskInfothek() {
  var tbody = document.getElementById('hsk-infothek-body');
  if (!tbody) return;

  // Alle unique evidenz_basis aus simulator_produkte sammeln
  var seen = {};
  (DATA.simulator_produkte || []).forEach(function(p) {
    (p.evidenz_basis || []).forEach(function(ev) {
      var key = ev.download_url;
      if (!seen[key]) {
        seen[key] = { ev: ev, produkte: [] };
      }
      // Nur 6-stellige (echte) Produkte anzeigen, keine 4-stelligen Rollups
      if (p.produkt_nummer.length >= 5 && parseFloat(p.kk5_2025 || 0) > 0) {
        seen[key].produkte.push(escHtml(p.bezeichnung));
      }
    });
  });

  var entries = Object.keys(seen).map(function(k) { return seen[k]; });
  if (!entries.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="py-4 text-slate-500 text-sm">' +
      'Keine Quellen hinterlegt.</td></tr>';
    return;
  }

  tbody.innerHTML = entries.map(function(item) {
    var ev = item.ev;
    var prodStr = item.produkte.length
      ? item.produkte.join('<br>')
      : '<span class="text-slate-500 italic">Gesamtquerschnitt</span>';
    var these = escHtml(ev.kernthese).substring(0, 140);
    if (ev.kernthese.length > 140) these += '&hellip;';

    return '<tr class="border-b border-slate-700/40 hover:bg-slate-800/20">' +
      '<td class="py-3 pr-4 align-top w-52">' +
        '<div class="font-medium text-blue-300 text-xs leading-snug">' +
          escHtml(ev.titel) +
        '</div>' +
      '</td>' +
      '<td class="py-3 pr-4 align-top text-xs text-slate-400 w-48">' +
        prodStr +
      '</td>' +
      '<td class="py-3 pr-4 align-top text-xs text-slate-300 leading-relaxed">' +
        these +
      '</td>' +
      '<td class="py-3 align-top">' +
        '<a href="' + escHtml(ev.download_url) + '"' +
          ' target="_blank" rel="noopener noreferrer"' +
          ' class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded' +
          ' bg-blue-800/40 text-blue-300 hover:bg-blue-700/60' +
          ' border border-blue-700/50 whitespace-nowrap transition-colors">' +
          '&#x2913;&ensp;PDF' +
        '</a>' +
      '</td>' +
    '</tr>';
  }).join('');
}

// Monkey-Patch renderHsk: Infothek nach dem HSK-Render aufrufen
(function() {
  var _rh_infothek_orig = renderHsk;
  renderHsk = function() {
    _rh_infothek_orig.apply(this, arguments);
    renderHskInfothek();
  };
})();
"""

ANCHOR_SCRIPT_CLOSE = "</script>"

# ---------------------------------------------------------------------------
# Haupt-Patch
# ---------------------------------------------------------------------------
def main():
    import shutil, os

    with open(PATCH_FILE, "rb") as f:
        raw = f.read()
    content = raw.decode("utf-8")

    bc_before = content.count("\x60")
    print(f"Backtick-Anzahl vor Patch: {bc_before}")

    shutil.copy2(PATCH_FILE, BACKUP_FILE)
    print(f"Backup: {BACKUP_FILE}")

    # ── Patch 1: HTML ──────────────────────────────────────────────────────
    if 'id="hsk-infothek"' in content:
        print("[SKIP] hsk-infothek bereits vorhanden — ueberspringe HTML-Patch")
    else:
        assert HTML_ANCHOR in content, \
            "FEHLER: HTML-Anker 'hsk-tabelle-body...}</div>' nicht gefunden"
        content = content.replace(HTML_ANCHOR, INFOTHEK_HTML, 1)
        print("Patch 1 OK: hsk-infothek HTML eingefuegt")

    # ── Patch 2: JavaScript ────────────────────────────────────────────────
    if "renderHskInfothek" in content:
        print("[SKIP] renderHskInfothek bereits vorhanden — ueberspringe JS-Patch")
    else:
        last_idx = content.rfind(ANCHOR_SCRIPT_CLOSE)
        assert last_idx > 0, f"Anker '{ANCHOR_SCRIPT_CLOSE}' nicht gefunden"
        content = content[:last_idx] + INFOTHEK_JS + "\r\n" + content[last_idx:]
        print("Patch 2 OK: renderHskInfothek JS eingefuegt")

    # ── Validierung ────────────────────────────────────────────────────────
    bc_after = content.count("\x60")
    assert bc_after == bc_before, \
        f"FEHLER: Backtick-Anzahl geaendert: {bc_before} -> {bc_after}"
    print(f"Backtick-Anzahl nach Patch: {bc_after} (unveraendert)")

    # ── Speichern (CRLF) ──────────────────────────────────────────────────
    content = content.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    with open(PATCH_FILE, "wb") as f:
        f.write(content.encode("utf-8"))
    print(f"Gespeichert: {PATCH_FILE} ({os.path.getsize(PATCH_FILE):,} Bytes)")
    print("Fertig.")

if __name__ == "__main__":
    main()
