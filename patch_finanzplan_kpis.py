#!/usr/bin/env python3
"""
patch_finanzplan_kpis.py
Fuegt Finanzplan-KPI-Chips (Einzahlungen, Auszahlungen, Finanzierungssaldo)
unterhalb der bestehenden Ergebnisplan-KPIs im Ueberblick-Tab hinzu.
"""

HTML_PATH = "index.html"
MARKER = 'id="kpi-einzahlungen"'

NEW_HTML = (
    '\r\n'
    '<div class="mb-8">\r\n'
    '  <div class="text-sm font-medium text-slate-400 mb-2">Finanzplan (Zahlungsrechnung &ndash; KK6/KK7)</div>\r\n'
    '  <div class="grid grid-cols-3 gap-4" id="kpi-finanzplan-row">\r\n'
    '    <div class="card p-4">\r\n'
    '      <div class="kpi-label">Einzahlungen</div>\r\n'
    '      <div class="kpi-value text-emerald-400" id="kpi-einzahlungen">&ndash;</div>\r\n'
    '      <div class="note mt-1" id="kpi-einzahlungen-note">Finanzplan</div>\r\n'
    '    </div>\r\n'
    '    <div class="card p-4">\r\n'
    '      <div class="kpi-label">Auszahlungen</div>\r\n'
    '      <div class="kpi-value text-rose-400" id="kpi-auszahlungen">&ndash;</div>\r\n'
    '      <div class="note mt-1" id="kpi-auszahlungen-note">Finanzplan</div>\r\n'
    '    </div>\r\n'
    '    <div class="card p-4">\r\n'
    '      <div class="kpi-label">Finanzierungssaldo</div>\r\n'
    '      <div class="kpi-value text-amber-400" id="kpi-finanzsaldo">&ndash;</div>\r\n'
    '      <div class="note mt-1">Einzahlungen &ndash; Auszahlungen</div>\r\n'
    '    </div>\r\n'
    '  </div>\r\n'
    '</div>\r\n'
)

# JS Monkey-Patch fuer renderKPI
# Unicode-Escapes statt direkter Zeichen in JS-Strings (Constraint: kein Unicode in JS)
NEW_JS = (
    '(function() {\r\n'
    '  const _origKPI = renderKPI;\r\n'
    '  renderKPI = function() {\r\n'
    '    _origKPI();\r\n'
    '    const m = getYD().meta;\r\n'
    '    const einz  = m.einzahlungen_soll  !== undefined ? m.einzahlungen_soll  : (m.einzahlungen_etl  || 0);\r\n'
    '    const ausz  = m.auszahlungen_soll  !== undefined ? m.auszahlungen_soll  : (m.auszahlungen_etl  || 0);\r\n'
    '    const saldo = m.finanzergebnis_soll !== undefined ? m.finanzergebnis_soll : (einz - ausz);\r\n'
    '    const hasGT = m.einzahlungen_soll !== undefined;\r\n'
    '    const note  = hasGT ? ("Haushaltssatzung " + activeJahr) : "ETL-Sch\\u00e4tzwert";\r\n'
    '    document.getElementById("kpi-einzahlungen").textContent = fmtMio(einz);\r\n'
    '    document.getElementById("kpi-auszahlungen").textContent = fmtMio(ausz);\r\n'
    '    document.getElementById("kpi-einzahlungen-note").textContent = note;\r\n'
    '    document.getElementById("kpi-auszahlungen-note").textContent = note;\r\n'
    '    const elS = document.getElementById("kpi-finanzsaldo");\r\n'
    '    elS.textContent = fmtMio(saldo);\r\n'
    '    elS.className = "kpi-value " + (saldo < 0 ? "text-rose-400" : "text-emerald-400");\r\n'
    '  };\r\n'
    '})();\r\n'
    '\r\n'
)


def patch():
    with open(HTML_PATH, "rb") as f:
        content = f.read().decode("utf-8")

    if MARKER in content:
        print("[SKIP] Patch already applied.")
        return

    # ── 1. HTML-Block nach kpi-cards, vor tabbar einfuegen ────────────────
    html_anchor = '<div class="tabbar" id="tabbar">'
    idx_html = content.find(html_anchor)
    if idx_html == -1:
        print("[ERROR] HTML-Anker (tabbar) nicht gefunden.")
        return
    content = content[:idx_html] + NEW_HTML + content[idx_html:]

    # ── 2. JS-Block vor renderSankey einfuegen ────────────────────────────
    js_anchor = "function renderSankey()"
    idx_js = content.find(js_anchor)
    if idx_js == -1:
        print("[ERROR] JS-Anker (renderSankey) nicht gefunden.")
        return
    content = content[:idx_js] + NEW_JS + content[idx_js:]

    # ── 3. Backtick-Paritaet pruefen ─────────────────────────────────────
    bc = content.count("\x60")
    if bc % 2 != 0:
        print(f"[WARN] Ungerade Backtick-Anzahl: {bc}")
    else:
        print(f"[OK] Backticks: {bc} (gerade)")

    with open(HTML_PATH, "wb") as f:
        f.write(content.encode("utf-8"))
    print("[OK] patch_finanzplan_kpis.py angewendet.")


if __name__ == "__main__":
    patch()
