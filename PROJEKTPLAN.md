# Rate My Throne – Projektplan

Stand: 30.10.2026 · Version 0.7

## ⚠️ Vor dem offiziellen Start (Pflicht)
- [x] Impressum: Name, Anschrift, E-Mail eingetragen (30.10.2026)
- [ ] Datenschutzerklärung: Verantwortlicher eingetragen; noch offen: Übermittlungsgrundlagen (GitHub, Supabase) prüfen, AV-Vertrag mit Supabase abschließen
- [ ] Rechtstexte von Fachleuten prüfen lassen (Entwurf ist keine Rechtsberatung)
- [ ] Cookie-Einwilligung erst nötig, sobald Werbung oder Statistik eingebaut wird (derzeit nur technisch notwendige Speicherung)
- [ ] Eigene Domain www.rate-my-throne.com (All-Inkl Privat Plus, DNS auf GitHub Pages gestellt am 30.10.2026); in GitHub eintragen, HTTPS erzwingen, Supabase-URLs anpassen
- [ ] E-Mail-Versand über Brevo (Absender noreply@rate-my-throne.com), SPF um Brevo ergänzen, Brevo und All-Inkl in Datenschutzerklärung aufnehmen

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
- Benutzernamen ändern
- Eingetragene Toiletten löschen: eigene, solange niemand anderes sie bewertet hat; Admin alle (Bewertungen werden mitgelöscht)

## Nächste Schritte
1. Eigener E-Mail-Versand (für Bestätigungsmails, Passwort vergessen)
2. Werbung (z. B. Google AdSense) – erst mit eigener Domain und Rechtstexten, dann Cookie-Einwilligung nötig

## Toiletten-Daten (seit 29.10.2026)
- OSM-Toiletten liegen in unserer Datenbank (Tabelle osm_toilets), die App fragt Overpass nicht mehr direkt
- Import läuft in der Datenbank selbst (pg_net + pg_cron, alle 20 Sekunden, Kacheln von 1°), Skript: supabase/migrations/20261029_osm_import_in_db.sql
- Deutschland ist vorgemerkt; neue Gegenden weltweit fordert die App beim ersten Besuch an (Funktion request_osm_tiles)
- Ist Overpass überlastet, wird die Kachel nach 10 Minuten erneut versucht; Aktualisierung jeder Kachel nach 7 Tagen
- Die Edge Function osm-sync wird nicht mehr benutzt (Overpass lehnt ihre Anfragen mit HTTP 406 ab) und kann im Supabase-Dashboard gelöscht werden
