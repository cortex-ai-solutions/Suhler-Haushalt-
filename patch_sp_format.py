"""
Patch: Plotly-Hovertemplates in Stellenplan-Charts auf deutsches
Zahlenformat umstellen (customdata mit fmt()-Vorformatierung).
"""

path = "index.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

CRLF = "\r\n"


def apply(c, old, new, label):
    if old not in c:
        raise ValueError(f"NICHT GEFUNDEN: {label!r}")
    print(f"  [OK] {label}")
    return c.replace(old, new, 1)


# ── 1: Besoldungsgruppen-Chart: customdata + deutsches Hovertemplate ───────
OLD_SP_BAR = (
    "  Plotly.newPlot(\"chart-sp-gruppen\", [{" + CRLF +
    "    type: \"bar\", orientation: \"h\"," + CRLF +
    "    x: allKeys.map(k => ng[k].planstellen)," + CRLF +
    "    y: allKeys," + CRLF +
    "    marker: { color: beamteColors }," + CRLF +
    "    hovertemplate: \"<b>%{y}</b>: %{x:.3f} Stellen<extra></extra>\"," + CRLF +
    "  }],"
)
NEW_SP_BAR = (
    "  Plotly.newPlot(\"chart-sp-gruppen\", [{" + CRLF +
    "    type: \"bar\", orientation: \"h\"," + CRLF +
    "    x: allKeys.map(k => ng[k].planstellen)," + CRLF +
    "    y: allKeys," + CRLF +
    "    customdata: allKeys.map(k => fmt(ng[k].planstellen, 3))," + CRLF +
    "    marker: { color: beamteColors }," + CRLF +
    "    hovertemplate: \"<b>%{y}</b>: %{customdata} Stellen<extra></extra>\"," + CRLF +
    "  }],"
)
content = apply(content, OLD_SP_BAR, NEW_SP_BAR, "chart-sp-gruppen customdata")


# ── 2: TP-Vergleich-Chart: customdata für 2024-Trace ──────────────────────
OLD_2024 = (
    "    hovertemplate:\"<b>%{x}</b> 2024: %{y:.3f} Stellen<extra></extra>\","
)
NEW_2024 = (
    "    customdata: tpNrs.map(tp => fmt((sp24.nach_tp[tp] || {}).gesamt || 0, 3))," + CRLF +
    "    hovertemplate:\"<b>%{x}</b> 2024: %{customdata} Stellen<extra></extra>\","
)
content = apply(content, OLD_2024, NEW_2024, "chart-sp-tp 2024 customdata")


# ── 3: TP-Vergleich-Chart: customdata für 2025-Trace ──────────────────────
OLD_2025 = (
    "    hovertemplate:\"<b>%{x}</b> 2025: %{y:.3f} Stellen<extra></extra>\","
)
NEW_2025 = (
    "    customdata: tpNrs.map(tp => fmt((sp25.nach_tp[tp] || {}).gesamt || 0, 3))," + CRLF +
    "    hovertemplate:\"<b>%{x}</b> 2025: %{customdata} Stellen<extra></extra>\","
)
content = apply(content, OLD_2025, NEW_2025, "chart-sp-tp 2025 customdata")


with open(path, "wb") as f:
    f.write(content.encode("utf-8"))

print(f"\nFertig! {path}")
