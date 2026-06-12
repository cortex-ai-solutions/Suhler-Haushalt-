#!/usr/bin/env python3
"""
patch_mobile_nav.py
Hamburger-Dropdown-Navigation fuer mobile Displays.
Auf Bildschirmen < 768px wird die Tab-Leiste durch ein Dropdown ersetzt.
"""

HTML_PATH = "index.html"
MARKER = 'id="mobile-nav"'

# ── CSS ──────────────────────────────────────────────────────────────────────
NEW_CSS = (
    "\r\n"
    "  @media (max-width: 767px) { .tabbar { display: none !important; } }\r\n"
    "  #mobile-nav { position: relative; margin-bottom: 1rem; }\r\n"
    "  #mobile-nav-btn { display: flex; align-items: center; justify-content: space-between;"
    " width: 100%; padding: 0.6rem 1rem; background: #1e293b;"
    " border: 1px solid #334155; border-radius: 0.5rem;"
    " color: #e2e8f0; font-size: 0.875rem; cursor: pointer; }\r\n"
    "  #mobile-nav-btn:hover { background: #273549; }\r\n"
    "  #mobile-nav-dropdown { position: absolute; top: calc(100% + 4px);"
    " left: 0; right: 0; background: #1e293b; border: 1px solid #334155;"
    " border-radius: 0.5rem; z-index: 50; overflow: hidden; box-shadow: 0 4px 16px #0008; }\r\n"
    "  .mobile-tab-item { padding: 0.65rem 1rem; color: #94a3b8; font-size: 0.875rem; cursor: pointer; }\r\n"
    "  .mobile-tab-item:hover { background: #273549; color: #e2e8f0; }\r\n"
    "  .mobile-tab-item.active { background: #1e3a5f; color: #60a5fa; font-weight: 500; }\r\n"
)

# ── HTML ─────────────────────────────────────────────────────────────────────
NEW_HTML = (
    "<!-- Mobile Navigation -->\r\n"
    '<div class="md:hidden" id="mobile-nav">\r\n'
    '  <button type="button" id="mobile-nav-btn" onclick="_mobileNavToggle()">\r\n'
    '    <span id="mobile-nav-label">\xdcberblick</span>\r\n'
    "    <span>&#9660;</span>\r\n"
    "  </button>\r\n"
    '  <div id="mobile-nav-dropdown" class="hidden">\r\n'
    '    <div class="mobile-tab-item active" data-tab="overview">\xdcberblick</div>\r\n'
    '    <div class="mobile-tab-item" data-tab="details">Details</div>\r\n'
    '    <div class="mobile-tab-item" data-tab="personal">Personal</div>\r\n'
    '    <div class="mobile-tab-item" data-tab="jahresvergleich">Jahresvergleich</div>\r\n'
    '    <div class="mobile-tab-item" data-tab="zeitreihe">Zeitreihe</div>\r\n'
    '    <div class="mobile-tab-item" data-tab="hsk">HSK &amp; Konsolidierung</div>\r\n'
    '    <div class="mobile-tab-item" data-tab="simulator">Konsolidierungs-Simulator</div>\r\n'
    "  </div>\r\n"
    "</div>\r\n"
)

# ── JS ───────────────────────────────────────────────────────────────────────
_js_lines = [
    "// ── Mobile Navigation Hamburger-Dropdown ───────────────────────────────",
    "(function() {",
    "  window._mobileNavToggle = function() {",
    '    var dd = document.getElementById("mobile-nav-dropdown");',
    '    if (dd) dd.classList.toggle("hidden");',
    "  };",
    "",
    '  document.addEventListener("click", function(e) {',
    '    var nav = document.getElementById("mobile-nav");',
    "    if (nav && !nav.contains(e.target)) {",
    '      var dd = document.getElementById("mobile-nav-dropdown");',
    '      if (dd) dd.classList.add("hidden");',
    "    }",
    "  });",
    "",
    '  document.querySelectorAll(".mobile-tab-item").forEach(function(item) {',
    '    item.addEventListener("click", function() {',
    '      var tabName = item.getAttribute("data-tab");',
    '      document.querySelectorAll(".mobile-tab-item").forEach(function(i) {',
    '        i.classList.remove("active");',
    "      });",
    '      item.classList.add("active");',
    '      var label = document.getElementById("mobile-nav-label");',
    "      if (label) label.textContent = item.textContent;",
    '      var dd = document.getElementById("mobile-nav-dropdown");',
    '      if (dd) dd.classList.add("hidden");',
    "      var desktopTab = document.querySelector(",
    "        '#tabbar .tab[data-tab=\"' + tabName + '\"]'",
    "      );",
    "      if (desktopTab) desktopTab.click();",
    "    });",
    "  });",
    "})();",
    "",
]
NEW_JS = "\r\n".join(_js_lines) + "\r\n"


def patch():
    with open(HTML_PATH, "rb") as f:
        content = f.read().decode("utf-8")

    if MARKER in content:
        print("[SKIP] Patch already applied.")
        return

    # ── 1. CSS nach .note-Regel einfuegen ─────────────────────────────────────
    css_anchor = ".note { font-size: 0.75rem; color: #64748b; }"
    idx_css = content.find(css_anchor)
    if idx_css == -1:
        print("[ERROR] CSS-Anker (.note) nicht gefunden.")
        return
    after_css = idx_css + len(css_anchor)
    content = content[:after_css] + NEW_CSS + content[after_css:]

    # ── 2. HTML vor .tabbar einfuegen ─────────────────────────────────────────
    html_anchor = '<div class="tabbar" id="tabbar">'
    idx_html = content.find(html_anchor)
    if idx_html == -1:
        print("[ERROR] HTML-Anker (tabbar) nicht gefunden.")
        return
    content = content[:idx_html] + NEW_HTML + content[idx_html:]

    # ── 3. JS vor renderSankey() einfuegen ───────────────────────────────────
    js_anchor = "function renderSankey()"
    idx_js = content.find(js_anchor)
    if idx_js == -1:
        print("[ERROR] JS-Anker (renderSankey) nicht gefunden.")
        return
    content = content[:idx_js] + NEW_JS + content[idx_js:]

    # ── 4. Backtick-Paritaet pruefen ─────────────────────────────────────────
    bc = content.count("\x60")
    if bc % 2 != 0:
        print(f"[WARN] Ungerade Backtick-Anzahl: {bc}")
    else:
        print(f"[OK] Backticks: {bc} (gerade)")

    with open(HTML_PATH, "wb") as f:
        f.write(content.encode("utf-8"))
    print("[OK] patch_mobile_nav.py angewendet.")


if __name__ == "__main__":
    patch()
