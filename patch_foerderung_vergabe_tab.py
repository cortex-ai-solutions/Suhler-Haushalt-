# -*- coding: utf-8 -*-
"""
patch_foerderung_vergabe_tab.py - 10. Tab "Förderung & Vergabe" (09.11.2026)

Übernimmt die Sicht "Stadt als Bauherr" aus dem Schwesterprojekt Förder- & Vorschriften-Lotse Suhl
(foerderprogramme-suhl). Entscheidung Tobias 09.11.2026: Das ist Verwaltungs-/Stadtratssicht und gehört
zum Nachschlagen ins Haushalts-Dashboard, auch wenn es sich mit "Investitionen" überschneidet.

Inhalt: Förderstand je Investitionsnummer mit wörtlichem Beleg aus der Erläuterung, Förder-Konfliktbericht
B1-B8, Vergabe-Lotse (Wertgrenzen EU/ThürVVöA), EU-Ausschreibungen des Stadtkonzerns (TED).

ALLES IST ALS ENTWURF GEKENNZEICHNET (Entscheidung Tobias 09.11.2026): maschinell abgeleitet, nicht fachlich
geprüft, dieses Dashboard ist öffentlich.

Daten: foerder_vergabe.json (erzeugt von ../Förderprogramme Suhl/export_haushalt.py, Wochenlauf dort),
wird erst beim Öffnen des Tabs geladen. Keine Änderung an budget_data.json / generate_json.py.
Bewusst KEINE automatische Bewertung/Priorisierung (vgl. feedback_no_auto_optimizer): Befunde mit Beleg,
die Bewertung bleibt bei Verwaltung und Stadtrat.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "index.html")
JS_PATH = os.path.join(BASE_DIR, "patch_foerderung_vergabe_tab.js")

with open(HTML_PATH, "rb") as f:
    content = f.read().decode("utf-8")

if 'data-tab="foerderung"' in content:
    raise SystemExit("[INFO] Tab 'foerderung' ist schon eingebaut - nichts zu tun.")


def nl(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\n", "\r\n")


def must_replace(old, new, label):
    global content
    old, new = nl(old), nl(new)
    n = content.count(old)
    if n != 1:
        raise SystemExit(f"[FEHLER] Anker '{label}' kommt {n}x vor (erwartet 1x). Abbruch ohne Aenderung.")
    content = content.replace(old, new, 1)


# 1) Reiter (mobil + Desktop)
must_replace('  <div class="mobile-tab-item" data-tab="investitionen">Investitionen</div>\n',
             '  <div class="mobile-tab-item" data-tab="investitionen">Investitionen</div>\n'
             '  <div class="mobile-tab-item" data-tab="foerderung">F&ouml;rderung &amp; Vergabe <span class="text-amber-400 text-[10px]">Entwurf</span></div>\n',
             "mobile tab")
must_replace('  <div class="tab" data-tab="investitionen">Investitionen</div>\n',
             '  <div class="tab" data-tab="investitionen">Investitionen</div>\n'
             '  <div class="tab" data-tab="foerderung">F&ouml;rderung &amp; Vergabe <span class="text-amber-400 text-[10px] align-top">Entwurf</span></div>\n',
             "desktop tab")

# 2) Container
must_replace('<div id="tab-investitionen" class="hidden">\n',
             '<div id="tab-foerderung" class="hidden"></div>\n\n<div id="tab-investitionen" class="hidden">\n',
             "tab container")

# 3) Umschalten
must_replace('  const TABS = ["overview", "details", "personal", "jahresvergleich", "zeitreihe", "hsk", "simulator", "vermoegen", "investitionen"];',
             '  const TABS = ["overview", "details", "personal", "jahresvergleich", "zeitreihe", "hsk", "simulator", "vermoegen", "investitionen", "foerderung"];',
             "TABS")
must_replace('      if (name === "investitionen") renderInvestitionen();\n',
             '      if (name === "investitionen") renderInvestitionen();\n'
             '      if (name === "foerderung") renderFoerderung();\n',
             "render switch")

# 4) Programmcode vor das letzte </script>
with open(JS_PATH, encoding="utf-8") as f:
    js = f.read()
i = content.rindex("</script>")
content = content[:i] + nl(js) + content[i:]

with open(HTML_PATH, "wb") as f:
    f.write(content.encode("utf-8"))
print("[OK] Tab 'Förderung & Vergabe' eingebaut.")
