"""
patch_evidenz.py — Fuegt Evidenzbasis-UI zum Konsolidierungs-Simulator hinzu.

Patcht index.html mit:
  1. Sidebar-HTML (fixiertes Panel rechts, zeigt Kernthese + Download-Button)
  2. openEvSidebar(p) / closeEvSidebar() JavaScript-Funktionen
  3. Monkey-Patch von renderSimListe: Fuegt Evidenz-Button zu Karten
     mit evidenz_basis hinzu (via post-processing nach Render)

Technische Constraints (CLAUDE.md):
  - CRLF-Pflicht: output immer mit open(..., 'wb') + encode('utf-8')
  - Kein Unicode in JS-Strings: HTML-Entities nutzen
  - Backtick-Anzahl muss GERADE bleiben
  - Kein direktes Template-Literal-Editing: String-Concatenation
"""

PATCH_FILE = "index.html"
BACKUP_FILE = "index.html.bak_evidenz"

# ---------------------------------------------------------------------------
# Pruefroutine
# ---------------------------------------------------------------------------
def check_backticks(content):
    bc = content.count("\x60")
    assert bc % 2 == 0, f"FEHLER: Ungerade Backtick-Anzahl: {bc}"
    return bc

# ---------------------------------------------------------------------------
# Patch 1: Sidebar-HTML direkt vor </body>
# ---------------------------------------------------------------------------
SIDEBAR_HTML = """
<!-- Evidenzbasis-Sidebar -->
<div id="ev-sidebar"
     class="hidden fixed inset-y-0 right-0 w-full max-w-sm bg-slate-900 border-l border-slate-700
            z-50 flex flex-col shadow-2xl overflow-hidden"
     style="top:0;bottom:0;">
  <div class="flex items-center justify-between px-4 py-3 border-b border-slate-700 shrink-0">
    <div class="flex items-center gap-2">
      <span class="text-blue-400 text-lg">&#x24D8;</span>
      <span class="font-semibold text-slate-200 text-sm">Evidenzbasis</span>
    </div>
    <button onclick="closeEvSidebar()"
            class="text-slate-400 hover:text-white text-xl leading-none px-1"
            title="Schlie&szlig;en">&times;</button>
  </div>
  <div id="ev-sidebar-prod" class="px-4 pt-3 shrink-0 text-xs text-slate-500 border-b border-slate-800 pb-2"></div>
  <div id="ev-sidebar-content" class="p-4 overflow-y-auto flex-1 text-sm space-y-4"></div>
</div>
<!-- Ende Evidenzbasis-Sidebar -->"""

ANCHOR_BODY_CLOSE = "</body>"

# ---------------------------------------------------------------------------
# Patch 2: JavaScript-Block (Sidebar-Logik + renderSimListe-Monkey-Patch)
# Am Ende des <script>-Blocks, vor </script>
# ---------------------------------------------------------------------------
EVIDENZ_JS = r"""
// ── Evidenzbasis-Sidebar ──────────────────────────────────────────────────

function openEvSidebar(p) {
  var sb = document.getElementById('ev-sidebar');
  var prodEl = document.getElementById('ev-sidebar-prod');
  var content = document.getElementById('ev-sidebar-content');
  if (!sb || !content) return;

  prodEl.innerHTML = escHtml(p.bezeichnung) +
    ' <span class="ml-1 font-mono">' + escHtml(p.produkt_nummer) + '</span>';

  var evList = p.evidenz_basis || [];
  if (!evList.length) {
    content.innerHTML = '<div class="text-slate-500">Keine Evidenz vorhanden.</div>';
  } else {
    content.innerHTML = evList.map(function(ev) {
      return '<div class="rounded border border-slate-700 bg-slate-800/60 p-3">' +
        '<div class="text-blue-300 font-medium text-xs mb-2 leading-tight">' +
          escHtml(ev.titel) +
        '</div>' +
        '<div class="text-slate-300 leading-relaxed text-xs mb-3">' +
          escHtml(ev.kernthese) +
        '</div>' +
        '<a href="' + escHtml(ev.download_url) + '" target="_blank" rel="noopener noreferrer"' +
          ' class="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded' +
          ' bg-blue-800/60 text-blue-200 hover:bg-blue-700/80 border border-blue-700/50' +
          ' transition-colors">' +
          '&#x2913;&ensp;Dokument herunterladen' +
        '</a>' +
      '</div>';
    }).join('');
  }
  sb.classList.remove('hidden');
}

function closeEvSidebar() {
  var sb = document.getElementById('ev-sidebar');
  if (sb) sb.classList.add('hidden');
}

// Schliessen bei Klick ausserhalb der Sidebar
document.addEventListener('click', function(e) {
  var sb = document.getElementById('ev-sidebar');
  if (!sb || sb.classList.contains('hidden')) return;
  if (!sb.contains(e.target) && !e.target.classList.contains('ev-btn')) {
    closeEvSidebar();
  }
});

// Monkey-Patch renderSimListe: Evidenz-Buttons nach Render hinzufuegen
(function() {
  var _rsl_ev_orig = renderSimListe;
  renderSimListe = function() {
    _rsl_ev_orig.apply(this, arguments);
    if (!DATA || !DATA.simulator_produkte) return;
    DATA.simulator_produkte.forEach(function(p) {
      if (!p.evidenz_basis || !p.evidenz_basis.length) return;
      // Karte per zone-ID lokalisieren (.card ist der direkte Eltern-Container)
      var zoneEl = document.getElementById('zone-' + p.produkt_nummer);
      if (!zoneEl) return;
      var card = zoneEl.closest ? zoneEl.closest('.card') : null;
      if (!card) return;
      if (card.querySelector('.ev-btn')) return; // bereits vorhanden
      var btn = document.createElement('button');
      btn.className = 'ev-btn mt-2 flex items-center gap-1 text-xs text-blue-400' +
        ' hover:text-blue-200 transition-colors';
      btn.title = 'Wissenschaftliche und juristische Grundlagen';
      btn.innerHTML = '&#x24D8;&ensp;Evidenzbasis&thinsp;(' +
        p.evidenz_basis.length + ' Dok.)';
      btn.onclick = function(e) {
        e.stopPropagation();
        openEvSidebar(p);
      };
      card.appendChild(btn);
    });
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

    bc_before = check_backticks(content)
    print(f"Backtick-Anzahl vor Patch: {bc_before}")

    # Sicherheitskopie
    shutil.copy2(PATCH_FILE, BACKUP_FILE)
    print(f"Backup: {BACKUP_FILE}")

    # ── Patch 1: Sidebar-HTML ──────────────────────────────────────────────
    if "ev-sidebar" in content:
        print("[SKIP] Sidebar bereits vorhanden — ueberspringe HTML-Patch")
    else:
        assert ANCHOR_BODY_CLOSE in content, f"Anker '{ANCHOR_BODY_CLOSE}' nicht gefunden"
        content = content.replace(
            ANCHOR_BODY_CLOSE,
            SIDEBAR_HTML + "\r\n" + ANCHOR_BODY_CLOSE,
            1,
        )
        print("Patch 1 OK: Sidebar-HTML eingefuegt")

    # ── Patch 2: Evidenz-JS ────────────────────────────────────────────────
    if "openEvSidebar" in content:
        print("[SKIP] openEvSidebar bereits vorhanden — ueberspringe JS-Patch")
    else:
        # Letztes </script> als Anker
        last_idx = content.rfind(ANCHOR_SCRIPT_CLOSE)
        assert last_idx > 0, f"Anker '{ANCHOR_SCRIPT_CLOSE}' nicht gefunden"
        content = (
            content[:last_idx]
            + EVIDENZ_JS
            + "\r\n"
            + content[last_idx:]
        )
        print("Patch 2 OK: Evidenz-JS eingefuegt")

    # ── Validierung ────────────────────────────────────────────────────────
    bc_after = check_backticks(content)
    print(f"Backtick-Anzahl nach Patch: {bc_after}")
    assert bc_after == bc_before, \
        f"FEHLER: Backtick-Anzahl geaendert: {bc_before} -> {bc_after}"

    # ── Speichern (CRLF) ──────────────────────────────────────────────────
    # Normalisiere alle Zeilenenden auf CRLF
    content = content.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    with open(PATCH_FILE, "wb") as f:
        f.write(content.encode("utf-8"))

    size = os.path.getsize(PATCH_FILE)
    print(f"Gespeichert: {PATCH_FILE} ({size:,} Bytes)")
    print("Fertig — Dashboard bereit zum Testen.")

if __name__ == "__main__":
    main()
