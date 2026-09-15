"""
patch_2026_rollout.py
HH-Plan 2026 wird neues "aktuelles" Jahr im Dashboard (Root-Meta, Simulator-Basis,
Personal-Trend, Details-Drilldown). 2023-2025 bleiben als Vergleichsjahre erhalten
(Jahresvergleich-Tab liest DATA.by_year dynamisch, keine Aenderung noetig).

NICHT angefasst (bewusst, separate Datenquellen ohne 2026-Daten):
  - Stellenplan (SP.by_year "2025_PLAN_ANSATZ"-Fallbacks) - stellenplan-Tabelle
    hat noch keine 2026-Zeilen (eigene Pipeline, nicht Teil dieses Rollouts)
  - HSK-Jahresarrays (2013-2025) - hsk_jahreswerte/hsk_abgleich VIEW gehen nur bis 2025
  - Beteiligungen-Jahresarray (2021-2024) - Beteiligungsbericht ist eigener Jahreszyklus
  - Bilanz-Jahre (2020/2021) - eigener Jahresabschluss-Zyklus
"""

INDEX = "index.html"


def run():
    content = open(INDEX, "rb").read()
    assert content.count(b"\r\n") > 1000, "CRLF erwartet"
    bt_before = content.count(b"\x60")

    # ── 1. Titel (<title> + <h1>, 2 Vorkommen) ──────────────────────────────
    OLD = b"Haushaltsplan Stadt Suhl 2025"
    NEW = b"Haushaltsplan Stadt Suhl 2026"
    assert content.count(OLD) == 2, f"Titel: erwartet 2 Vorkommen, gefunden {content.count(OLD)}"
    content = content.replace(OLD, NEW)
    print("1. Titel (<title> + <h1>) -> 2026")

    # ── 2. KPI-Note Platzhalter (kosmetisch, wird von renderKPI() ueberschrieben) ─
    OLD = b'id="kpi-ertraege-note">Haushaltssatzung 2025</div>'
    NEW = b'id="kpi-ertraege-note">Haushaltssatzung 2026</div>'
    assert content.count(OLD) == 1
    content = content.replace(OLD, NEW, 1)
    print("2. KPI-Note Platzhalter -> 2026")

    # ── 3. Jahres-Toggle: 2026-Button hinzufuegen, 2025 wird inaktiv ────────
    OLD = (
        b'    <button onclick="switchYear(2025)" data-jahr="2025"\r\n'
        b'      class="year-pill text-sm px-4 py-1.5 rounded-full border-blue-400 text-slate-100 bg-blue-950 transition-colors">\r\n'
        b'      2025\r\n'
        b'    </button>\r\n'
        b'  </div>'
    )
    NEW = (
        b'    <button onclick="switchYear(2025)" data-jahr="2025"\r\n'
        b'      class="year-pill text-sm px-4 py-1.5 rounded-full border border-slate-600 text-slate-400 hover:border-blue-400 hover:text-slate-200 transition-colors">\r\n'
        b'      2025\r\n'
        b'    </button>\r\n'
        b'    <button onclick="switchYear(2026)" data-jahr="2026"\r\n'
        b'      class="year-pill text-sm px-4 py-1.5 rounded-full border-blue-400 text-slate-100 bg-blue-950 transition-colors">\r\n'
        b'      2026\r\n'
        b'    </button>\r\n'
        b'  </div>'
    )
    assert content.count(OLD) == 1, "Jahres-Toggle-Block nicht eindeutig gefunden"
    content = content.replace(OLD, NEW, 1)
    print("3. Jahres-Toggle: 2026-Button ergaenzt (aktiv), 2025 -> inaktiv-Stil")

    # ── 4. activeJahr Default ───────────────────────────────────────────────
    OLD = b"let activeJahr = 2025;"
    NEW = b"let activeJahr = 2026;"
    assert content.count(OLD) == 1
    content = content.replace(OLD, NEW, 1)
    print("4. activeJahr Default -> 2026")

    # ── 5. Personal-Tab Fallback-Jahr ───────────────────────────────────────
    OLD = b'const y = P.by_year[yr] || P.by_year["2025"];'
    NEW = b'const y = P.by_year[yr] || P.by_year["2026"];'
    assert content.count(OLD) == 1
    content = content.replace(OLD, NEW, 1)
    print("5. Personal-Tab Fallback -> P.by_year['2026']")

    # ── 6. Personal Trend-Chart Jahre ───────────────────────────────────────
    OLD = (
        b'  // Trend-Chart (immer 2023\xe2\x80\x932025)\r\n'
        b'  const tYears = ["2023", "2024", "2025"];'
    )
    NEW = (
        b'  // Trend-Chart (immer 2024\xe2\x80\x932026)\r\n'
        b'  const tYears = ["2024", "2025", "2026"];'
    )
    assert content.count(OLD) == 1
    content = content.replace(OLD, NEW, 1)
    print("6. Personal Trend-Chart tYears -> [2024,2025,2026]")

    # ── 7. getKK5(): Jahres-Vergleiche + Feldnamen verschieben ──────────────
    OLD = (
        b"function getKK5(p, jahr) {\r\n"
        b"  if (jahr === 2025) return p.kk5_2025 || 0;\r\n"
        b"  if (jahr === 2024) return p.kk5_2024 || 0;\r\n"
        b"  return p.kk5_2023 || 0;\r\n"
        b"}"
    )
    NEW = (
        b"function getKK5(p, jahr) {\r\n"
        b"  if (jahr === 2026) return p.kk5_2026 || 0;\r\n"
        b"  if (jahr === 2025) return p.kk5_2025 || 0;\r\n"
        b"  return p.kk5_2024 || 0;\r\n"
        b"}"
    )
    assert content.count(OLD) == 1
    content = content.replace(OLD, NEW, 1)
    print("7. getKK5(): 2025/2024/2023 -> 2026/2025/2024")

    # ── 8. Details-Drilldown Jahres-Keys (b23/b24/b25 -> b24/b25/b26) ───────
    OLD = b'["b23","b24","b25"]'
    NEW = b'["b24","b25","b26"]'
    assert content.count(OLD) == 1
    content = content.replace(OLD, NEW, 1)
    print("8. Details-Drilldown Keys -> [b24,b25,b26]")

    # ── 9. Alle uebrigen kk5_2025 -> kk5_2026 (Simulator/Treemap etc.) ──────
    remaining = content.count(b"kk5_2025")
    content = content.replace(b"kk5_2025", b"kk5_2026")
    print(f"9. {remaining} weitere kk5_2025 -> kk5_2026 (Simulator, Treemap, Sortierung)")

    # ── 10. Cache-Buster fuer budget_data.json hochzaehlen ──────────────────
    OLD = b'fetch("budget_data.json?v=20260615c")'
    NEW = b'fetch("budget_data.json?v=20260915a")'
    assert content.count(OLD) == 1
    content = content.replace(OLD, NEW, 1)
    print("10. Cache-Buster budget_data.json -> v=20260915a")

    # ── Validierung ──────────────────────────────────────────────────────────
    bt_after = content.count(b"\x60")
    assert bt_after == bt_before, f"Backtick-Paritaet verletzt: vorher={bt_before} nachher={bt_after}"
    assert content.count(b"kk5_2025") == 0, "Es sollten keine kk5_2025 mehr uebrig sein"
    assert content.count(b"kk5_2024") == 1, "Genau 1 kk5_2024 erwartet (aus getKK5, war vorher kk5_2023)"
    assert content.count(b"kk5_2023") == 0, "Es sollte kein kk5_2023 mehr geben"
    print(f"OK: Backticks unveraendert ({bt_after})")

    open(INDEX, "wb").write(content)
    size_kb = len(content) // 1024
    print(f"[OK] index.html ({size_kb} KB)")


if __name__ == "__main__":
    run()
