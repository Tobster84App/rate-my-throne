# Rate My Throne – Projektplan

Stand: 03.11.2026 · Version 0.13

## ⚠️ Vor dem offiziellen Start (Pflicht)
- [x] Impressum: Name, Anschrift, E-Mail eingetragen (30.10.2026)
- [ ] Datenschutzerklärung: Verantwortlicher und Dienstleister eingetragen; GitHub (DPF + Standardvertragsklauseln) und Supabase erledigt; offen nur noch Brevo
- [ ] Rechtstexte von Fachleuten prüfen lassen (Entwurf ist keine Rechtsberatung)
- [ ] Cookie-Einwilligung erst nötig, sobald Werbung oder cookie-basierte Statistik eingebaut wird (derzeit nur technisch notwendige Speicherung; Seitenaufrufe werden ohne Cookies gezählt)
- [x] Eigene Domain www.rate-my-throne.com: DNS (All-Inkl), GitHub Pages mit HTTPS, Supabase-URLs (30.10.2026)
- [x] E-Mail-Versand über Brevo (Absender noreply@rate-my-throne.com), Domain bei Brevo authentifiziert, Test-Registrierung erfolgreich (30.10.2026)
- [x] AV-Vertrag Supabase: seit 01.08.2026 Bestandteil der Nutzungsbedingungen (Antwort Supabase Privacy Team, 02.11.2026); Übermittlung USA/Singapur per EU-Standardvertragsklauseln Modul 2 (TIA vom 14.03.2025)
- [x] AV-Vertrag All-Inkl abgeschlossen (30.10.2026, Stand der Bedingungen 25.08.2026; PDF im Drive). Achtung: Stammdaten bei All-Inkl zeigen „74193 Bruchsal“ statt Schwaigern – korrigieren und Vertrag neu erzeugen (Stand 03.11.: hochgeladene PDF zeigt noch Bruchsal)
- [ ] AV-Vertrag Brevo: laut Brevo Teil der Nutzungsbedingungen; Bestätigung und Firmierung vom Support ausstehend

## Stand
- Startseite (index.html): Erklärung, Live-Zahlen aus der Datenbank, Registrierung/Anmeldung, FAQ
- Karte (karte.html): öffentliche Toiletten aus OpenStreetMap, Bewertungen, Infokarte, „Nächste Toilette finden“ mit Route in Google Maps
- Online: https://www.rate-my-throne.com (alte Adresse tobster84app.github.io/rate-my-throne/ leitet weiter; rate-my-throne.de, rate-my-throne.net und ratemythrone.de leiten bei All-Inkl auf die .com-Adresse weiter)
- Datenbank & Konten: Supabase (Projekt „Rate My Throne“, eu-west-1)
- Code: https://github.com/Tobster84App/rate-my-throne (Sicherung: Code → Download ZIP; im Drive nur Dokumente)

## Erledigt seit 0.4
- App-Symbol (Krone aus Toilettensitz), als App installierbar
- Passwort vergessen/ändern, Konto löschen
- Moderation: Melden, eigene Bewertungen löschen, Admin-Übersicht (Admin: Konto kerntobias84@gmail.com)
- Bewertungsverlauf: erneut bewerten nach 30 Tagen, Trend „letzte 3 Monate vs. davor“
- Schriften und Bibliotheken lokal (vendor/), keine Verbindung zu Google Fonts oder CDNs
- Benutzernamen ändern
- Eingetragene Toiletten löschen: eigene, solange niemand anderes sie bewertet hat; Admin alle (Bewertungen werden mitgelöscht)
- Eigene Domain, Postfach info@rate-my-throne.com, Mail-Versand über Brevo
- Mail-Vorlagen DE/EN für alle sechs Supabase-Mails (supabase/email-templates, erzeugt mit build.py, in Supabase von Hand eingetragen)
- Mail-Links führen auf die Karte und werden erst nach Klick auf „Weiter“ eingelöst (Schutz vor Link-Scannern in Firmen-Postfächern)
- Filter: kostenlos, barrierefrei, Wickeltisch, ab 4 Sternen, nur bewertete (Toiletten ohne Angabe bleiben sichtbar, „Nächsten Thron finden“ beachtet die Filter)
- Mail-Limit in Supabase auf 100 pro Stunde erhöht
- Nutzer-Übersicht für Admins (Benutzername, Registrierung, letzte Anmeldung, Zahl der Bewertungen/Toiletten; ohne E-Mail-Adressen), Skript supabase/migrations/20261102_admin_users.sql
- Ortssuche (Nominatim/OpenStreetMap) zum Vorplanen: gesuchter Ort ersetzt den eigenen Standort für „Nächsten Thron finden“ und die Entfernungen; Datenschutzerklärung ergänzt
- Startseite: Abschnitt „Vorab planen“ (Ortssuche, Filter, mit Kind) mit Knopf, der die Ortssuche direkt öffnet; FAQ aktualisiert
- Aktualität: „zuletzt geprüft“, Kurzmeldungen mit Konto (ok/kein Papier/verschmutzt/geschlossen/defekt, 1 pro Stunde, 48 Std. sichtbar), Daumen hoch/runter ohne Konto (Bremse 30/Stunde je Toilette, 1 pro Tag im Browser)
- Bewertungen mit Detail-Kriterien (Papier, Seife, Handtrocknung, Geruch, Schloss) und Familie (Kinderwagen, Kindersitz, familienfreundlich); Abzeichen und Filter „Familienfreundlich“; Skript supabase/migrations/20261103_status_details.sql
- Seitenaufrufe je Tag (Startseite/Karte) ohne Personendaten, Admin-Ansicht „Statistik“; Skript supabase/migrations/20261103_page_views.sql
- Suchmaschinen: Titel mit Suchbegriffen, Vorschaubild für geteilte Links (Open Graph), Sprachfassungen (hreflang), kanonische Adressen
- Städte-Seiten für alle 64 Großstädte ab Heilbronn-Größe, 23 Urlaubsorte in Deutschland (z. B. Sylt, Rügen, Garmisch, Rust/Europa-Park) und 16 Urlaubsziele im Ausland (z. B. Mallorca, Rom, Paris, Wien) + Übersicht toiletten/: Liste mit Straße, Merkmalen, Öffnungszeiten, Bewertungen; Link öffnet die Toilette auf der Karte (karte.html?toilette=…). Erzeugt von tools/staedte.py, automatisch jede Woche per GitHub Action (.github/workflows/staedte.yml), inkl. sitemap.xml
- Startseite: Werbefilm (stumm, Endlosschleife) unter den Zahlen; auf Handys im Hochformat die Fassung 9x16; Dateien in media/ (je ca. 2 MB, ohne Tonspur, Poster = Schlussbild)

## Nächste Schritte
1. Google Search Console: eingerichtet und Sitemap eingereicht (03.11.2026); Status „Konnte nicht abgerufen werden“ beobachten, Indexierung für Startseite und /toiletten/ beantragt
2. Links von anderen Seiten sammeln (Tobias plant das)
3. Städte-Seiten auch auf Englisch; weitere Orte bei Bedarf in tools/staedte.py ergänzen
4. Vor Werbung prüfen: GitHub Pages ist nicht für überwiegend kommerzielle Seiten gedacht – ggf. Hoster wechseln
5. Werbung (z. B. Google AdSense) – erst mit eigener Domain und Rechtstexten, dann Cookie-Einwilligung nötig
6. Später: Rankings mit Humor („Thron der Woche“, beste/schlimmste Throne einer Stadt, Ehrentitel für fleißige Bewertende)

## Toiletten-Daten (seit 29.10.2026)
- OSM-Toiletten liegen in unserer Datenbank (Tabelle osm_toilets), die App fragt Overpass nicht mehr direkt
- Import läuft in der Datenbank selbst (pg_net + pg_cron, alle 20 Sekunden, Kacheln von 1°), Skript: supabase/migrations/20261029_osm_import_in_db.sql
- Deutschland ist vorgemerkt; neue Gegenden weltweit fordert die App beim ersten Besuch an (Funktion request_osm_tiles)
- Ist Overpass überlastet, wird die Kachel nach 10 Minuten erneut versucht; Aktualisierung jeder Kachel nach 7 Tagen
- Die Edge Function osm-sync wird nicht mehr benutzt (Overpass lehnt ihre Anfragen mit HTTP 406 ab) und kann im Supabase-Dashboard gelöscht werden
