// Öffnungszeiten aus OpenStreetMap (opening_hours) auswerten: „jetzt geöffnet?“ und lesbare Anzeige.
// Unterstützt die häufigen Formen: 24/7 · Mo-Fr 08:00-18:00; Sa 09:00-12:00 · Mo-Su 06:00-22:00 · Mar-Oct 10:00-18:00 ·
// mehrere Zeiten (08:00-12:00,13:00-17:00) · über Mitternacht (22:00-02:00) · off/closed.
// Alles Kompliziertere (Feiertage allein, Sonnenauf-/untergang, Datumsbereiche, Kommentare) ergibt null = unbekannt.
const OH = (() => {
  const DAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const range = (list, a, b) => {           // zyklischer Bereich, z. B. Fr-Mo oder Nov-Feb
    const i = list.indexOf(a), j = list.indexOf(b), out = [];
    if (i < 0 || j < 0) return null;
    for (let k = i; ; k = (k + 1) % list.length) { out.push(k); if (k === j) break; }
    return out;
  };
  const toMin = s => { const m = /^(\d{1,2}):(\d{2})$/.exec(s); return m ? +m[1] * 60 + +m[2] : null; };

  // Eine Regel zerlegen: { months: Set|null, days: Set|null, times: [[von, bis]] | "off" }
  function parseRule(rule) {
    let r = rule.trim();
    if (!r) return null;
    const out = { months: null, days: null, times: null };
    // Monate am Anfang, z. B. "Mar-Oct" oder "May,Jun"
    let m = /^((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))?(?:,(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))?)*)(?=\s|:|$)\s*:?\s*/.exec(r);
    if (m) {
      out.months = new Set();
      for (const part of m[1].split(",")) {
        const [a, b] = part.split("-");
        const idx = b ? range(MONTHS, a, b) : [MONTHS.indexOf(a)];
        if (!idx) return undefined;
        idx.forEach(i => out.months.add(i));
      }
      r = r.slice(m[0].length);
    }
    // Wochentage, z. B. "Mo-Fr", "Sa,Su,PH"
    m = /^((?:Mo|Tu|We|Th|Fr|Sa|Su|PH|SH)(?:-(?:Mo|Tu|We|Th|Fr|Sa|Su))?(?:\s*,\s*(?:Mo|Tu|We|Th|Fr|Sa|Su|PH|SH)(?:-(?:Mo|Tu|We|Th|Fr|Sa|Su))?)*)(?=\s|$)\s*/.exec(r);
    if (m) {
      out.days = new Set();
      for (const part of m[1].split(/\s*,\s*/)) {
        if (part === "PH" || part === "SH") continue;          // Feiertage/Ferien kennen wir nicht
        const [a, b] = part.split("-");
        const idx = b ? range(DAYS, a, b) : [DAYS.indexOf(a)];
        if (!idx) return undefined;
        idx.forEach(i => out.days.add(i));
      }
      if (!out.days.size) return null;                       // nur "PH …": für normale Tage bedeutungslos
      r = r.slice(m[0].length);
    }
    r = r.trim();
    if (r === "off" || r === "closed") { out.times = "off"; return out; }
    if (r === "24/7" || r === "" || r === "open") { out.times = [[0, 1440]]; return out; }
    out.times = [];
    for (const span of r.split(/\s*,\s*/)) {
      if (/^\d{1,2}:\d{2}\+$/.test(span)) { out.times.push([toMin(span.slice(0, -1)), 1440]); continue; }   // "18:00+" = ab 18 Uhr
      const [a, b] = span.split("-");
      const from = toMin(a);
      let to = toMin(b);
      if (from == null || to == null) return undefined;
      if (to === 0) to = 1440;                                  // "06:00-00:00" bzw. "00:00-00:00" = bis Mitternacht
      out.times.push([from, to]);
    }
    return out;
  }

  function parse(oh) {
    if (!oh || typeof oh !== "string") return null;
    let s = oh.trim();
    if (/^"[^"]*"$/.test(s)) return null;                    // nur ein Kommentar, z. B. "nur bei Veranstaltungen"
    s = s.replace(/\s*"[^"]*"/g, "").trim();                 // Kommentare hinter einer Angabe weglassen
    if (s === "24/7") return [{ months: null, days: null, times: [[0, 1440]], add: false }];
    if (!s || /unknown|sunrise|sunset|dawn|dusk|week|easter|\[|\|\|/.test(s)) return null;
    const rules = [];
    for (const group of s.split(/\s*;\s*/)) {
      // Mit Komma angehängte Regeln ("Mo-Fr 08:00-12:00, Th 14:00-17:00") ergänzen, statt zu ersetzen
      group.split(/,\s*(?=(?:Mo|Tu|We|Th|Fr|Sa|Su|PH|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b)/).forEach((part, i) => {
        const rule = parseRule(part);
        if (rule === undefined) rules.push(undefined);
        else if (rule) rules.push({ ...rule, add: i > 0 });
      });
    }
    if (rules.includes(undefined)) return null;               // etwas nicht verstanden → lieber „unbekannt“
    return rules.length ? rules : null;
  }

  // true = geöffnet, false = geschlossen, null = unbekannt
  function isOpen(oh, now = new Date()) {
    const rules = parse(oh);
    if (!rules) return null;
    const day = now.getDay(), month = now.getMonth(), min = now.getHours() * 60 + now.getMinutes();
    const yesterday = (day + 6) % 7;
    let today = null, spill = false;   // spill: Zeit von gestern, die über Mitternacht reicht
    for (const r of rules) {
      if (r.months && !r.months.has(month)) continue;
      if (!r.days || r.days.has(day)) {                         // spätere Regel ersetzt frühere für diesen Tag …
        today = r.add && today && today.times !== "off" && r.times !== "off"
          ? { ...r, times: today.times.concat(r.times) } : r;   // … außer sie ist mit Komma angehängt
      }
      if (r.times !== "off" && (!r.days || r.days.has(yesterday)) && r.times.some(([a, b]) => b < a && min < b)) spill = true;
    }
    if (spill) return true;
    if (!today || today.times === "off") return false;
    return today.times.some(([a, b]) => (b > a ? min >= a && min < b : min >= a));
  }

  // Anzeige: Kürzel in der jeweiligen Sprache
  function format(oh, lang) {
    if (!oh) return "";
    const s = oh.trim().replace(/^"|"$/g, "");
    if (s === "24/7") return lang === "de" ? "rund um die Uhr" : "24/7";
    if (lang !== "de") return s;
    const w = { Tu: "Di", We: "Mi", Th: "Do", Su: "So", PH: "Feiertag", off: "geschlossen", closed: "geschlossen",
                Mar: "Mär", May: "Mai", Oct: "Okt", Dec: "Dez" };
    return s.replace(/\b(Tu|We|Th|Su|PH|off|closed|Mar|May|Oct|Dec)\b/g, x => w[x]);
  }

  return { isOpen, format, parse };
})();
if (typeof module !== "undefined") module.exports = OH;
