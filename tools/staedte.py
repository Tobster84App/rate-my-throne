#!/usr/bin/env python3
"""Erzeugt die Städte-Seiten toiletten/<stadt>.html (Deutsch) und toilets/<city>.html (Englisch), die Übersichten und sitemap.xml.

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
MAX_LOOKUPS = 1000  # Nominatim-Straßenabfragen pro Lauf (Rest folgt in den nächsten Läufen)
MAX_LIST = 300      # höchstens so viele Toiletten pro Seite auflisten (die nächsten zur Innenstadt)

# Orte je Gruppe: (Gruppentitel, Ländercode, Umkreis km, Orte). Ein Ort ist "Name" oder ("Name", "Suchbegriff", Ländercode, km).
# Suchbegriff "@Breite,Länge" setzt den Mittelpunkt fest (wenn Nominatim die Gemeindefläche statt des Ortskerns liefert).
GROUPS = {
    "gross": ("Großstädte in Deutschland", "de", 6, [
        ("Berlin", None, None, 8), ("Hamburg", None, None, 8), ("München", None, None, 8), ("Köln", None, None, 8),
        "Frankfurt am Main", "Stuttgart", "Düsseldorf", "Leipzig", "Dortmund", "Essen", "Bremen", "Dresden", "Hannover",
        "Nürnberg", "Duisburg", "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster", "Mannheim", "Karlsruhe", "Augsburg",
        "Wiesbaden", "Mönchengladbach", "Gelsenkirchen", "Aachen", "Braunschweig", "Kiel", "Chemnitz", "Halle (Saale)",
        "Magdeburg", "Freiburg im Breisgau", "Krefeld", "Mainz", "Lübeck", "Erfurt", "Oberhausen", "Rostock", "Kassel",
        "Hagen", "Potsdam", "Saarbrücken", "Hamm", "Ludwigshafen am Rhein", ("Oldenburg", "Oldenburg, Niedersachsen"), "Mülheim an der Ruhr", "Osnabrück",
        "Leverkusen", "Darmstadt", "Heidelberg", "Solingen", "Herne", "Neuss", "Regensburg", "Paderborn", "Ingolstadt",
        "Offenbach am Main", "Würzburg", "Fürth", "Ulm", "Heilbronn", "Pforzheim", "Wolfsburg"]),
    "urlaub": ("Urlaubsorte in Deutschland", "de", 3, [
        ("Westerland (Sylt)", "Westerland"), "Norderney", ("Binz (Rügen)", "Binz"), ("Heringsdorf (Usedom)", "Heringsdorf"),
        "Timmendorfer Strand", "Warnemünde", "Stralsund", "Garmisch-Partenkirchen", "Berchtesgaden", "Füssen", ("Oberstdorf", "@47.4097,10.2797"),
        "Rothenburg ob der Tauber", "Bamberg", "Konstanz", ("Lindau (Bodensee)", "Lindau"), "Baden-Baden", ("Titisee-Neustadt", "@47.9003,8.1546"),
        ("Rüdesheim am Rhein", "@49.9790,7.9236"), "Cochem", "Wernigerode", "Quedlinburg", ("Rust (Europa-Park)", "Rust, Ortenaukreis"), "Schwaigern"]),
    "ausland": ("Urlaubsziele im Ausland", "", 5, [
        ("Palma (Mallorca)", "Palma", "es"), ("Barcelona", None, "es"), ("Rom", None, "it"), ("Venedig", None, "it"),
        ("Florenz", None, "it"), ("Paris", None, "fr"), ("Wien", None, "at"), ("Salzburg", None, "at"), ("Innsbruck", None, "at"),
        ("Amsterdam", None, "nl"), ("Prag", None, "cz"), ("London", None, "gb"), ("Lissabon", None, "pt"),
        ("Kopenhagen", None, "dk"), ("Budapest", None, "hu"), ("Zürich", None, "ch")]),
}


def slugify(name):
    s = name.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    s = "".join(ch if ch.isalnum() else "-" for ch in s.split("(")[0])
    return "-".join(x for x in s.split("-") if x)


def parse_cities():
    out = []
    for g, (_, cc, km, places) in GROUPS.items():
        for x in places:
            name, query, ccode, radius = (tuple(x) + (None,) * 3)[:4] if isinstance(x, tuple) else (x, None, None, None)
            out.append({"slug": slugify(name), "name": name, "query": query or name, "cc": ccode or cc, "km": radius or km, "group": g})
    return out


CITIES = parse_cities()
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


def supa_all(path):
    rows, off = [], 0
    while True:
        part = supa(f"{path}&order=id&limit=1000&offset={off}")
        rows += part
        if len(part) < 1000: return rows
        off += 1000


def tiles_ready(c):
    """Sind die OSM-Kacheln (1°) dieser Gegend importiert? Fehlende werden angefordert (für den nächsten Lauf)."""
    a, b, d, e = box(c)
    keys = sorted({f"{x}_{y}" for x in range(math.floor(d), math.floor(e) + 1) for y in range(math.floor(a), math.floor(b) + 1)})
    have = {t["key"] for t in supa(f"osm_tiles?select=key,status&status=eq.ok&key=in.({','.join(keys)})")}
    missing = [k for k in keys if k not in have]
    if missing:
        try:
            body = json.dumps({"keys": missing[:4]}).encode()
            req = urllib.request.Request(f"{SUPABASE}/rest/v1/rpc/request_osm_tiles", data=body, method="POST",
                headers={"User-Agent": UA, "apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=60).read()
        except Exception as ex:
            print("Import anfordern:", ex, file=sys.stderr)
    return not missing


def load_city(c):
    a, b, d, e = box(c)
    flt = f"lat=gte.{a}&lat=lte.{b}&lon=gte.{d}&lon=lte.{e}"
    rows = supa_all(f"osm_toilets?select=id,lat,lon,name,operator,fee,wheelchair,changing_table,opening_hours&{flt}")
    own = supa_all(f"toilets?select=id,lat,lon,name,fee,wheelchair,changing_table&{flt}")
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


# ---------- Nominatim: Stadtmitte und Straßennamen (zwischengespeichert) ----------
ADDR_FILE = os.path.join(OUT, "adressen.json")
PLACES_FILE = os.path.join(OUT, "orte.json")
lookups = 0


def geocode(c, places, online):
    """Mittelpunkt einer Stadt per Nominatim-Suche; Ergebnis bleibt in orte.json gespeichert."""
    if c["query"].startswith("@"):
        c["lat"], c["lon"] = map(float, c["query"][1:].split(","))
        return True
    key = f"{c['query']}|{c['cc']}"
    if key not in places and online:
        time.sleep(1.1)
        q = urllib.parse.urlencode({"q": c["query"], "format": "jsonv2", "limit": 1, "countrycodes": c["cc"], "accept-language": "de"})
        try:
            res = get_json(f"https://nominatim.openstreetmap.org/search?{q}", {})
            if res: places[key] = [round(float(res[0]["lat"]), 5), round(float(res[0]["lon"]), 5)]
        except Exception as ex:
            print("Ortssuche", c["name"], ex, file=sys.stderr)
    if key in places:
        c["lat"], c["lon"] = places[key]
        return True
    return False


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
# Englische Namen (sonst wie Deutsch)
EN_NAMES = {"München": "Munich", "Köln": "Cologne", "Nürnberg": "Nuremberg", "Hannover": "Hanover", "Frankfurt am Main": "Frankfurt",
    "Freiburg im Breisgau": "Freiburg", "Lindau (Bodensee)": "Lindau (Lake Constance)", "Rom": "Rome", "Venedig": "Venice",
    "Florenz": "Florence", "Wien": "Vienna", "Prag": "Prague", "Lissabon": "Lisbon", "Kopenhagen": "Copenhagen", "Zürich": "Zurich"}
DIRS = {"de": "toiletten", "en": "toilets"}
GROUP_EN = {"gross": "Major cities in Germany", "urlaub": "Holiday towns in Germany", "ausland": "Holiday destinations abroad"}

TX = {
 "de": dict(
    title="Öffentliche Toiletten in {c} – Karte & Bewertungen | Rate My Throne",
    desc="{n} öffentliche Toiletten in {c}: {free} kostenlos, {wc} rollstuhlgerecht, {ch} mit Wickeltisch. Mit Öffnungszeiten, Bewertungen und Karte.",
    h1="Öffentliche Toiletten in {c}",
    lead="Rate My Throne kennt <strong>{n} öffentliche Toiletten</strong> im Umkreis von {km} km um die Innenstadt von {c}. {free} davon sind kostenlos, {wc} rollstuhlgerecht und {ch} haben einen Wickeltisch. Die Liste ist nach Entfernung zur Innenstadt sortiert.",
    cta="Karte von {c} öffnen", k_n="Toiletten", k_free="kostenlos", k_wc="rollstuhlgerecht", k_ch="mit Wickeltisch", k_rated="bewertet",
    q_free="Wo gibt es kostenlose Toiletten in {c}?", a_free="Am nächsten zur Innenstadt: {x}.",
    q_ch="Wo finde ich einen Wickeltisch in {c}?", a_ch="Zum Beispiel hier: {x}. Für die Planung mit Kind kannst du auf der Karte nach „Wickeltisch“ und „familienfreundlich“ filtern.",
    q_wc="Barrierefreie Toiletten in {c}", a_wc="Rollstuhlgerecht laut Eintrag: {x}.",
    all="Alle {n} Toiletten in {c}", near="Die {k} Toiletten nahe der Innenstadt in {c}",
    more="Gezeigt werden die {k} Toiletten, die der Innenstadt am nächsten sind. Alle {n} findest du auf der <a href=\"{map}\">Karte</a>.",
    km="{d} km von der Innenstadt", rev1="Bewertung", revn="Bewertungen", go="Auf der Karte zeigen und bewerten →", others="Weitere Orte in der Nähe",
    t_toilet="Toilette ({op})", t_public="Öffentliche Toilette",
    c_free="kostenlos", c_fee="kostenpflichtig", c_wc="rollstuhlgerecht", c_wcl="eingeschränkt barrierefrei", c_wcn="nicht barrierefrei",
    c_ch="Wickeltisch", c_open="geöffnet: {h}", c_none="noch keine Angaben", h247="rund um die Uhr",
    i_title="Öffentliche Toiletten nach Stadt | Rate My Throne",
    i_desc="Öffentliche Toiletten nach Stadt: kostenlos, barrierefrei, mit Wickeltisch – mit Karte und Bewertungen der Community.",
    i_h1="Öffentliche Toiletten nach Stadt", i_lead="Wähle eine Stadt – oder öffne direkt die <a href=\"../karte.html\">Karte</a>, sie funktioniert überall.",
    src="Toilettendaten: © <a href=\"https://www.openstreetmap.org/copyright\" target=\"_blank\" rel=\"noopener\">OpenStreetMap-Mitwirkende</a> (ODbL), ergänzt und bewertet von der Rate-My-Throne-Community. Angaben ohne Gewähr, Stand {d}.",
    nav=[("../", "Startseite"), ("../karte.html", "Karte"), ("./", "Alle Städte"), ("../impressum.html", "Impressum"), ("../datenschutz.html", "Datenschutz")],
    q="", locale="de_DE", other="EN", other_label="English version"),
 "en": dict(
    title="Public toilets in {c} – map & reviews | Rate My Throne",
    desc="{n} public toilets in {c}: {free} free, {wc} wheelchair accessible, {ch} with baby changing. With opening hours, reviews and a map.",
    h1="Public toilets in {c}",
    lead="Rate My Throne knows <strong>{n} public toilets</strong> within {km} km of the centre of {c}. {free} of them are free, {wc} are wheelchair accessible and {ch} have baby changing facilities. The list is sorted by distance from the centre.",
    cta="Open the map of {c}", k_n="toilets", k_free="free", k_wc="wheelchair accessible", k_ch="baby changing", k_rated="reviewed",
    q_free="Where are free public toilets in {c}?", a_free="Closest to the centre: {x}.",
    q_ch="Where can I change a baby in {c}?", a_ch="For example here: {x}. Planning with kids? Filter the map by “baby changing” and “family-friendly”.",
    q_wc="Accessible toilets in {c}", a_wc="Wheelchair accessible according to the listing: {x}.",
    all="All {n} toilets in {c}", near="The {k} toilets closest to the centre of {c}",
    more="Showing the {k} toilets closest to the centre. You’ll find all {n} on the <a href=\"{map}\">map</a>.",
    km="{d} km from the centre", rev1="review", revn="reviews", go="Show on the map and rate →", others="More places nearby",
    t_toilet="Toilet ({op})", t_public="Public toilet",
    c_free="free", c_fee="paid", c_wc="wheelchair accessible", c_wcl="limited accessibility", c_wcn="not accessible",
    c_ch="baby changing", c_open="open: {h}", c_none="no details yet", h247="24/7",
    i_title="Public toilets by city | Rate My Throne",
    i_desc="Public toilets by city: free, accessible, with baby changing – with a map and community reviews.",
    i_h1="Public toilets by city", i_lead="Pick a city – or go straight to the <a href=\"../karte.html?lang=en\">map</a>, it works everywhere.",
    src="Toilet data: © <a href=\"https://www.openstreetmap.org/copyright\" target=\"_blank\" rel=\"noopener\">OpenStreetMap contributors</a> (ODbL), added to and rated by the Rate My Throne community. No guarantee of accuracy, as of {d}.",
    nav=[("../?lang=en", "Home"), ("../karte.html?lang=en", "Map"), ("./", "All cities"), ("../impressum.html?lang=en", "Legal notice"), ("../datenschutz.html?lang=en", "Privacy policy")],
    q="lang=en&amp;", locale="en_GB", other="DE", other_label="Deutsche Version"),
}


def num(x, lang):
    s = str(x)
    return s.replace(".", ",") if lang == "de" else s


def head(lang, title, desc, url, alt):
    """alt: {"de": url, "en": url} der Sprachfassungen"""
    other = "en" if lang == "de" else "de"
    links = "\n".join(f'<link rel="alternate" hreflang="{l}" href="{u}">' for l, u in alt.items())
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#2a1f4d">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
{links}
<link rel="alternate" hreflang="x-default" href="{alt["en"]}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Rate My Throne">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}media/rate-my-throne-werbefilm-16x9-poster.jpg">
<meta property="og:locale" content="{TX[lang]["locale"]}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="../icons/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../vendor/fonts.css">
<link rel="stylesheet" href="../legal.css">
<style>{CSS}</style>
</head>
<body>
<header>
  <a class="brand" href="../{"?lang=en" if lang == "en" else ""}"><svg viewBox="86 100 340 332" aria-hidden="true"><path d="M120 300 104 150l84 70 68-110 68 110 84-70-16 150z" fill="#e3b341"/><ellipse cx="256" cy="330" rx="142" ry="74" fill="none" stroke="#e3b341" stroke-width="36"/></svg>Rate My&nbsp;<span>Throne</span></a>
  <a class="lang" href="{alt[other].replace(BASE, "../")}" hreflang="{other}" lang="{other}" aria-label="{TX[lang]["other_label"]}">{TX[lang]["other"]}</a>
</header>
<main>
"""


def foot(lang, stand):
    t = TX[lang]
    nav = "".join(f'<a href="{h}">{E(x)}</a>' for h, x in t["nav"])
    return f"""
  <p class="muted">{t["src"].format(d=stand)}</p>
  <nav class="back">{nav}</nav>
</main>
</body>
</html>
"""


def label(r, lang):
    if r.get("name"):
        return r["name"]
    if r.get("operator"):
        return TX[lang]["t_toilet"].format(op=r["operator"])
    return TX[lang]["t_public"]


def hours(oh, lang="de"):
    if not oh:
        return None
    oh = oh.strip('"')
    if oh == "24/7":
        return TX[lang]["h247"]
    if lang == "en":
        return oh
    # OSM-Schreibweise (englische Kürzel) lesbar auf Deutsch
    import re
    words = {"Tu": "Di", "We": "Mi", "Th": "Do", "Su": "So", "PH": "Feiertag", "off": "geschlossen", "closed": "geschlossen",
             "Mar": "Mär", "May": "Mai", "Oct": "Okt", "Dec": "Dez"}
    return re.sub(r"\b(" + "|".join(words) + r")\b", lambda m: words[m.group(1)], oh)


def chips(r, lang):
    t, out = TX[lang], []
    f, w, c = r.get("fee"), r.get("wheelchair"), r.get("changing_table")
    if f == "no": out.append(("ok", t["c_free"]))
    elif f == "yes": out.append(("", t["c_fee"]))
    if w in ("yes", "designated"): out.append(("ok", t["c_wc"]))
    elif w == "limited": out.append(("", t["c_wcl"]))
    elif w == "no": out.append(("no", t["c_wcn"]))
    if c == "yes": out.append(("ok", t["c_ch"]))
    h = hours(r.get("opening_hours"), lang)
    if h: out.append(("", t["c_open"].format(h=h)))
    if not out: out.append(("", t["c_none"]))
    return "".join(f'<span class="chip {k}">{E(x)}</span>' for k, x in out)


def nearest_names(rows, cond, lang, n=3):
    sel = [r for r in rows if cond(r)][:n]
    return [label(r, lang) + (f" – {r['street']}" if r.get("street") else "") for r in sel]


def page_url(c, lang):
    return f"{BASE}{DIRS[lang]}/{c['slugs'][lang]}.html"


def city_page(c, rows, others, stand, lang):
    t, name = TX[lang], c["names"][lang]
    n = len(rows)
    free = sum(1 for r in rows if r.get("fee") == "no")
    wc = sum(1 for r in rows if r.get("wheelchair") in ("yes", "designated"))
    ch = sum(1 for r in rows if r.get("changing_table") == "yes")
    rated = sum(1 for r in rows if r.get("n"))
    v = dict(c=E(name), n=n, free=free, wc=wc, ch=ch, km=c["km"])
    map_url = f"../karte.html?{t['q']}lat={c['lat']}&amp;lon={c['lon']}"
    alt = {l: page_url(c, l) for l in DIRS}
    p = [head(lang, t["title"].format(**{**v, "c": name}), t["desc"].format(**{**v, "c": name}), alt[lang], alt)]
    p.append(f"""  <h1>{t["h1"].format(**v)}</h1>
  <p class="lead">{t["lead"].format(**v)}</p>
  <a class="cta" href="{map_url}">{t["cta"].format(**v)}</a>
  <div class="kpis">
    <div class="kpi"><b>{n}</b><span>{t["k_n"]}</span></div>
    <div class="kpi"><b>{free}</b><span>{t["k_free"]}</span></div>
    <div class="kpi"><b>{wc}</b><span>{t["k_wc"]}</span></div>
    <div class="kpi"><b>{ch}</b><span>{t["k_ch"]}</span></div>
    <div class="kpi"><b>{rated}</b><span>{t["k_rated"]}</span></div>
  </div>
""")
    tips = []
    for key, cond in (("free", lambda r: r.get("fee") == "no"), ("ch", lambda r: r.get("changing_table") == "yes"),
                      ("wc", lambda r: r.get("wheelchair") in ("yes", "designated"))):
        x = nearest_names(rows, cond, lang)
        if x: tips.append(f'<h2>{t["q_" + key].format(**v)}</h2><p>{t["a_" + key].format(x=E("; ".join(x)))}</p>')
    p.append("  " + "\n  ".join(tips) + "\n")
    shown = min(n, MAX_LIST)
    p.append(f'  <h2>{(t["all"] if n <= MAX_LIST else t["near"]).format(**v, k=shown)}</h2>\n  <ol class="list">\n')
    for r in rows[:MAX_LIST]:
        stars = f' · ★ {num(r["avg"], lang)} ({r["n"]} {t["rev1"] if r["n"] == 1 else t["revn"]})' if r.get("n") else ""
        where = (E(r["street"]) + " · " if r.get("street") else "") + t["km"].format(d=num(round(r["km"], 1), lang)) + stars
        p.append(f"""    <li><h3>{E(label(r, lang))}</h3><p class="where">{where}</p><div class="chips">{chips(r, lang)}</div>
      <a class="go" href="../karte.html?{t["q"]}toilette={urllib.parse.quote(r['id'])}">{t["go"]}</a></li>\n""")
    p.append("  </ol>\n")
    if n > shown:
        p.append(f'  <p class="muted">{t["more"].format(k=shown, n=n, map=map_url)}</p>\n')
    if others:
        p.append(f'  <h2>{t["others"]}</h2>\n  <div class="cities">' + "".join(f'<a href="{o["slugs"][lang]}.html">{E(o["names"][lang])}</a>' for o in others) + "</div>\n")
    p.append(foot(lang, stand))
    return "".join(p)


def index_page(cities, counts, stand, lang):
    t = TX[lang]
    alt = {l: f"{BASE}{DIRS[l]}/" for l in DIRS}
    p = [head(lang, t["i_title"], t["i_desc"], alt[lang], alt)]
    p.append(f'  <h1>{t["i_h1"]}</h1>\n  <p class="lead">{t["i_lead"]}</p>\n')
    for g, (title, *_ ) in GROUPS.items():
        sel = sorted((c for c in cities if c["group"] == g), key=lambda c: c["names"][lang])
        if not sel: continue
        p.append(f'  <h2>{E(title if lang == "de" else GROUP_EN[g])}</h2>\n  <div class="cities">')
        p.append("".join(f'<a href="{c["slugs"][lang]}.html">{E(c["names"][lang])} ({counts[c["slug"]]})</a>' for c in sel))
        p.append("</div>\n")
    p.append(foot(lang, stand))
    return "".join(p)


def sitemap(cities):
    urls = [BASE + s for s in STATIC_PAGES] + [BASE + s + "?lang=en" for s in STATIC_PAGES]
    for lang in DIRS:
        urls += [f"{BASE}{DIRS[lang]}/"] + [page_url(c, lang) for c in cities]
    body = "\n".join(f"  <url><loc>{u.replace('&', '&amp;')}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


def main():
    for d in DIRS.values():
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    for c in CITIES:
        c["names"] = {"de": c["name"], "en": EN_NAMES.get(c["name"], c["name"])}
        c["slugs"] = {"de": c["slug"], "en": slugify(c["names"]["en"])}
    test = "--daten" in sys.argv
    data = from_file(sys.argv[sys.argv.index("--daten") + 1]) if test else None
    load = lambda f: json.load(open(f, encoding="utf-8")) if os.path.exists(f) else {}
    cache, places = load(ADDR_FILE), load(PLACES_FILE)
    stand = date.today().strftime("%d.%m.%Y")
    counts, per, ready, waiting = {}, {}, [], []
    for c in CITIES:
        if test:
            if c["slug"] not in data: continue
            rows = data[c["slug"]]
            c["lat"], c["lon"] = rows[0]["lat"], rows[0]["lon"]
        else:
            try:
                if not geocode(c, places, True) or not tiles_ready(c):
                    waiting.append(c["name"]); continue
                rows = load_city(c)
            except Exception as ex:   # eine Stadt mit Fehler überspringen, die anderen trotzdem erzeugen
                print("Fehler bei", c["name"], ex, file=sys.stderr)
                waiting.append(c["name"]); continue
        if not rows:
            waiting.append(c["name"]); continue
        for r in rows:
            r["km"] = dist_km(c["lat"], c["lon"], r["lat"], r["lon"])
        rows.sort(key=lambda r: r["km"])
        per[c["slug"]], counts[c["slug"]] = rows, len(rows)
        ready.append(c)
    # Straßennamen: reihum je Stadt von innen nach außen, damit jede Stadt zuerst ihre Innenstadt bekommt
    order = sorted(((i, r) for c in ready for i, r in enumerate(per[c["slug"]][:MAX_LIST])), key=lambda x: x[0])
    for _, r in order:
        r["street"] = street(r, cache, not test)
    for c in ready:
        others = sorted((o for o in ready if o is not c), key=lambda o: dist_km(c["lat"], c["lon"], o["lat"], o["lon"]))[:8]
        for lang, d in DIRS.items():
            with open(os.path.join(ROOT, d, c["slugs"][lang] + ".html"), "w", encoding="utf-8") as f:
                f.write(city_page(c, per[c["slug"]], others, stand, lang))
    # Seiten von Orten, die nicht mehr in der Liste stehen, entfernen; noch nicht fertige Orte behalten ihre alte Seite
    for lang, d in DIRS.items():
        keep = {c["slugs"][lang] for c in CITIES}
        for fn in os.listdir(os.path.join(ROOT, d)):
            if fn.endswith(".html") and fn != "index.html" and fn[:-5] not in keep:
                os.remove(os.path.join(ROOT, d, fn))
    listed = [c for c in CITIES if all(os.path.exists(os.path.join(ROOT, d, c["slugs"][l] + ".html")) for l, d in DIRS.items())]
    for c in listed:
        counts.setdefault(c["slug"], "…")
    for lang, d in DIRS.items():
        with open(os.path.join(ROOT, d, "index.html"), "w", encoding="utf-8") as f:
            f.write(index_page(listed, counts, stand, lang))
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap(listed))
    if not test:
        for fn, d in ((ADDR_FILE, cache), (PLACES_FILE, places)):
            with open(fn, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=0, sort_keys=True)
    print("fertig:", len(ready), "Orte", counts, "| wartet noch:", waiting, "| Nominatim-Abfragen:", lookups)


if __name__ == "__main__":
    main()
