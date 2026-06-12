#!/usr/bin/env python3
"""
patch_sp_tp_detail.py
Fuegt eine aufklappbare TP-Detailansicht (Beamte + Tarif je Teilplan)
in den Stellenplan-Abschnitt des Personal-Tabs ein.
Setzt nach_tp_detail in budget_data.json voraus (generate_json.py 2026-06-12).
"""

HTML_PATH = "index.html"
MARKER = 'id="sp-tp-detail-body"'

# ── Neues HTML (Accordion-Container) ─────────────────────────────────────────
NEW_HTML = (
    '\r\n'
    '    <!-- Stellenplan-TP-Accordion -->\r\n'
    '    <div class="card p-5">\r\n'
    '      <div class="flex items-center justify-between mb-4">\r\n'
    '        <div class="section-title">Stellen nach Teilplan &amp; Besoldungsgruppe</div>\r\n'
    '        <span class="note">Jahr: <span id="sp-tp-detail-yr"></span></span>\r\n'
    '      </div>\r\n'
    '      <div id="sp-tp-detail-body"></div>\r\n'
    '    </div>\r\n'
)

# ── JS: renderSpTpDetail + _spTpToggle + Monkey-Patch renderPersonal ──────────
# WICHTIG: keine Unicode-Zeichen in JS-Strings (nur ASCII + HTML-Entities)
_js_lines = [
    "// ── Stellenplan TP-Detail-Accordion ────────────────────────────────",
    "(function() {",
    "  function renderSpTpDetail(sp, yr) {",
    '    var container = document.getElementById("sp-tp-detail-body");',
    "    if (!container || !sp) return;",
    '    var yrEl = document.getElementById("sp-tp-detail-yr");',
    '    if (yrEl) yrEl.textContent = yr + " Plan";',
    "    var detail = sp.nach_tp_detail || {};",
    "    var tps = Object.keys(detail).sort();",
    '    if (!tps.length) { container.innerHTML = \'<p class="note">Keine Daten</p>\'; return; }',
    '    var html = "";',
    "    tps.forEach(function(tp) {",
    "      var d = detail[tp];",
    "      var beamteTotal = d.beamte.reduce(function(s, x) { return s + x.planstellen; }, 0);",
    "      var tarifTotal  = d.tarif.reduce( function(s, x) { return s + x.planstellen; }, 0);",
    "      var gesamt = beamteTotal + tarifTotal;",
    '      var domId  = "sp-tp-det-" + tp;',
    # Accordion header – nutzt data-sptp statt inline onclick-Argument
    '      html += \'<div class="border border-slate-700 rounded-lg mb-2 overflow-hidden">\';',
    '      html += \'<button class="w-full flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3 text-left\';',
    '      html += \' hover:bg-slate-700/40 transition-colors"\';',
    '      html += \' data-sptp="\' + domId + \'"\';',
    '      html += \' onclick="_spTpToggle(this)">\';',
    '      html += \'<span class="text-slate-400 text-xs font-mono">TP\' + tp + \'</span>\';',
    '      html += \'<span class="text-slate-100 font-medium flex-1 text-sm">\' + d.name + \'</span>\';',
    "      if (beamteTotal > 0) {",
    '        html += \'<span class="text-xs bg-violet-900/40 text-violet-300 px-2 py-0.5 rounded">\';',
    '        html += "Beamte: " + fmt(beamteTotal, 3) + "</span>";',
    "      }",
    '      html += \'<span class="text-xs bg-emerald-900/40 text-emerald-300 px-2 py-0.5 rounded">\';',
    '      html += "Tarif: " + fmt(tarifTotal, 3) + "</span>";',
    '      html += \'<span class="text-xs text-slate-400">Ges.: \' + fmt(gesamt, 3) + \'</span>\';',
    '      html += \'<span class="text-slate-500 text-xs ml-1">&#9660;</span>\';',
    "      html += '</button>';",
    # Accordion body
    '      html += \'<div id="\' + domId + \'" class="hidden px-4 pb-4 pt-2">\';',
    '      html += \'<div class="grid grid-cols-1 md:grid-cols-2 gap-4">\';',
    # Beamtenstellen-Tabelle
    "      if (beamteTotal > 0) {",
    '        html += \'<div>\';',
    '        html += \'<div class="text-xs font-semibold text-violet-300 mb-2">Beamtenstellen</div>\';',
    '        html += \'<table class="w-full text-xs border-collapse">\';',
    '        html += \'<thead><tr class="text-slate-400 border-b border-slate-700">\';',
    '        html += \'<th class="text-left pb-1.5 font-normal">Besoldungsgruppe</th>\';',
    '        html += \'<th class="text-right pb-1.5 font-normal">Stellen</th></tr></thead><tbody>\';',
    "        d.beamte.forEach(function(b) {",
    '          html += \'<tr class="border-b border-slate-800/40">\';',
    '          html += \'<td class="py-1 text-slate-300">\' + b.kuerzel + \'</td>\';',
    '          html += \'<td class="py-1 text-right text-violet-200">\' + fmt(b.planstellen, 3) + \'</td></tr>\';',
    "        });",
    '        html += \'<tr class="border-t border-slate-600 font-semibold">\';',
    '        html += \'<td class="pt-1.5 text-violet-300">Summe</td>\';',
    '        html += \'<td class="pt-1.5 text-right text-violet-300">\' + fmt(beamteTotal, 3) + \'</td></tr>\';',
    "        html += '</tbody></table></div>';",
    "      }",
    # Tarifbeschäftigte-Tabelle (ä = &#228;)
    '      html += \'<div>\';',
    '      html += \'<div class="text-xs font-semibold text-emerald-300 mb-2">Tarifbesch&#228;ftigte</div>\';',
    '      html += \'<table class="w-full text-xs border-collapse">\';',
    '      html += \'<thead><tr class="text-slate-400 border-b border-slate-700">\';',
    '      html += \'<th class="text-left pb-1.5 font-normal">Entgeltgruppe</th>\';',
    '      html += \'<th class="text-right pb-1.5 font-normal">Stellen</th></tr></thead><tbody>\';',
    "      d.tarif.forEach(function(t) {",
    '        html += \'<tr class="border-b border-slate-800/40">\';',
    '        html += \'<td class="py-1 text-slate-300">\' + t.kuerzel + \'</td>\';',
    '        html += \'<td class="py-1 text-right text-emerald-200">\' + fmt(t.planstellen, 3) + \'</td></tr>\';',
    "      });",
    '      html += \'<tr class="border-t border-slate-600 font-semibold">\';',
    '      html += \'<td class="pt-1.5 text-emerald-300">Summe</td>\';',
    '      html += \'<td class="pt-1.5 text-right text-emerald-300">\' + fmt(tarifTotal, 3) + \'</td></tr>\';',
    "      html += '</tbody></table></div>';",
    "      html += '</div></div></div>';",
    "    });",
    "    container.innerHTML = html;",
    "  }",
    "",
    "  // Toggle-Helper: liest data-sptp statt Argument (kein Quoting-Problem)",
    "  window._spTpToggle = function(btn) {",
    '    var id = btn.getAttribute("data-sptp");',
    '    if (id) document.getElementById(id).classList.toggle("hidden");',
    "  };",
    "",
    "  // Monkey-Patch renderPersonal",
    "  var _origRP = renderPersonal;",
    "  renderPersonal = function() {",
    "    _origRP();",
    "    var SP = DATA && DATA.personal && DATA.personal.stellenplan;",
    "    if (!SP) return;",
    "    var yr = String(activeJahr);",
    '    var sp = SP.by_year[yr + "_PLAN_ANSATZ"] || SP.by_year["2025_PLAN_ANSATZ"];',
    "    renderSpTpDetail(sp, yr);",
    "  };",
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

    # ── 1. HTML vor dem schliessenden </div> von pers-stellenplan ─────────────
    pers_sp_start = content.find('id="pers-stellenplan"')
    hsk_tab_start = content.find('id="tab-hsk"')
    if pers_sp_start == -1 or hsk_tab_start == -1:
        print("[ERROR] Anker nicht gefunden.")
        return

    search_area = content[pers_sp_start:hsk_tab_start]
    # Letztes \r\n\r\n  </div> = schliessendes </div> von pers-stellenplan
    close_rel = search_area.rfind("\r\n\r\n  </div>")
    if close_rel == -1:
        print("[ERROR] Schliessende pers-stellenplan-div nicht gefunden.")
        return

    insert_at = pers_sp_start + close_rel + 4  # nach \r\n\r\n, vor "  </div>"
    content = content[:insert_at] + NEW_HTML + content[insert_at:]

    # ── 2. JS vor renderSankey() einfuegen ────────────────────────────────────
    js_anchor = "function renderSankey()"
    idx_js = content.find(js_anchor)
    if idx_js == -1:
        print("[ERROR] JS-Anker (renderSankey) nicht gefunden.")
        return
    content = content[:idx_js] + NEW_JS + content[idx_js:]

    # ── 3. Backtick-Paritaet pruefen ─────────────────────────────────────────
    bc = content.count("\x60")
    if bc % 2 != 0:
        print(f"[WARN] Ungerade Backtick-Anzahl: {bc}")
    else:
        print(f"[OK] Backticks: {bc} (gerade)")

    with open(HTML_PATH, "wb") as f:
        f.write(content.encode("utf-8"))
    print("[OK] patch_sp_tp_detail.py angewendet.")


if __name__ == "__main__":
    patch()
