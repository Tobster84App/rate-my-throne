# Rate My Throne – Projektplan

Stand: 29.10.2026 · Version 0.6

## ⚠️ Vor dem offiziellen Start (Pflicht)
- [ ] Impressum: Seite steht (impressum.html), gelbe Platzhalter mit Name, Anschrift, E-Mail füllen
- [ ] Datenschutzerklärung: Entwurf steht (datenschutz.html), Platzhalter füllen, Übermittlungsgrundlagen (GitHub, Supabase) prüfen, AV-Vertrag mit Supabase abschließen
- [ ] Rechtstexte von Fachleuten prüfen lassen (Entwurf ist keine Rechtsberatung)
- [ ] Cookie-Einwilligung erst nötig, sobald Werbung oder Statistik eingebaut wird (derzeit nur technisch notwendige Speicherung)
- [ ] Eigene Domain (ratemythrone.de/.com/.net waren laut Tobias am 29.10.2026 frei)

## Stand
- Startseite (index.html): Erklärung, Live-Zahlen aus der Datenbank, Registrierung/Anmeldung, FAQ
- Karte (karte.html): öffentliche Toiletten aus OpenStreetMap, Bewertungen, Infokarte, „Nächste Toilette finden“ mit Route in Google Maps
- Online: https://tobster84app.github.io/rate-my-throne/
- Datenbank & Konten: Supabase (Projekt „Rate My Throne“, eu-west-1)
- Code: https://github.com/Tobster84App/rate-my-throne (Kopie in Google Drive)

## Erledigt seit 0.4
- App-Symbol (Krone aus Toilettensitz), als App installierbar
- Passwort vergessen/ändern, Konto löschen
- Moderation: Melden, eigene Bewertungen löschen, Admin-Übersicht (Admin: Konto kerntobias84@gmail.com)
- Bewertungsverlauf: erneut bewerten nach 30 Tagen, Trend „letzte 3 Monate vs. davor“
- Schriften und Bibliotheken lokal (vendor/), keine Verbindung zu Google Fonts oder CDNs

## Nächste Schritte
1. Eigener E-Mail-Versand (für Bestätigungsmails, Passwort vergessen)
2. Werbung (z. B. Google AdSense) – erst mit eigener Domain und Rechtstexten, dann Cookie-Einwilligung nötig

## Toiletten-Daten (seit 29.10.2026)
- OSM-Toiletten liegen in unserer Datenbank (Tabelle osm_toilets), die App fragt Overpass nicht mehr direkt
- Import läuft in der Datenbank selbst (pg_net + pg_cron, alle 20 Sekunden, Kacheln von 1°), Skript: supabase/migrations/20261029_osm_import_in_db.sql
- Deutschland ist vorgemerkt; neue Gegenden weltweit fordert die App beim ersten Besuch an (Funktion request_osm_tiles)
- Ist Overpass überlastet, wird die Kachel nach 10 Minuten erneut versucht; Aktualisierung jeder Kachel nach 7 Tagen
- Die Edge Function osm-sync wird nicht mehr benutzt (Overpass lehnt ihre Anfragen mit HTTP 406 ab) und kann im Supabase-Dashboard gelöscht werden
