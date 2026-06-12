#!/usr/bin/env python3
"""
patch_fix_hsk_tab_visibility.py
Behebt Bug: initHsk() entfernte faelschlicherweise 'hidden' von tab-hsk,
sodass der HSK-Tab dauerhaft im Ueberblick sichtbar war.
Fix: hidden nur hinzufuegen wenn keine Daten vorhanden, niemals entfernen.
"""

HTML_PATH = "index.html"
MARKER = "if (!DATA.hsk) el.classList.add"

OLD_LINE = 'el.classList.toggle("hidden", !DATA.hsk);'
NEW_LINE = 'if (!DATA.hsk) el.classList.add("hidden");  // nur verstecken wenn keine Daten'


def patch():
    with open(HTML_PATH, "rb") as f:
        content = f.read().decode("utf-8")

    if MARKER in content:
        print("[SKIP] Patch already applied.")
        return

    if OLD_LINE not in content:
        print("[ERROR] Ziel-Zeile nicht gefunden.")
        return

    content = content.replace(OLD_LINE, NEW_LINE)

    bc = content.count("\x60")
    if bc % 2 != 0:
        print(f"[WARN] Ungerade Backtick-Anzahl: {bc}")
    else:
        print(f"[OK] Backticks: {bc} (gerade)")

    with open(HTML_PATH, "wb") as f:
        f.write(content.encode("utf-8"))
    print("[OK] patch_fix_hsk_tab_visibility.py angewendet.")


if __name__ == "__main__":
    patch()
