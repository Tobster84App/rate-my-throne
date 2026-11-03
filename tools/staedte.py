#!/usr/bin/env python3
"""Erzeugt die Städte-Seiten toiletten/<stadt>.html, die Übersicht toiletten/index.html und sitemap.xml.

Daten: Toiletten und Bewertungen aus Supabase (öffentlich lesbar mit dem Publishable Key),
Straßennamen per Nominatim (Rückwärtssuche, höchstens 1 Anfrage pro Sekunde, Ergebnisse in toiletten/adressen.json zwischengespeichert).

Aufruf:  python3 tools/staedte.py                 (lädt alles aus dem Netz)
         python3 tools/staedte.py --daten x.json  (Testdaten statt Supabase, ohne Nominatim)
Läuft automatisch über .github/workflows/staedte.yml (wöchentlich und bei Änderungen an dieser Datei).
"""
import html, json, math, os, sys, time, urllib.parse, urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "toiletten")
BASE = "https://www.rate-my-throne.com/"
SUPABASE = "https://bzgeqaseogawdptaqzgq.supabase.co"
KEY = "sb_publishable_Uoawl08FsfsJwdv3eLVV0A_Zh5tT6EE"
UA = "RateMyThrone-Staedteseiten/1.0 (+https://www.rate-my-throne.com; info@rate-my-throne.com)"
MAX_LOOKUPS = 400  # Nominatim-Abfragen pro Lauf (Rest beim nächsten Lauf)

# Städte: Name, Mittelpunkt (Innenstadt) und Umkreis in km
CITIES = [
    {"slug": "heilbronn", "name": "Heilbronn", "lat": 49.1427, "lon": 9.2109, "km": 6},
    {"slug": "stuttgart", "name": "Stuttgart", "lat": 48.7784, "lon": 9.1800, "km": 6},
    {"slug": "schwaigern", "name": "Schwaigern", "lat": 49.1440, "lon": 9.0540, "km": 3},
]
STATIC_PAGES = ["", "karte.html", "impressum.html", "datenschutz.html"]


def get_json(url, headers):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **headers})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def supa(path):
    return get_json(f"{SUPABASE}/rest/v1/{path}", {"apikey": KEY, "Authorization": f"Bearer {KEY}"})


def dist_km(a_lat, a_lon, b_lat, b_lon):
    r = math.radians
    x = (r(b_lon) - r(a_lon)) * math.cos(r((a_lat + b_lat) / 2))
    return math.hypot(x, r(b_lat) - r(a_lat)) * 6371


def box(c):
    dlat = c["km"] / 111.0
    dlon = c["km"] / (111.0 * math.cos(math.radians(c["lat"])))
    return c["lat"] - dlat, c["lat"] + dlat, c["lon"] - dlon, c["lon"] + dlon


def yn(v):
    return "yes" if v is True else "no" if v is False else None


def load_city(c):
    a, b, d, e = box(c)
    flt = f"lat=gte.{a}&lat=lte.{b}&lon=gte.{d}&lon=lte.{e}"
    rows = supa(f"osm_toilets?select=id,lat,lon,name,operator,fee,wheelchair,changing_table,opening_hours&{flt}&limit=2000")
    own = supa(f"toilets?select=id,lat,lon,name,fee,wheelchair,changing_table&{flt}&limit=2000")
    rows += [{**o, "id": str(o["id"]), "operator": None, "opening_hours": None,
              "fee": yn(o["fee"]), "wheelchair": yn(o["wheelchair"]), "changing_table": yn(o["changing_table"])} for o in own]
    rows = [r for r in rows if dist_km(c["lat"], c["lon"], r["lat"], r["lon"]) <= c["km"]]
    revs = {}
    ids = [r["id"] for r in rows]
    for i in range(0, len(ids), 100):
        part = ",".join(f'"{x}"' for x in ids[i:i + 100])
        for v in supa(f"reviews?select=toilet_ref,clean,equip,access&toilet_ref=in.({urllib.parse.quote(part)})"):
            revs.setdefault(v["toilet_ref"], []).append((v["clean"] + v["equip"] + v["access"]) / 3)
    for r in rows:
        s = revs.get(r["id"], [])
        r["n"], r["avg"] = len(s), (round(sum(s) / len(s), 1) if s else None)
    return rows


def from_file(path):
    data = json.load(open(path, encoding="utf-8"))
    out = {}
    for r in data:
        out.setdefault(r["c"], []).append({"id": r["id"], "lat": r["lat"], "lon": r["lon"], "name": r.get("name"),
            "operator": r.get("op"), "fee": r.get("fee"), "wheelchair": r.get("wc"), "changing_table": r.get("ch"),
            "opening_hours": r.get("oh"), "n": r.get("n") or 0, "avg": r.get("avg")})
    return out


# ---------- Straßennamen (Nominatim) ----------
ADDR_FILE = os.path.join(OUT, "adressen.json")
lookups = 0


def street(r, cache, online):
    global lookups
    if r["id"] in cache:
        return cache[r["id"]]
    if not online or lookups >= MAX_LOOKUPS:
        return None
    lookups += 1
    time.sleep(1.1)
    try:
        j = get_json(f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=17&accept-language=de&lat={r['lat']}&lon={r['lon']}", {})
        a = j.get("address", {})
        road = a.get("road") or a.get("pedestrian") or a.get("footway") or a.get("square") or a.get("park")
        part = a.get("suburb") or a.get("city_district") or a.get("quarter")
        txt = ", ".join(x for x in (road, part) if x) or None
    except Exception as ex:  # einzelne Fehler überspringen
        print("Nominatim:", ex, file=sys.stderr)
        return None
    cache[r["id"]] = txt
    return txt


# ---------- HTML ----------
E = html.escape
CSS = """
.lead{font-size:18px;max-width:68ch}
.cta{display:inline-block;margin:8px 0 4px;background:var(--royal);color:#fff;text-decoration:none;font-weight:700;padding:12px 20px;border-radius:999px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:20px 0}
.kpi{background:var(--surface);border-radius:14px;padding:12px 14px}
.kpi b{display:block;font:800 26px/1.1 var(--display)}
.kpi span{color:var(--muted);font-size:14px}
ol.list{list-style:none;padding:0;margin:0;display:grid;gap:10px}
ol.list li{background:var(--surface);border-radius:14px;padding:12px 16px;max-width:none}
ol.list h3{font:700 17px/1.3 var(--display);margin:0}
.where{color:var(--muted);font-size:14px;margin:2px 0 6px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}
.chip{font-size:13px;border:1px solid var(--line);border-radius:999px;padding:2px 9px}
.chip.ok{border-color:#1f9d63;color:#1f9d63}
.chip.no{border-color:#c0392b;color:#c0392b}
.go{font-weight:700;font-size:14px}
.cities{display:flex;flex-wrap:wrap;gap:8px}
.cities a{background:var(--surface);border-radius:999px;padding:6px 14px;text-decoration:none;font-weight:600}
"""
HEADER = """<header>
  <a class="brand" href="../"><svg viewBox="86 100 340 332" aria-hidden="true"><path d="M120 300 104 150l84 70 68-110 68 110 84-70-16 150z" fill="#e3b341"/><ellipse cx="256" cy="330" rx="142" ry="74" fill="none" stroke="#e3b341" stroke-width="36"/></svg>Rate My&nbsp;<span>Throne</span></a>
</header>"""


def head(title, desc, url):
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#2a1f4d">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Rate My Throne">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}media/rate-my-throne-werbefilm-16x9-poster.jpg">
<meta property="og:locale" content="de_DE">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="../icons/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../vendor/fonts.css">
<link rel="stylesheet" href="../legal.css">
<style>{CSS}</style>
</head>
<body>
{HEADER}
<main>
"""


def foot(stand):
    return f"""
  <p class="muted">Toilettendaten: © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap-Mitwirkende</a> (ODbL), ergänzt und bewertet von der Rate-My-Throne-Community. Angaben ohne Gewähr, Stand {stand}.</p>
  <nav class="back"><a href="../">Startseite</a><a href="../karte.html">Karte</a><a href="./">Alle Städte</a><a href="../impressum.html">Impressum</a><a href="../datenschutz.html">Datenschutz</a></nav>
</main>
</body>
</html>
"""


def label(r):
    if r.get("name"):
        return r["name"]
    if r.get("operator"):
        return f"Toilette ({r['operator']})"
    return "Öffentliche Toilette"


def hours(oh):
    if not oh:
        return None
    oh = oh.strip('"')
    if oh == "24/7":
        return "rund um die Uhr"
    # OSM-Schreibweise (englische Kürzel) lesbar auf Deutsch
    import re
    words = {"Tu": "Di", "We": "Mi", "Th": "Do", "Su": "So", "PH": "Feiertag", "off": "geschlossen", "closed": "geschlossen",
             "Mar": "Mär", "May": "Mai", "Oct": "Okt", "Dec": "Dez"}
    return re.sub(r"\b(" + "|".join(words) + r")\b", lambda m: words[m.group(1)], oh)


def chips(r):
    out = []
    f, w, c = r.get("fee"), r.get("wheelchair"), r.get("changing_table")
    if f == "no": out.append(("ok", "kostenlos"))
    elif f == "yes": out.append(("", "kostenpflichtig"))
    if w in ("yes", "designated"): out.append(("ok", "rollstuhlgerecht"))
    elif w == "limited": out.append(("", "eingeschränkt barrierefrei"))
    elif w == "no": out.append(("no", "nicht barrierefrei"))
    if c == "yes": out.append(("ok", "Wickeltisch"))
    h = hours(r.get("opening_hours"))
    if h: out.append(("", "geöffnet: " + h))
    if not out: out.append(("", "noch keine Angaben"))
    return "".join(f'<span class="chip {k}">{E(t)}</span>' for k, t in out)


def nearest_names(rows, cond, n=3):
    sel = [r for r in rows if cond(r)][:n]
    return [label(r) + (f" – {r['street']}" if r.get("street") else "") for r in sel]


def city_page(c, rows, others, stand):
    n = len(rows)
    free = sum(1 for r in rows if r.get("fee") == "no")
    wc = sum(1 for r in rows if r.get("wheelchair") in ("yes", "designated"))
    ch = sum(1 for r in rows if r.get("changing_table") == "yes")
    rated = sum(1 for r in rows if r.get("n"))
    url = f"{BASE}toiletten/{c['slug']}.html"
    title = f"Öffentliche Toiletten in {c['name']} – Karte & Bewertungen | Rate My Throne"
    desc = (f"{n} öffentliche Toiletten in {c['name']}: {free} kostenlos, {wc} rollstuhlgerecht, {ch} mit Wickeltisch. "
            "Mit Öffnungszeiten, Bewertungen und Karte.")
    map_url = f"../karte.html?lat={c['lat']}&amp;lon={c['lon']}"
    p = [head(title, desc, url)]
    p.append(f"""  <h1>Öffentliche Toiletten in {E(c['name'])}</h1>
  <p class="lead">Rate My Throne kennt <strong>{n} öffentliche Toiletten</strong> im Umkreis von {c['km']} km um die Innenstadt von {E(c['name'])}.
  {free} davon sind kostenlos, {wc} rollstuhlgerecht und {ch} haben einen Wickeltisch. Die Liste ist nach Entfernung zur Innenstadt sortiert.</p>
  <a class="cta" href="{map_url}">Karte von {E(c['name'])} öffnen</a>
  <div class="kpis">
    <div class="kpi"><b>{n}</b><span>Toiletten</span></div>
    <div class="kpi"><b>{free}</b><span>kostenlos</span></div>
    <div class="kpi"><b>{wc}</b><span>rollstuhlgerecht</span></div>
    <div class="kpi"><b>{ch}</b><span>mit Wickeltisch</span></div>
    <div class="kpi"><b>{rated}</b><span>bewertet</span></div>
  </div>
""")
    tips = []
    fr = nearest_names(rows, lambda r: r.get("fee") == "no")
    if fr: tips.append(f"<h2>Wo gibt es kostenlose Toiletten in {E(c['name'])}?</h2><p>Am nächsten zur Innenstadt: {E('; '.join(fr))}.</p>")
    cr = nearest_names(rows, lambda r: r.get("changing_table") == "yes")
    if cr: tips.append(f"<h2>Wo finde ich einen Wickeltisch in {E(c['name'])}?</h2><p>Zum Beispiel hier: {E('; '.join(cr))}. Für die Planung mit Kind kannst du auf der Karte nach „Wickeltisch“ und „familienfreundlich“ filtern.</p>")
    wr = nearest_names(rows, lambda r: r.get("wheelchair") in ("yes", "designated"))
    if wr: tips.append(f"<h2>Barrierefreie Toiletten in {E(c['name'])}</h2><p>Rollstuhlgerecht laut Eintrag: {E('; '.join(wr))}.</p>")
    p.append("  " + "\n  ".join(tips) + "\n")
    p.append(f'  <h2>Alle {n} Toiletten in {E(c["name"])}</h2>\n  <ol class="list">\n')
    for r in rows:
        stars = f' · ★ {str(r["avg"]).replace(".", ",")} ({r["n"]} Bewertung{"en" if r["n"] != 1 else ""})' if r.get("n") else ""
        where = (E(r["street"]) + " · " if r.get("street") else "") + f"{str(round(r['km'], 1)).replace('.', ',')} km von der Innenstadt" + stars
        p.append(f"""    <li><h3>{E(label(r))}</h3><p class="where">{where}</p><div class="chips">{chips(r)}</div>
      <a class="go" href="../karte.html?toilette={urllib.parse.quote(r['id'])}">Auf der Karte zeigen und bewerten →</a></li>\n""")
    p.append("  </ol>\n")
    if others:
        p.append('  <h2>Weitere Städte</h2>\n  <div class="cities">' + "".join(f'<a href="{o["slug"]}.html">{E(o["name"])}</a>' for o in others) + "</div>\n")
    p.append(foot(stand))
    return "".join(p)


def index_page(cities, counts, stand):
    url = f"{BASE}toiletten/"
    p = [head("Öffentliche Toiletten nach Stadt | Rate My Throne",
              "Öffentliche Toiletten nach Stadt: kostenlos, barrierefrei, mit Wickeltisch – mit Karte und Bewertungen der Community.", url)]
    p.append('  <h1>Öffentliche Toiletten nach Stadt</h1>\n  <p class="lead">Wähle eine Stadt – oder öffne direkt die <a href="../karte.html">Karte</a>, sie funktioniert überall.</p>\n  <div class="cities">')
    p.append("".join(f'<a href="{c["slug"]}.html">{E(c["name"])} ({counts[c["slug"]]})</a>' for c in cities))
    p.append("</div>\n")
    p.append(foot(stand))
    return "".join(p)


def sitemap(cities):
    urls = [BASE + s for s in STATIC_PAGES] + [BASE + "toiletten/"] + [f"{BASE}toiletten/{c['slug']}.html" for c in cities]
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


def main():
    os.makedirs(OUT, exist_ok=True)
    test = "--daten" in sys.argv
    data = from_file(sys.argv[sys.argv.index("--daten") + 1]) if test else None
    cache = json.load(open(ADDR_FILE, encoding="utf-8")) if os.path.exists(ADDR_FILE) else {}
    stand = date.today().strftime("%d.%m.%Y")
    counts, per = {}, {}
    for c in CITIES:
        rows = data.get(c["slug"], []) if test else load_city(c)
        for r in rows:
            r["km"] = dist_km(c["lat"], c["lon"], r["lat"], r["lon"])
        rows.sort(key=lambda r: r["km"])
        for r in rows:
            r["street"] = street(r, cache, not test)
        per[c["slug"]], counts[c["slug"]] = rows, len(rows)
    for c in CITIES:
        others = [o for o in CITIES if o is not c]
        with open(os.path.join(OUT, c["slug"] + ".html"), "w", encoding="utf-8") as f:
            f.write(city_page(c, per[c["slug"]], others, stand))
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_page(CITIES, counts, stand))
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap(CITIES))
    if not test:
        with open(ADDR_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=0, sort_keys=True)
    print("fertig:", counts, "Nominatim-Abfragen:", lookups)


if __name__ == "__main__":
    main()
