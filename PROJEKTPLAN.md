# Rate My Throne – Projektplan

Stand: 29.10.2026 · Version 0.2

## Stand
- Web-App (PWA geplant), Start in Berlin
- Karte mit öffentlichen Toiletten aus OpenStreetMap
- Echte Konten über Supabase (Projekt "Rate My Throne", Region eu-west-1 / Irland): Registrierung mit E-Mail, Benutzername, Passwort; Anmeldung mit E-Mail + Passwort
- Bewertungen (Sauberkeit, Ausstattung, Erreichbarkeit; kostenlos/barrierefrei/Wickeltisch; Kommentar) werden in der Datenbank gespeichert und sind für alle sichtbar
- Eigene Toiletten hinzufügen (nur in unserer Datenbank)
- Datenbank-Regeln: Lesen für alle, Schreiben nur eigene Einträge

## Ausprobieren
index.html herunterladen und per Doppelklick im Browser öffnen.

## Nächste Schritte
1. Online stellen (Netlify oder Cloudflare Pages) und in Supabase die "Site URL" auf die echte Adresse setzen
2. Code auf GitHub ablegen (Versionsverwaltung)
3. PWA: App-Symbol, auf Startbildschirm installierbar
4. Eigener E-Mail-Versand für Bestätigungsmails (Supabase-Standardversand ist stark begrenzt)
5. Moderation: Kommentare melden/löschen
6. Konto löschen, Passwort vergessen
7. Rechtliches: Impressum, Datenschutzerklärung, Cookie-Einwilligung (wegen Werbung)
8. Werbung (z. B. Google AdSense) – erst mit eigener Domain
