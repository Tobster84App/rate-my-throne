# Erzeugt die Mail-Vorlagen für Supabase (Authentication → Emails → Templates).
# Jede Vorlage enthält Deutsch und Englisch; angezeigt wird die Sprache, die bei der Registrierung gespeichert wurde (user_metadata.lang).
# Aufruf: python3 build.py
BTN = '''<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 20px;"><tr><td style="border-radius:12px;background:#e3b341;">
<a href="{{ .ConfirmationURL }}" style="display:inline-block;padding:14px 26px;font-size:16px;font-weight:bold;color:#2a1f4d;text-decoration:none;border-radius:12px;">%s</a>
</td></tr></table>'''
CODE = '''<p style="margin:0 0 8px;font-size:14px;color:#6b6480;">%s</p>
<p style="margin:0 0 8px;font-size:30px;font-weight:bold;letter-spacing:6px;color:#2a1f4d;">{{ .Token }}</p>'''
LINK = '''<p style="margin:16px 0 0;font-size:12px;line-height:1.5;color:#6b6480;word-break:break-all;">%s<br><a href="{{ .ConfirmationURL }}" style="color:#6b6480;">{{ .ConfirmationURL }}</a></p>'''

def block(t, link):
    out = f'''<h1 style="margin:0 0 12px;font-size:24px;line-height:1.25;color:#2a1f4d;">{t["title"]}</h1>
<p style="margin:0 0 24px;font-size:16px;line-height:1.5;color:#1f1a2e;">{t["text"]}</p>'''
    if "btn" in t: out += "\n" + BTN % t["btn"]
    if "code" in t: out += "\n" + CODE % t["code"]
    out += f'\n<p style="margin:24px 0 0;font-size:13px;line-height:1.5;color:#6b6480;">{t["hint"]}</p>'
    if "btn" in t: out += "\n" + LINK % link
    return out

def page(de, en):
    return f'''<!doctype html>
<html>
<body style="margin:0;padding:0;background:#f5f3fa;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f5f3fa;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:520px;background:#ffffff;border-radius:16px;overflow:hidden;">
<tr><td style="background:#2a1f4d;padding:18px 24px;">
<img src="https://www.rate-my-throne.com/icons/icon-192.png" width="36" height="36" alt="" style="vertical-align:middle;border:0;">
<span style="vertical-align:middle;margin-left:8px;font-size:20px;font-weight:bold;color:#ffffff;">Rate My <span style="color:#e3b341;">Throne</span></span>
</td></tr>
<tr><td style="padding:28px 24px;">
{{{{ if and .Data.lang (eq .Data.lang "en") }}}}
{block(en, "If the button doesn't work, open this link:")}
{{{{ else }}}}
{block(de, "Falls der Knopf nicht funktioniert, öffne diesen Link:")}
{{{{ end }}}}
</td></tr>
<tr><td style="padding:16px 24px;border-top:1px solid #e3dfee;font-size:12px;color:#6b6480;">
Rate My Throne · <a href="https://www.rate-my-throne.com/impressum.html" style="color:#6b6480;">Impressum / Legal notice</a>
</td></tr>
</table>
</td></tr></table>
</body>
</html>
'''

T = {
 "confirm-signup": (
  dict(title="Bestätige deine E-Mail-Adresse", text="Fast geschafft! Tippe auf den Knopf, um dein Konto bei Rate My Throne zu aktivieren.",
       btn="E-Mail bestätigen", hint="Du hast dich nicht registriert? Dann ignoriere diese E-Mail einfach."),
  dict(title="Confirm your email address", text="Almost there! Tap the button to activate your Rate My Throne account.",
       btn="Confirm email", hint="Didn't sign up? Just ignore this email.")),
 "invite-user": (
  dict(title="Du bist eingeladen", text="Du wurdest zu Rate My Throne eingeladen – der App, mit der du öffentliche Toiletten findest und bewertest. Tippe auf den Knopf, um dein Konto anzulegen.",
       btn="Einladung annehmen", hint="Du kennst uns nicht? Dann ignoriere diese E-Mail einfach."),
  dict(title="You're invited", text="You've been invited to Rate My Throne – the app for finding and rating public toilets. Tap the button to create your account.",
       btn="Accept invitation", hint="Don't know us? Just ignore this email.")),
 "magic-link": (
  dict(title="Dein Anmeldelink", text="Tippe auf den Knopf, um dich bei Rate My Throne anzumelden. Der Link gilt nur kurze Zeit und nur einmal.",
       btn="Anmelden", code="Oder gib diesen Code ein:", hint="Du wolltest dich nicht anmelden? Dann ignoriere diese E-Mail. Ohne den Link kommt niemand in dein Konto."),
  dict(title="Your sign-in link", text="Tap the button to sign in to Rate My Throne. The link is valid only for a short time and only once.",
       btn="Sign in", code="Or enter this code:", hint="Didn't try to sign in? Just ignore this email. Nobody can access your account without the link.")),
 "change-email": (
  dict(title="Neue E-Mail-Adresse bestätigen", text="Du möchtest die E-Mail-Adresse deines Kontos bei Rate My Throne ändern. Tippe auf den Knopf, um die neue Adresse zu bestätigen.",
       btn="Neue Adresse bestätigen", hint="Du hast das nicht veranlasst? Dann ignoriere diese E-Mail und ändere zur Sicherheit dein Passwort."),
  dict(title="Confirm your new email address", text="You want to change the email address of your Rate My Throne account. Tap the button to confirm the new address.",
       btn="Confirm new address", hint="Didn't request this? Ignore this email and change your password to be safe.")),
 "reset-password": (
  dict(title="Neues Passwort festlegen", text="Tippe auf den Knopf, um ein neues Passwort für dein Konto bei Rate My Throne festzulegen.",
       btn="Neues Passwort festlegen", hint="Du hast das nicht angefordert? Dann ignoriere diese E-Mail. Dein Passwort bleibt unverändert."),
  dict(title="Set a new password", text="Tap the button to set a new password for your Rate My Throne account.",
       btn="Set new password", hint="Didn't request this? Just ignore this email. Your password stays the same.")),
 "reauthentication": (
  dict(title="Bestätige, dass du es bist", text="Für eine wichtige Änderung an deinem Konto bei Rate My Throne brauchen wir eine kurze Bestätigung.",
       code="Dein Bestätigungscode:", hint="Du hast nichts geändert? Dann ignoriere diese E-Mail und ändere zur Sicherheit dein Passwort."),
  dict(title="Confirm it's you", text="We need a quick confirmation for an important change to your Rate My Throne account.",
       code="Your confirmation code:", hint="Didn't change anything? Ignore this email and change your password to be safe.")),
}
# Links zeigen auf unsere Karte statt direkt auf Supabase: Der Einmal-Code wird dort erst nach einem Klick eingelöst
# (Mail-Virenscanner öffnen Links automatisch und würden ihn sonst verbrauchen).
TYPES = {"confirm-signup": "email", "invite-user": "invite", "magic-link": "magiclink", "change-email": "email_change", "reset-password": "recovery"}
for name, (de, en) in T.items():
    html = page(de, en)
    if name in TYPES:
        html = html.replace("{{ .ConfirmationURL }}", "https://www.rate-my-throne.com/karte.html?token_hash={{ .TokenHash }}&amp;type=" + TYPES[name])
    open(name + ".html", "w", encoding="utf-8").write(html)
    print(name + ".html")
