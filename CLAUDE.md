# Rate My Throne – Projektüberblick

Stand: 03.11.2026. Diese Datei kurz halten und bei wichtigen Änderungen selbst aktualisieren.

## Ziel und Zielgruppe
- Web-App/PWA zum Finden und Bewerten öffentlicher Toiletten, international (DE/EN), später mit Werbeeinnahmen.
- Lernprojekt von Tobias Kern (programmiert nicht selbst; alle Erklärungen auf Deutsch, verständlich, Rückfragen nummeriert als F1, F2 …).
- Zielgruppe: alle unterwegs, besonders Familien mit Kindern (Wickeltisch, vorab planen) und Menschen mit Mobilitätseinschränkung.

## Technik
- **Hosting:** GitHub Pages, Repo `Tobster84App/rate-my-throne`, Branch `main` = live. Domain www.rate-my-throne.com (DNS bei All-Inkl; .de/.net/ratemythrone.de leiten dort weiter).
- **Frontend:** reines HTML/CSS/JS ohne Build. `index.html` (Startseite), `karte.html` (App), `impressum.html`, `datenschutz.html`, `i18n.js` (alle Texte DE/EN), `sw.js` (Service Worker, network-first), `media/` (Werbefilm 16x9/9x16), `toiletten/` (Städte-Seiten, erzeugt von `tools/staedte.py` per GitHub Action `.github/workflows/staedte.yml`, wöchentlich; nicht von Hand bearbeiten).
- **Bibliotheken lokal** in `vendor/` (Leaflet 1.9.4, supabase-js 2.45.4, Schriften) – keine CDNs, kein Google Fonts.
- **Datenbank/Konten:** Supabase, Projekt `bzgeqaseogawdptaqzgq`, eu-west-1. Tabellen u. a. `profiles`, `toilets` (eigene Einträge), `reviews`, `review_reports`, `toilet_reports` (Kurzmeldungen), `toilet_votes` (Daumen), `page_views` (Seitenaufrufe je Tag), `osm_toilets`/`osm_tiles` (OSM-Kopie). Zugriff über RLS und RPCs (`security definer`).
- **Datenquellen:** OpenStreetMap (Toiletten werden per pg_net/pg_cron in die DB importiert, Kacheln 1°), Nominatim (Ortssuche), OSM-Kartenbilder. Namensnennung „© OpenStreetMap-Mitwirkende“ (ODbL).
- **E-Mail:** Supabase Auth über Brevo-SMTP, Absender noreply@rate-my-throne.com; Vorlagen in `supabase/email-templates/` (erzeugt mit `build.py`, in Supabase von Hand eingetragen). Postfächer info@/admin@ bei All-Inkl.

## Wichtige Entscheidungen
- **OSM-Daten in eigener DB statt Live-Overpass:** Overpass war überlastet/langsam; Import läuft in der DB, weil Overpass Anfragen von Edge Functions ablehnte (HTTP 406).
- **Bewertungen:** drei Kategorien (Sauberkeit, Ausstattung, Erreichbarkeit); erneut bewerten frühestens nach 30 Tagen; Verlauf/Trend sichtbar. Detail-Kriterien als ja/nein/keine Angabe – „keine Angabe“ zählt nicht.
- **Aktualität:** Kurzmeldungen nur mit Konto (1 pro Person/Toilette/Stunde, 48 Std. sichtbar); ohne Konto nur Daumen hoch/runter (ohne Personendaten, Bremse 30/Stunde je Toilette).
- **Moderation:** eigene Bewertungen löschen, fremde melden, Admin darf alles. Eingetragene Toiletten löschen: eigene ohne fremde Bewertungen, Admin alle.
- **Mail-Links** führen auf `karte.html?token_hash=…` und werden erst nach Klick auf „Weiter“ eingelöst (Link-Scanner in Firmen-Postfächern verbrauchten sonst die Einmal-Links).
- **Statistik:** nur Seitenaufrufe je Seite und Tag zählen (keine Besucher, keine IP, nichts im Browser) – so ohne Cookie-Banner möglich; sichtbar nur für Admins.
- **SEO:** Karte ist für Google unsichtbar (JS) → statische Städte-Seiten mit Liste; Links `karte.html?toilette=<id>` bzw. `?lat=&lon=`. Sprachfassungen per `?lang=de/en` mit hreflang, canonical setzt i18n.js.
- **Datenschutz:** keine Tracking-/Werbe-Cookies, Standort nur im Browser, Ortssuche nur auf Knopfdruck (Nominatim-Regeln).

## Arbeitsweise
- **DB-Änderungen** als SQL-Datei in `supabase/migrations/` committen; Tobias führt sie über den Raw-GitHub-Link im Supabase SQL Editor aus (apply_migration-Rückfragen erreichen ihn nicht). `execute_sql` nur zum Lesen/Prüfen.
- **Tests:** Playwright mit nachgebauten Supabase-Antworten (Scratchpad), vor jedem Commit.
- **Google-Drive-Kopie** (Ordner „Rate My Throne“): nur Dokumente (Projektplan, CLAUDE.md, SQL-Skripte, Verträge, Anschreiben) nach Änderungen aktualisieren, alte Versionen in den Papierkorb. Code nicht im Drive – Sicherung über GitHub (Code → Download ZIP).
- Neue Texte immer in `i18n.js` für DE und EN; Projektplan in `PROJEKTPLAN.md` mitpflegen.

## Aktueller Stand
Karte mit OSM- und eigenen Toiletten, Bewertungen mit Trend, Detail-Kriterien und Familien-Abzeichen, Filter (kostenlos, barrierefrei, Wickeltisch, familienfreundlich, ab 4 Sternen, nur bewertete), Ortssuche zum Vorplanen, Kurzmeldungen/Daumen, Konten (Registrierung, Passwort vergessen/ändern, Benutzername ändern, Konto löschen), Moderation, Admin-Statistik (Seitenaufrufe), Städte-Seiten (64 Großstädte ab Heilbronn-Größe, 23 Urlaubsorte in DE, 16 Urlaubsziele im Ausland), Startseite mit Werbefilm und „Vorab planen“, Impressum, Datenschutz, robots.txt/sitemap.xml.

## Offene Punkte
- Datenschutz: Brevo-Support-Bestätigung ausstehend; Rechtstexte prüfen lassen. (Erledigt: Supabase – DPA in den AGB, SCC Modul 2 laut TIA; GitHub – DPF-zertifiziert plus SCC laut GitHub Privacy Statement.)
- **GitHub Pages erlaubt laut Nutzungsgrenzen keine Seiten, die „primarily directed at … commercial transactions“ sind** – vor Werbung prüfen, ggf. Hoster wechseln.
- All-Inkl-Stammdaten: Ort „Bruchsal“ → Schwaigern korrigieren, AV-Vertrag neu erzeugen.
- SQL `20261102_admin_users.sql` (Nutzer-Übersicht) noch nicht ausgeführt; Knopf „Nutzer“ zeigt bis dahin einen Fehler.
- Google Search Console einrichten (Mail-Limit auf 100/Std. erledigt).
- Städte-Seiten: Orte stehen in `GROUPS` (tools/staedte.py). Stadtmitte und Straßen kommen per Nominatim (Cache `toiletten/orte.json`, `adressen.json`, max. 1000 Straßenabfragen pro Lauf). Orte, deren OSM-Kacheln noch fehlen (Ausland), werden angefordert und erscheinen beim nächsten Lauf. Seiten nur auf Deutsch.
- Später: Rankings mit Humor; Werbung (vorher Gewerbe-Frage klären, Cookie-Einwilligung, Datenschutz ergänzen).
