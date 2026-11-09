# Rate My Throne – Projektüberblick

Stand: 03.11.2026. Diese Datei kurz halten und bei wichtigen Änderungen selbst aktualisieren.

## Ziel und Zielgruppe
- Web-App/PWA zum Finden und Bewerten öffentlicher Toiletten, international (DE/EN), später mit Werbeeinnahmen.
- Lernprojekt von Tobias Kern (programmiert nicht selbst; alle Erklärungen auf Deutsch, verständlich, Rückfragen nummeriert als F1, F2 …).
- Zielgruppe: alle unterwegs, besonders Familien mit Kindern (Wickeltisch, vorab planen) und Menschen mit Mobilitätseinschränkung.

## Technik
- **Hosting:** GitHub Pages, Repo `Tobster84App/rate-my-throne`, Branch `main` = live. Domain www.rate-my-throne.com (DNS bei All-Inkl; .de/.net/ratemythrone.de leiten dort weiter, mit Let's-Encrypt-SSL bei All-Inkl; .com bekommt HTTPS von GitHub – dort kein All-Inkl-Zertifikat).
- **Frontend:** reines HTML/CSS/JS ohne Build. `index.html` (Startseite), `karte.html` (App), `impressum.html`, `datenschutz.html`, `i18n.js` (alle Texte DE/EN), `oh.js` (Öffnungszeiten), `toc.js` (Inhaltsverzeichnis: PC-Leiste, Handy-Knopf „☰ Inhalt“; Startseite + Datenschutz), `sw.js` (Service Worker, network-first), `media/` (Werbefilm 16x9/9x16), `toiletten/` + `toilets/` (Städte-Seiten DE/EN, erzeugt von `tools/staedte.py` per GitHub Action `.github/workflows/staedte.yml`, wöchentlich; nicht von Hand bearbeiten).
- **Bibliotheken lokal** in `vendor/` (Leaflet 1.9.4, supabase-js 2.45.4, Schriften) – keine CDNs, kein Google Fonts.
- **Datenbank/Konten:** Supabase, Projekt `bzgeqaseogawdptaqzgq`, eu-west-1. Tabellen u. a. `profiles`, `toilets` (eigene Einträge), `reviews`, `review_reports`, `toilet_reports` (Kurzmeldungen), `toilet_votes` (Daumen), `page_views` (Seitenaufrufe je Tag), `osm_toilets`/`osm_tiles` (OSM-Kopie). Zugriff über RLS und RPCs (`security definer`).
- **Datenquellen:** OpenStreetMap (Toiletten werden per pg_net/pg_cron in die DB importiert, Kacheln 1°), Nominatim (Ortssuche), OSM-Kartenbilder. Namensnennung „© OpenStreetMap-Mitwirkende“ (ODbL).
- **E-Mail:** Supabase Auth über Brevo-SMTP, Absender noreply@rate-my-throne.com; Vorlagen in `supabase/email-templates/` (erzeugt mit `build.py`, in Supabase von Hand eingetragen). Postfächer info@/admin@ bei All-Inkl.

## Wichtige Entscheidungen
- **OSM-Daten in eigener DB statt Live-Overpass:** Overpass war überlastet/langsam; Import läuft in der DB, weil Overpass Anfragen von Edge Functions ablehnte (HTTP 406).
- **Bewertungen:** drei Kategorien (Sauberkeit, Ausstattung, Erreichbarkeit); erneut bewerten frühestens nach 30 Tagen; Verlauf/Trend sichtbar. Detail-Kriterien als ja/nein/keine Angabe – „keine Angabe“ zählt nicht.
- **Aktualität:** Daumen hoch/runter für alle, mit und ohne Konto (ohne Personendaten, 1 pro Toilette und Tag im Browser, Bremse 30/Stunde je Toilette); Kurzmeldungen zusätzlich nur mit Konto (1 pro Person/Toilette/Stunde); beides 48 Std. sichtbar.
- **Moderation:** eigene Bewertungen löschen, fremde melden, Admin darf alles. Eingetragene Toiletten löschen: eigene ohne fremde Bewertungen, Admin alle.
- **Mail-Links** führen auf `karte.html?token_hash=…` und werden erst nach Klick auf „Weiter“ eingelöst (Link-Scanner in Firmen-Postfächern verbrauchten sonst die Einmal-Links).
- **Positionierung (04.11.2026):** Mitbewerber PeeFinder (peefinder.com, Android, werbefrei, 163.000 WCs, 6 Detailbewertungen) ist funktional breiter. Wir setzen auf **Live-Zustand, Familie/Vorab-Planen und Humor**, nicht auf Funktionsvielfalt.
- **Startseite:** oben Angebot (Toiletten gesamt, davon kostenlos, mit Wickeltisch – live aus der DB); Community-Zahlen (Bewertungen, Mitglieder, eingetragene Throne) erst ab 500 Bewertungen (`COURT_MIN` in index.html), vorher nur Einladung – kleine Zahlen schrecken ab.
- **Geld (04.11.2026):** Ziel kleiner Nebenverdienst. Vorschlag Stufenplan: jetzt keine Werbung (nach außen nicht „werbefrei für immer“ versprechen); ab ca. 10–20 Tsd. Seitenaufrufen/Monat eigene Sponsoren ohne Tracking (Städte-Seiten, als „Gesponsert“ gekennzeichnet); Banner mit Einwilligung höchstens auf Städte-Seiten, nie auf Karte/Details. Kein Spenden-Link vorerst; kein Hinweis „ohne Tracking“ auf der Startseite (Tobias’ Entscheidung). Konkrete Planung erst, wenn die Reichweite erreicht ist.
- **Ranglisten (04.11.2026):** Thron der Woche (Startseite, beste Durchschnittsnote der laufenden Woche), Goldene Throne (🏆 auf der Karte, Kartenausschnitt, mind. 3 Bewertungen), Hofstaat des Monats (meiste Bewertungen), Ehrentitel nach Anzahl Bewertungen (Knappe 1, Ritter 5, Burgherr*in 15, Herzog*in 30, Majestät 60). **Keine „Tatort-Liste“** (schlechteste Toiletten) – bewusst weggelassen. DB-Funktionen in `20261104_rankings.sql`.
- **Statistik:** nur Seitenaufrufe je Seite und Tag zählen – Startseite, Karte, Städte-Seiten als `city:<slug>` (keine Besucher, keine IP, nichts im Browser) – so ohne Cookie-Banner möglich; sichtbar nur für Admins.
- **SEO:** Karte ist für Google unsichtbar (JS) → statische Städte-Seiten mit Liste; Links `karte.html?toilette=<id>` bzw. `?lat=&lon=`. Sprachfassungen per `?lang=de/en` mit hreflang, canonical setzt i18n.js.
- **Datenschutz:** keine Tracking-/Werbe-Cookies, Standort nur im Browser, Ortssuche nur auf Knopfdruck (Nominatim-Regeln).

## Arbeitsweise
- **DB-Änderungen** als SQL-Datei in `supabase/migrations/` committen; Tobias führt sie über den Raw-GitHub-Link im Supabase SQL Editor aus (apply_migration-Rückfragen erreichen ihn nicht). `execute_sql` nur zum Lesen/Prüfen.
- **Tests:** Playwright mit nachgebauten Supabase-Antworten (Scratchpad), vor jedem Commit.
- **Google-Drive-Kopie** (Ordner „Rate My Throne“): nur Dokumente (Projektplan, CLAUDE.md, SQL-Skripte, Verträge, Anschreiben) nach Änderungen aktualisieren, alte Versionen in den Papierkorb. Code nicht im Drive – Sicherung über GitHub (Code → Download ZIP).
- Neue Texte immer in `i18n.js` für DE und EN; Projektplan in `PROJEKTPLAN.md` mitpflegen.

## Aktueller Stand
Karte mit OSM- und eigenen Toiletten, Bewertungen mit Trend, Detail-Kriterien und Familien-Abzeichen, Filter (jetzt geöffnet – Öffnungszeiten-Auswertung in `oh.js`, kostenlos, barrierefrei, Wickeltisch, familienfreundlich, ab 4 Sternen, nur bewertete), Ortssuche zum Vorplanen, Kurzmeldungen/Daumen, Konten (Registrierung, Passwort vergessen/ändern, Benutzername ändern, Konto löschen), Moderation, Admin-Statistik (Seitenaufrufe), Städte-Seiten (64 Großstädte ab Heilbronn-Größe, 23 Urlaubsorte in DE, 16 Urlaubsziele im Ausland), Startseite mit Werbefilm und „Vorab planen“, Impressum, Datenschutz, robots.txt/sitemap.xml.

## Offene Punkte
- Datenschutz: Brevo-Support-Bestätigung ausstehend; Rechtstexte prüfen lassen. (Erledigt: Supabase – DPA in den AGB, SCC Modul 2 laut TIA; GitHub – DPF-zertifiziert plus SCC laut GitHub Privacy Statement.)
- **GitHub Pages erlaubt laut Nutzungsgrenzen keine Seiten, die „primarily directed at … commercial transactions“ sind** – vor Werbung prüfen, ggf. Hoster wechseln.
- All-Inkl-Stammdaten: Ort „Bruchsal“ → Schwaigern korrigieren, AV-Vertrag neu erzeugen.
- Google Search Console eingerichtet (03.11.2026, Domain-Property per TXT). Sitemap anfangs „Konnte nicht abgerufen werden“ (bei neuen Domains üblich); Indexierung für / und /toiletten/ beantragt. Falls nach einigen Tagen weiter Fehler: zweite Sitemap mit anderem Namen anlegen.
- Städte-Seiten: Orte stehen in `GROUPS` (tools/staedte.py). Stadtmitte und Straßen kommen per Nominatim (Cache `toiletten/orte.json`, `adressen.json`, max. 1000 Straßenabfragen pro Lauf). Orte, deren OSM-Kacheln noch fehlen (Ausland), werden angefordert und erscheinen beim nächsten Lauf. Englische Namen in `EN_NAMES`, Texte in `TX`.
- SQL `20261109_city_views.sql` (Zählung der Städte-Seiten) muss Tobias noch ausführen; bis dahin schlägt die Zählung dort still fehl.
- Instagram-Konto für die Seite legt Tobias an (Werbefilm 9:16, „Thron der Woche“ als wöchentliches Format).
- Später: Werbung (vorher Gewerbe-Frage klären, Cookie-Einwilligung, Datenschutz ergänzen).
