
// ── Förderung & Vergabe (aus dem Förder- & Vorschriften-Lotsen, ENTWURF) ─────────────
// Eingebaut von patch_foerderung_vergabe_tab.py. Daten: foerder_vergabe.json (export_haushalt.py im Förderlotsen).
var FV = null, _fvRendered = false;
var FV_GRAU = "bg-slate-800 text-slate-300 border-slate-600";
var FV_STATUS = {
  antrag_offen: ["bg-rose-950/60 text-rose-300 border-rose-700", "Antrag offen"],
  beantragt:    ["bg-amber-950/50 text-amber-300 border-amber-700", "beantragt"],
  bewilligt:    ["bg-emerald-950/50 text-emerald-300 border-emerald-700", "bewilligt"],
  mittelabruf:  ["bg-sky-950/50 text-sky-300 border-sky-700", "Mittelabruf offen"],
  abgelehnt:    ["bg-rose-950/60 text-rose-300 border-rose-700", "abgelehnt"],
  pauschale:    [FV_GRAU, "Pauschale"], erstattung: [FV_GRAU, "keine Förderung"], unklar: [FV_GRAU, "Stand unklar"]
};
var FV_EINSTUFUNG = {belegt: ["bg-rose-950/60 text-rose-300 border-rose-700", "steht so im Haushalt"],
  "Prüfhinweis": ["bg-amber-950/50 text-amber-300 border-amber-700", "Prüfhinweis"], Transparenz: [FV_GRAU, "Transparenz"]};
var FV_NOTICE = {"cn-standard": "Ausschreibung", "can-standard": "Zuschlag", "corr": "Berichtigung", "veat": "Direktvergabe (Ex-ante)",
  "pin-only": "Vorinformation", "pin-tran": "Vorinformation", "pin-rtl": "Vorinformation", "cn-desg": "Wettbewerb", "can-desg": "Wettbewerbsergebnis"};
var FV_VERFAHREN = {open: "offenes Verfahren", restricted: "nicht offenes Verfahren", "neg-w-call": "Verhandlungsverf. mit Teilnahmewettbewerb",
  "neg-wo-call": "Verhandlungsverf. ohne Teilnahmewettbewerb", "comp-tend": "wettbewerbliches Verfahren"};
function fvEsc(s) { return s == null ? "" : String(s).replace(/[&<>"']/g, function(c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]; }); }
function fvEuro(v) { return v == null ? "–" : Number(v).toLocaleString("de-DE", {maximumFractionDigits: 0}) + " €"; }
function fvMio(v) { return v == null ? "–" : Math.abs(v) >= 1e6 ? (v / 1e6).toLocaleString("de-DE", {maximumFractionDigits: 2}) + " Mio. €" : fvEuro(v); }
function fvDatum(s) { return s ? String(s).slice(0, 10).split("-").reverse().join(".") : ""; }
function fvPill(cls, text) { return '<span class="inline-block whitespace-nowrap text-[11px] font-semibold px-2 py-0.5 rounded-full border ' + cls + '">' + fvEsc(text) + "</span>"; }
function fvEntwurf() { return fvPill("bg-amber-500/15 text-amber-300 border-amber-500/60", "ENTWURF"); }
function fvQuote(q) { return q == null ? "" : Math.abs(q - 2 / 3) < 0.001 ? "2/3" : Math.round(q * 100) + " %"; }
function fvName(nr) {
  var IP = (DATA && DATA.investitionsprojekte) || {massnahmen: []};
  var m = (IP.massnahmen || []).find(function(x) { return x.investitionsnummer === nr; });
  return m ? m.bezeichnung : "";
}
function fvTitel(text) { return '<h3 class="text-sm font-semibold text-slate-200 uppercase tracking-wide mt-8 mb-3 flex flex-wrap items-center gap-2">' + text + " " + fvEntwurf() + "</h3>"; }

function renderFoerderung() {
  var el = document.getElementById("tab-foerderung");
  if (!el || _fvRendered) return;
  if (!FV) {
    el.innerHTML = '<div class="card p-6 text-slate-400 text-sm">Lade Förder- und Vergabedaten …</div>';
    fetch("foerder_vergabe.json?v=" + new Date().toISOString().slice(0, 10))
      .then(function(r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function(d) { FV = d; renderFoerderung(); })
      .catch(function(e) { el.innerHTML = '<div class="card p-6 text-rose-300 text-sm">foerder_vergabe.json konnte nicht geladen werden (' + fvEsc(e.message) + ").</div>"; });
    return;
  }
  _fvRendered = true;
  var B = FV.befunde || [];
  var bef = function(code) { return B.find(function(b) { return b.code === code; }) || {faelle: [], summe: null}; };
  var ohneAngebot = (FV.vergaben || []).filter(function(v) { return v.anzahl_angebote === 0; });
  var ausschreibungen = (FV.ted || []).filter(function(t) { return t.notice_type === "cn-standard"; });
  var kpi = function(wert, label, note, farbe) {
    return '<div class="card p-4"><div class="kpi-label">' + label + '</div><div class="kpi-value ' + farbe + '">' + wert + '</div><div class="note mt-1">' + note + "</div></div>";
  };
  var stati = Object.keys(FV_STATUS).filter(function(s) { return (FV.foerderung || []).some(function(f) { return f.status === s; }); });
  var typen = Array.from(new Set((FV.ted || []).map(function(t) { return t.notice_type; })));

  el.innerHTML =
    '<div class="rounded-xl border-2 border-amber-500/60 bg-amber-500/10 p-4 mb-6 flex gap-4 items-start">' +
      '<div class="text-amber-300 font-bold text-lg tracking-widest">ENTWURF</div>' +
      '<div class="text-sm text-amber-100/90">' + fvEsc(FV.hinweis) +
        '<div class="note mt-2 text-amber-200/70">Herkunft: ' + fvEsc(FV.herkunft) + ". „Steht so im Haushalt“ heißt: Der Satz steht wörtlich in der Erläuterung des Investitionsplans. " +
        "„Prüfhinweis“ heißt: Widerspruch zu anderen Daten, Ursache offen. Keine automatische Bewertung – die Einordnung bleibt bei Verwaltung und Stadtrat.</div></div></div>" +

    '<div class="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-2">' +
      kpi(fvMio(bef("B1").summe), "Förderung eingeplant, Antrag noch nicht gestellt", bef("B1").faelle.length + " Maßnahmen · Entwurf", "text-rose-300") +
      kpi(fvMio(bef("B6").summe), "Förderung beantragt, Bescheid steht aus", bef("B6").faelle.length + " Maßnahmen · Entwurf", "text-amber-300") +
      kpi(fvMio(bef("B4").summe), "Bewilligt, Eigenanteil steigt trotzdem", bef("B4").faelle.length + " Maßnahmen · Entwurf", "text-amber-300") +
      kpi(String(ausschreibungen.length), "EU-Ausschreibungen Stadtkonzern", (FV.ted || []).length + " EU-Bekanntmachungen insgesamt (TED)", "text-sky-300") +
      kpi(String(ohneAngebot.length), "Lose ohne Angebot (belegt)", ohneAngebot.map(function(v) { return fvEsc(v.los + " " + (v.massnahme_titel || "")); }).join(", ") || "–", "text-rose-300") +
    "</div>" +

    fvTitel("Förder-Konflikte im Investitionsplan " + fvEsc(FV.aktuelles_jahr)) +
    '<div class="space-y-2">' + B.map(function(b) {
      var e = FV_EINSTUFUNG[b.einstufung] || [FV_GRAU, b.einstufung];
      return '<details class="card p-4"><summary class="cursor-pointer flex flex-wrap items-center gap-2 text-sm">' +
        '<b class="text-slate-100">' + fvEsc(b.code) + "</b><span class=\"text-slate-200\">" + fvEsc(b.titel) + "</span>" + fvPill(e[0], e[1]) +
        '<span class="note">' + b.faelle.length + (b.faelle.length === 1 ? " Fall" : " Fälle") + (b.summe ? " · " + fvMio(b.summe) : "") + "</span></summary>" +
        '<p class="text-xs text-slate-400 mt-3 mb-3">' + fvEsc(b.text) + "</p>" +
        (b.faelle.length ? '<div class="overflow-x-auto"><table class="w-full text-xs"><thead><tr class="text-slate-500 text-left border-b border-slate-700">' +
          '<th class="py-1 pr-3">Nr.</th><th class="py-1 pr-3">Maßnahme</th><th class="py-1 pr-3">Programm</th><th class="py-1 pr-3 text-right">Betrag</th><th class="py-1">Beleg (Erläuterung)</th></tr></thead><tbody>' +
          b.faelle.map(function(f) {
            return '<tr class="border-b border-slate-800 align-top"><td class="py-1.5 pr-3 text-slate-500 whitespace-nowrap">' + fvEsc(f.nr) + '</td><td class="py-1.5 pr-3 text-slate-200">' + fvEsc(f.massnahme) +
              (f.zusatz ? '<div class="note">' + fvEsc(f.zusatz) + "</div>" : "") + '</td><td class="py-1.5 pr-3 text-slate-400">' + fvEsc(f.programm) +
              '</td><td class="py-1.5 pr-3 text-right whitespace-nowrap text-slate-200">' + (f.betrag == null ? "–" : fvMio(f.betrag)) +
              '</td><td class="py-1.5 text-slate-400 italic">„' + fvEsc(f.beleg) + "“</td></tr>";
          }).join("") + "</tbody></table></div>" : '<p class="note">Keine Fälle.</p>') + "</details>";
    }).join("") + "</div>" +

    fvTitel("Förderstand je Maßnahme (laut Erläuterung)") +
    '<div class="flex flex-wrap gap-3 items-center mb-3">' +
      '<input id="fv-suche" type="text" placeholder="Maßnahme oder Programm suchen …" class="bg-slate-800 border border-slate-600 rounded px-3 py-1 text-xs text-slate-300 placeholder:text-slate-500 focus:outline-none focus:border-slate-400 w-64">' +
      '<select id="fv-status" class="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-slate-300"><option value="">alle Stände</option>' +
        stati.map(function(s) { return '<option value="' + s + '">' + fvEsc(FV_STATUS[s][1]) + "</option>"; }).join("") + "</select>" +
      '<span id="fv-anzahl" class="note"></span></div>' +
    '<div class="card overflow-x-auto"><table class="w-full text-xs"><thead><tr class="text-slate-500 text-left border-b border-slate-700">' +
      '<th class="p-2">Nr.</th><th class="p-2">Maßnahme</th><th class="p-2">Programm</th><th class="p-2">Stand</th><th class="p-2 text-right">Förderung</th><th class="p-2 text-right">Quote</th><th class="p-2">Bescheid</th></tr></thead>' +
      '<tbody id="fv-body"></tbody></table></div>' +
    '<p class="note mt-2">Zeile antippen zeigt den wörtlichen Satz aus der Erläuterung. Maschinell gelesen – der Stand kann sich seit dem Haushaltsplan geändert haben.</p>' +

    fvTitel("Vergabe-Lotse: welches Verfahren ist mindestens nötig?") +
    '<div class="card p-4"><div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-400">' +
      '<label class="flex flex-col gap-1">Auftragswert (netto, €)<input id="fv-wert" type="number" value="180000" min="0" step="1000" class="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-slate-200"></label>' +
      '<label class="flex flex-col gap-1">Leistungsart<select id="fv-art" class="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-slate-200"><option value="bau">Bauleistung</option><option value="liefer_dienst">Liefer-/Dienstleistung</option></select></label>' +
      '<label class="flex flex-col gap-1">Auftraggeber<select id="fv-ag" class="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-slate-200"><option value="kommune">Stadt / Beteiligung</option><option value="sektor">Versorger (Sektorenauftraggeber)</option></select></label>' +
      '<label class="flex flex-col gap-1">Gesamtwert der Maßnahme bei Losen (€)<input id="fv-gesamt" type="number" min="0" step="10000" placeholder="leer = kein Los" class="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-slate-200"></label>' +
      '<label class="flex items-center gap-2 text-slate-300"><input id="fv-foerder" type="checkbox" checked> mit Fördermitteln</label>' +
      '<label class="flex items-center gap-2 text-slate-300"><input id="fv-strasse" type="checkbox"> Straßenbau, über 8 Wochen</label>' +
    '</div><div id="fv-vl" class="mt-4 border-l-4 border-amber-500/60 pl-3 text-sm"></div></div>' +

    fvTitel("EU-Ausschreibungen des Stadtkonzerns (TED)") +
    '<div class="flex flex-wrap gap-3 items-center mb-3">' +
      '<input id="fv-tsuche" type="text" placeholder="Suche in Gegenstand, Auftraggeber, Zuschlag …" class="bg-slate-800 border border-slate-600 rounded px-3 py-1 text-xs text-slate-300 placeholder:text-slate-500 focus:outline-none focus:border-slate-400 w-72">' +
      '<select id="fv-ttyp" class="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-slate-300"><option value="">alle Arten</option>' +
        typen.map(function(t) { return '<option value="' + fvEsc(t) + '">' + fvEsc(FV_NOTICE[t] || t) + "</option>"; }).join("") + "</select>" +
      '<span id="fv-tanzahl" class="note"></span></div>' +
    '<div class="card overflow-x-auto"><table class="w-full text-xs"><thead><tr class="text-slate-500 text-left border-b border-slate-700">' +
      '<th class="p-2">Datum</th><th class="p-2">Art</th><th class="p-2">Gegenstand</th><th class="p-2">Auftraggeber</th><th class="p-2">Verfahren</th><th class="p-2">Zuschlag an</th><th class="p-2">Maßnahme (automatisch zugeordnet)</th></tr></thead>' +
      '<tbody id="fv-tbody"></tbody></table></div>' +
    '<p class="note mt-2">Quelle: Tenders Electronic Daily (ted.europa.eu). Zuordnung zu Maßnahmen automatisch über seltene Stichworte – unvollständig und ohne Gewähr.</p>' +

    '<div class="note mt-8">Rechtsgrundlagen: ' + (FV.quellen || []).map(function(q) {
      return '<a class="text-sky-400 hover:underline" href="' + fvEsc(q.url) + '" target="_blank" rel="noopener" title="' + fvEsc(q.titel) + '">' + fvEsc(q.kurz) + "</a>";
    }).join(" · ") + ". Orientierung, keine Rechtsauskunft.</div>";

  ["fv-suche", "fv-status"].forEach(function(id) { document.getElementById(id).addEventListener("input", fvFoerderTabelle); });
  ["fv-wert", "fv-art", "fv-ag", "fv-gesamt", "fv-foerder", "fv-strasse"].forEach(function(id) { document.getElementById(id).addEventListener("input", fvVergabeLotse); });
  ["fv-tsuche", "fv-ttyp"].forEach(function(id) { document.getElementById(id).addEventListener("input", fvTedTabelle); });
  document.getElementById("fv-body").addEventListener("click", function(e) {
    var tr = e.target.closest("tr[data-i]"); if (!tr) return;
    var nxt = tr.nextElementSibling;
    if (nxt && nxt.classList.contains("fv-beleg")) { nxt.remove(); return; }
    var f = FV.foerderung[Number(tr.dataset.i)];
    tr.insertAdjacentHTML("afterend", '<tr class="fv-beleg bg-slate-900/60"><td></td><td colspan="6" class="p-2 text-slate-400 italic">„' + fvEsc(f.beleg || "kein Beleg") + "“</td></tr>");
  });
  fvFoerderTabelle(); fvVergabeLotse(); fvTedTabelle();
}

function fvFoerderTabelle() {
  var s = document.getElementById("fv-suche").value.trim().toLowerCase(), st = document.getElementById("fv-status").value;
  var reihen = (FV.foerderung || []).map(function(f, i) { return [f, i]; }).filter(function(p) {
    var f = p[0];
    return (!st || f.status === st) && (!s || (f.investitionsnummer + " " + fvName(f.investitionsnummer) + " " + f.programm_text).toLowerCase().indexOf(s) >= 0);
  });
  document.getElementById("fv-anzahl").textContent = reihen.length + " von " + FV.foerderung.length + " Förderzeilen";
  document.getElementById("fv-body").innerHTML = reihen.map(function(p) {
    var f = p[0], s2 = FV_STATUS[f.status] || [FV_GRAU, f.status];
    return '<tr data-i="' + p[1] + '" class="border-b border-slate-800 cursor-pointer hover:bg-slate-800/60 align-top">' +
      '<td class="p-2 text-slate-500 whitespace-nowrap">' + fvEsc(f.investitionsnummer) + '</td><td class="p-2 text-slate-200">' + fvEsc(fvName(f.investitionsnummer)) +
      '</td><td class="p-2 text-slate-400">' + fvEsc(f.programm_text) + '</td><td class="p-2">' + fvPill(s2[0], s2[1]) +
      '</td><td class="p-2 text-right whitespace-nowrap text-slate-200">' + (f.foerdermittel_eur ? fvMio(f.foerdermittel_eur) : "–") +
      '</td><td class="p-2 text-right whitespace-nowrap text-slate-400">' + (f.quote_vorher ? fvQuote(f.quote_vorher) + " → " : "") + fvQuote(f.quote) +
      '</td><td class="p-2 whitespace-nowrap text-slate-400">' + fvDatum(f.bescheid_datum) + "</td></tr>";
  }).join("");
}

function fvVergabeLotse() {
  var wert = Number(document.getElementById("fv-wert").value) || 0, art = document.getElementById("fv-art").value, ag = document.getElementById("fv-ag").value;
  var gesamt = Number(document.getElementById("fv-gesamt").value) || 0, foerder = document.getElementById("fv-foerder").checked, strasse = document.getElementById("fv-strasse").checked;
  var EU = {bau: 5404000, liefer_dienst: ag === "sektor" ? 432000 : 216000}, KLEINLOS = {bau: 1000000, liefer_dienst: 80000};
  var VERF = {direktvergabe: "Direktvergabe", freihaendig: "Freihändige Vergabe", beschraenkt: "Beschränkte Ausschreibung", verhandlungsvergabe: "Verhandlungsvergabe", oeffentlich: "Öffentliche Ausschreibung"};
  var zeilen = [], massgeblich = wert, verfahren, quelle;
  if (gesamt && gesamt >= EU[art]) {
    massgeblich = gesamt;
    zeilen.push("Gesamtmaßnahme " + fvEuro(gesamt) + " erreicht die EU-Schwelle (" + fvEuro(EU[art]) + "): Lose sind grundsätzlich EU-weit auszuschreiben.");
    if (wert < KLEINLOS[art]) zeilen.push("Ausnahme möglich: Los unter " + fvEuro(KLEINLOS[art]) + " national vergeben, solange alle so vergebenen Lose höchstens 20 % des Gesamtwerts ausmachen (§ 3 Abs. 9 VgV).");
  }
  if (massgeblich >= EU[art]) { verfahren = "EU-weites Verfahren"; quelle = "EU-Schwellenwerte 2026/27"; }
  else if (ag === "sektor") { verfahren = "unterhalb der Sektoren-Schwelle: Regeln des Trägers (Satzung/Beschaffungsordnung)"; quelle = "SektVO gilt erst ab Schwelle"; }
  else {
    var g = (FV.wertgrenzen || []).filter(function(w) { return w.gilt_fuer === "kommune" && w.auftragsart === art && w.rechtsrahmen !== "EU"; })
      .find(function(w) { return w.max_netto_eur == null || massgeblich <= w.max_netto_eur; });
    verfahren = g ? (VERF[g.verfahrensart] || g.verfahrensart) : "Öffentliche Ausschreibung";
    quelle = g ? "ThürVVöA bis " + fvEuro(g.max_netto_eur) + (g.belegt ? "" : " (Wert unbelegt)") : "ThürVVöA";
  }
  if (foerder) zeilen.push("Förderbescheid prüfen: Die Vergabeauflage (Nr. 3 ANBest-Gk) kann ein strengeres Verfahren verlangen; ein Verstoß kann zur Rückforderung führen (Nr. 8 ANBest-Gk).");
  if (strasse && foerder) zeilen.push("§ 146 Abs. 2 TKG: Bei öffentlich finanzierten Verkehrsbauarbeiten über 8 Wochen Glasfaser-Leerrohre mitverlegen.");
  document.getElementById("fv-vl").innerHTML = '<p class="text-slate-100"><b>Mindestens: ' + fvEsc(verfahren) + '</b> <span class="note">(' + fvEsc(quelle) + ")</span></p>" +
    zeilen.map(function(z) { return '<p class="text-xs text-slate-400 mt-1">' + fvEsc(z) + "</p>"; }).join("") +
    '<p class="note mt-2">Entwurf, Orientierung, keine Rechtsauskunft. Vergabestelle und Förderbescheid sind maßgeblich.</p>';
}

function fvTedTabelle() {
  var s = document.getElementById("fv-tsuche").value.trim().toLowerCase(), typ = document.getElementById("fv-ttyp").value;
  var zu = {};
  (FV.zuordnung || []).forEach(function(z) { (zu[z.ted] = zu[z.ted] || []).push(z.nr); });
  var liste = (FV.ted || []).filter(function(t) {
    return (!typ || t.notice_type === typ) && (!s || [t.titel, t.auftraggeber, t.gewinner].join(" ").toLowerCase().indexOf(s) >= 0);
  });
  document.getElementById("fv-tanzahl").textContent = liste.length + " Bekanntmachungen";
  document.getElementById("fv-tbody").innerHTML = liste.slice(0, 200).map(function(t) {
    var ms = Array.from(new Set(zu[t.id] || [])).map(function(nr) { return fvEsc(fvName(nr) || nr); }).join(", ");
    return '<tr class="border-b border-slate-800 align-top"><td class="p-2 whitespace-nowrap text-slate-500">' + fvDatum(t.datum) + '</td><td class="p-2">' + fvPill(FV_GRAU, FV_NOTICE[t.notice_type] || t.notice_type) +
      '</td><td class="p-2"><a class="text-sky-400 hover:underline" href="' + fvEsc(t.url) + '" target="_blank" rel="noopener">' + fvEsc(t.titel) + '</a></td><td class="p-2 text-slate-400">' + fvEsc(t.auftraggeber) +
      '</td><td class="p-2 text-slate-400">' + fvEsc(FV_VERFAHREN[t.verfahrensart] || t.verfahrensart || "") + '</td><td class="p-2 text-slate-400">' + fvEsc(t.gewinner || "") +
      '</td><td class="p-2 text-slate-300">' + ms + "</td></tr>";
  }).join("") + (liste.length > 200 ? '<tr><td colspan="7" class="p-2 note">… ' + (liste.length - 200) + " weitere, Suche verfeinern</td></tr>" : "");
}
