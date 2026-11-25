# Anforderungen und Änderungswünsche

Zweck: [ZIEL.md](ZIEL.md) · Lösungen: [ENTSCHEIDUNGEN.md](ENTSCHEIDUNGEN.md) · Umsetzung: [PLAN.md](PLAN.md) · Nachweise: [ARBEITSLOGBUCH.md](ARBEITSLOGBUCH.md)

| ID | Eingang / Quelle | Anforderung | Abnahmekriterium | Status | Planschritt | Prüfbeleg / Grund |
| --- | --- | --- | --- | --- | --- | --- |
| A-001 | 2026-11-20 Claus, Chat | Möglichkeiten der LinkedIn Business Card recherchieren | Faktenseite mit Quellen, Stand, offiziell vs. Dritte | geprüft | S1 | references/linkedin-native-card.md; offizielle Hilfe a16648713 + Newsroom 15.10.2026 |
| A-002 | 2026-11-20 Claus, Chat | Formen (Layouts, Ecken, Fotoform) | ≥5 Layouts, 3 Eckenstile, 4 Fotoformen rendern fehlerfrei | geprüft | S3 | 6 Layouts, 3 Ecken, 4 Fotoformen; test_make_card.py (Katalog, Foto-Clip), Sichtprüfung Kontaktbögen |
| A-003 | 2026-11-20 Claus, Chat | Farben (CI-Palette, Kontrast) | Text ≥4,5:1 in allen Kombinationen, QR dunkel auf hell | geprüft | S3 | test_colors.py 27 Kombinationen; min_text_contrast im Bericht |
| A-004 | 2026-11-20 Claus, Chat | Muster | ≥7 Muster rendern, Text bleibt lesbar | geprüft | S3 | 8 Muster × 6 Layouts in test_make_card.py; Ton-in-Ton-Regel |
| A-005 | 2026-11-20 Claus, Chat | LinkedIn-Profil auslesen | Export-CSV, Profil-PDF, Text → profile.json; ungültige URL abgelehnt | geprüft | S4 | test_parse_profile.py (Export, PDF-Text, Text, URL-Validierung) |
| A-006 | 2026-11-20 Claus, Chat | Website-CI auslesen | Farben, Schriften, Logo aus Fixture; SSRF-Fälle abgelehnt | geprüft | S5 | test_extract_ci.py inkl. SSRF-Missbrauch; Realtest sparkasse.de, stripe.com, bosch.de, dm.de |
| A-007 | 2026-11-20 Claus, Chat | Business Card im CI-Stil erstellen | SVG/PNG/PDF vorne+hinten, QR dekodiert zur Profil-URL | geprüft | S3 | QR-Decode je Layout (OpenCV) = Profil-URL; PDF/PNG erzeugt; evals/run_offline.py 13/13 |
| A-008 | 2026-11-20 Claus, Chat | Als Skill nutzbar | SKILL.md, Evals, Einbindung unter ~/.claude/skills | umgesetzt | S6 | SKILL.md, evals.json, Symlink ~/.claude/skills; Agenten-Eval (LLM) noch nicht gelaufen |
| A-009 | 2026-11-20 Claus, Chat | Repo zum Teilen über LinkedIn, „möglichst perfekt“ | README DE+EN, Banner, Lizenz, Beispielbilder, CRA-Doku, lokaler Commit | umgesetzt | S7 | Live: github.com/clauszeissler-dot/business_card (main 70e333b), frischer Klon 182 Tests grün; Social Preview offen (nur Web-Oberfläche) |
| A-010 | 2026-11-20 Claus, Chat | Sperrbildschirm-Bild mit Gültigkeit in Tagen | PNG iPhone/Android, „gültig bis“, Erinnerung (.ics) und Kurzbefehl-Anleitung | geprüft | S8 | test_extras.py (Uhr-/Tastenzone, Datum, EN), QR-Decode am PNG, ICS; Sichtprüfung iPhone/Android |
| A-011 | 2026-11-20 Claus, Chat | vCard | .vcf 3.0 mit Foto/Kontakt, optional QR mit vCard | geprüft | S8 | test_extras.py (Felder, Faltung, Foto, Injection) |
| A-012 | 2026-11-20 Claus, Chat | Sticker/Begegnungsfotos auf der Rückseite (wie LinkedIn) | Rückseite „stickers“ mit bis zu 3 Fotos + Bildunterschrift | geprüft | S8 | test_make_card.py (1–5 Sticker, Fallback, QR-Decode); Sichtprüfung |
| A-013 | 2026-11-20 Claus, Chat | Apple- und Google-Wallet-Pässe mit Ablauf in Tagen | pass.json/.pkpass (signiert, Testzertifikat) und Google-Save-Link (JWT, Testschlüssel) | umgesetzt | S9 | test_wallet.py; 25.11.: echtes Apple-Zertifikat (pass.de.affairs-consulting.card, bis 25.12.2027), Test-Pass über service.core signiert, OpenSSL-Verify ok; Google-Issuer und Test auf iPhone offen |
| A-014 | 2026-11-20 Claus, Chat | Nutzung in Claude-App und ChatGPT | Rendering ohne Systemprogramme (resvg + eingebettete Schriften), App-Weg für CI, ZIP zum Hochladen | umgesetzt | S10 | render.py (resvg + Schriften), App-Abschnitt SKILL.md, ZIP + test_build_zip.py; Test in Claude-/ChatGPT-App offen |
| A-015 | 2026-11-20 Claus, Chat | LinkedIn-Developer-App: Anmeldung für alle Nutzer, Karte posten | OIDC-Login (Name, Foto, E-Mail) und Share im öffentlichen Dienst | umgesetzt | S11 | service/core.py OIDC + Share; test_service.py; 25.11.: eigene App „Business Card by KI AffAIrs“ (ID 265146809), Produkte OIDC + Share aktiv, Redirect gesetzt, Secrets in secrets.env; Echttest nach Deploy offen |
| A-016 | 2026-11-20 Claus, Chat | Öffentlicher Dienst auf Vercel/Netlify für Wallet-Signatur und LinkedIn | Deploy auf *.vercel.app, Geheimnisse nur in Vercel, DSGVO-Seiten, Missbrauchsschutz | in Arbeit | S11 | Code + 22 Sicherheitstests grün; Vercel-MCP 403 beim Anlegen → CLI-Login durch Claus nötig; Secrets-Ordner ~/Desktop/business-card-secrets vorbereitet |
| A-017 | 2026-11-25 Claus, Chat | Eigene Datenschutzhinweise für den Dienst, abgestimmt auf DSE von KI AffAIrs, Vercel und LinkedIn | Seite nennt Verantwortlichen, Cookies/Laufzeiten/Scopes passend zum Code, Empfänger, Widerruf, Aufsicht | geprüft | S11 | tests/test_datenschutz.py (4 Tests, erst rot, dann grün); 232 Tests grün; Sichtprüfung Ego Lite |

## Statusregeln

offen → in Arbeit → umgesetzt → geprüft (nur mit Beleg und E-NNN).

## Letzter Abschlussabgleich

- Stand: 2026-11-20 (Sitzungsende)
- Abgeglichene IDs: A-001 bis A-016
- Geprüft erfüllt: A-001 bis A-007, A-010 bis A-012
- Nicht erfüllt: A-008 (LLM-Eval offen), A-009 (Social Preview manuell), A-013 (Echttest mit echtem Apple-Zertifikat/Google-Issuer), A-014 (Test in Claude-/ChatGPT-App), A-015 (LinkedIn-Produkte + Secrets fehlen), A-016 (Deploy durch Claus ausstehend, Secrets unvollständig)
- Neue Wünsche seit dem letzten Abgleich vollständig erfasst: ja
