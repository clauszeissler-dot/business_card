# Entscheidungen und Ergebnisse

Anforderungen: [AENDERUNGEN.md](AENDERUNGEN.md) · Umsetzung: [PLAN.md](PLAN.md) · Nachweise: [ARBEITSLOGBUCH.md](ARBEITSLOGBUCH.md)

E-NNN gehört zu A-NNN. Änderungen als datierter Nachtrag.

<!-- Einträge ab hier, aufsteigend nach Nummer. -->

## E-001 – Recherche LinkedIn Business Card
- Problem: Funktionsumfang der neuen LinkedIn-Karte unklar, viele Drittquellen.
- Lösung: Faktenseite references/linkedin-native-card.md, getrennt nach offiziell/Dritte, mit Stand 20.11.2026.
- Verworfen: Aussagen aus Marketing-Seiten (ConnectMachine) als Fakten übernehmen.
- Entscheidung: Claude, 2026-11-20, Auftrag Claus.
- Live seit: noch nicht live (lokaler Commit)
- Beleg: AENDERUNGEN A-001
- Offen: Faktenstand bei Rollout-Änderungen nachziehen.

## E-002 – Formen
- Problem: Karten sollen in verschiedenen Formen gestaltbar sein.
- Lösung: 6 Layouts, Ecken sharp/soft/round (Druck: Eckenabrundung als Hinweis), Foto/Monogramm circle/rounded/square/hexagon.
- Verworfen: echte Stanzformen in der Druckdatei (Druckereien wollen Rechteck + Beschnitt).
- Entscheidung: Claude, 2026-11-20.
- Live seit: noch nicht live
- Beleg: test_make_card.py
- Offen: –

## E-003 – Farben
- Problem: CI-Farben müssen lesbar bleiben.
- Lösung: Palette nur über Helligkeit anpassen (Farbton bleibt), Text ≥7:1 bzw. ≥4,5:1 auf Markenfläche, QR immer dunkel auf weiß.
- Verworfen: feste Weiß/Schwarz-Schrift ohne Prüfung.
- Entscheidung: Claude, 2026-11-20.
- Live seit: noch nicht live
- Beleg: test_colors.py
- Offen: –

## E-004 – Muster
- Problem: Muster dürfen Text nicht schwächen.
- Lösung: 8 SVG-Muster, Ton in Ton; auf mittelhellen Flächen mit weißer Schrift automatisch dunkler; Kontrast gegen Mustergrund geprüft.
- Verworfen: Bildtexturen (Druckqualität, Dateigröße).
- Entscheidung: Claude, 2026-11-20.
- Live seit: noch nicht live
- Beleg: test_make_card.py
- Offen: –

## E-005 – LinkedIn-Profil auslesen
- Problem: Profildaten automatisch übernehmen, ohne Nutzungsbedingungen zu verletzen.
- Lösung: parse_profile.py für Datenexport, Profil-PDF und Text; kein Scraping; Adresse/Geburtsdatum nie, Telefon nur auf Wunsch.
- Verworfen: Scraping von linkedin.com (ToS, Firecrawl blockiert), Auslesen über eingeloggten Browser.
- Entscheidung: Claude, 2026-11-20.
- Live seit: noch nicht live
- Beleg: test_parse_profile.py
- Offen: PDF-Heuristik an echtem LinkedIn-PDF prüfen.

## E-006 – Website-CI auslesen
- Problem: Farben, Schriften, Logo, Rundungen einer Website ermitteln.
- Lösung: extract_ci.py (stdlib, SSRF-geschützt, IP-Pinning) plus Firecrawl-Branding-Import; Ranking gegen Hover-/Tint-Farben.
- Verworfen: nur Firecrawl (nicht für alle Nutzer verfügbar, Logo teils falsch).
- Entscheidung: Claude, 2026-11-20.
- Live seit: noch nicht live
- Beleg: test_extract_ci.py, Realtests 20.11.2026
- Offen: JS-only-Seiten und Bot-Schutz → manueller Weg über Ego Lite.

## E-007 – Business Card im CI erstellen
- Problem: Druckfähige und digitale Karte mit QR-Code.
- Lösung: make_card.py: SVG-Master, PNG 300 dpi und 2-seitiges PDF über rsvg-convert, preview.html, report.json, Galerie.
- Verworfen: Wallet-Pässe (Zertifikat/Issuer nötig).
- Entscheidung: Claude, 2026-11-20.
- Live seit: noch nicht live
- Beleg: QR-Decode-Tests, evals/run_offline.py
- Offen: –

## E-008 – Als Skill nutzbar
- Problem: Agenten sollen den Ablauf zuverlässig ausführen.
- Lösung: SKILL.md mit 6-Schritt-Ablauf, Referenzen, evals.json (5 Fälle inkl. Grenzfälle), Symlink nach ~/.claude/skills.
- Verworfen: –
- Entscheidung: Claude, 2026-11-20.
- Live seit: lokal eingebunden 2026-11-20
- Beleg: evals/run_offline.py 13/13
- Offen: LLM-Eval der Prompts.

## E-009 – Repo zum Teilen
- Problem: Öffentliches Repo, über LinkedIn teilbar.
- Lösung: README DE (Hauptsprache) + EN, Anleitungen, Banner, Hero-Bild, MIT, Drittlizenzen, CRA-Doku, Disclaimer „nicht mit LinkedIn verbunden“.
- Verworfen: LinkedIn-Logo in Bildern.
- Entscheidung: Claude, 2026-11-20.
- Live seit: noch nicht live (Push wartet auf Auftrag)
- Beleg: lokaler Commit
- Offen: Ziel (GitHub vs. Forgejo), Push, Social Preview, Repo-Beschreibung/Topics.

### Nachtrag E-009 – 2026-11-20
- Markenrichtlinien (brand.linkedin.com/policies, /business-books-and-media-usage) gelesen: Marke nur beschreibend, mit ®, kein Logo, kein Anschein von Sponsoring; Domains/Handles mit „LinkedIn“ verboten, Repo-Namen nicht geregelt.
- Umgesetzt: offizieller Attributionshinweis in README DE/EN und App-Anleitung.
- Offen (Entscheidung Claus): Repo-Name ohne führendes „linkedin“, Vorschlag `business-card-skill`.

### Nachtrag E-009 – 2026-11-20 (Veröffentlichung)
- Entscheidung Claus 2026-11-20: Ziel-Repo https://github.com/clauszeissler-dot/business_card (öffentlich).
- Skill-Name auf `business-card` geändert (Markenrichtlinien: „LinkedIn“ nur beschreibend); Symlink `~/.claude/skills/business-card`.
- Vorhandenes Initial-README des Repos durch das vollständige README ersetzt (Merge der Historien).

## E-010 – Sperrbildschirm mit Gültigkeit
- Problem: Karte schnell auf dem Handy zeigen, zeitlich begrenzt (z. B. Messe).
- Lösung: extras.py rendert Hochformat-Bilder (iPhone, iPhone Max, Android) mit freier Uhr- und Tastenzone, großem QR, „Gültig bis“ + Event; Kalender-Erinnerung (.ics) und Kurzbefehl-Hinweis zum Zurückstellen.
- Verworfen: „automatisch ablaufendes“ Bild – technisch nicht möglich ohne App.
- Entscheidung: Claus 2026-11-20 (Wunsch), Umsetzung Claude.
- Live seit: noch nicht live
- Beleg: test_extras.py
- Offen: –

## E-011 – vCard
- Problem: Kontakt mit einem Tipp speichern.
- Lösung: vCard 3.0 mit Foto, Feldmaskierung und Zeilenfaltung.
- Verworfen: vCard 4.0 (schlechtere Unterstützung auf iOS/Android-Adressbüchern).
- Entscheidung: Claude, 2026-11-20.
- Live seit: noch nicht live
- Beleg: test_extras.py
- Offen: –

## E-012 – Sticker/Begegnungsfotos
- Problem: LinkedIn erlaubt Sticker auf der Rückseite; gewünscht als Funktion.
- Lösung: Rückseite `--back stickers` mit bis zu 3 Polaroid-Fotos und Bildunterschrift, QR bleibt.
- Verworfen: Emoji-Sticker (Icon-Standard), Hintergrund-Freistellung (schwere Abhängigkeit).
- Entscheidung: Claude, 2026-11-20.
- Live seit: noch nicht live
- Beleg: test_make_card.py
- Offen: –

## E-013 – Wallet-Pässe
- Problem: Karte in Apple/Google Wallet.
- Lösung: wallet.py: Apple .pkpass (generic, PKCS#7 detached SHA-256, WWDR) und Google Generic Pass als signierter Save-Link; Ablauf in Tagen. Geheimnisse nur aus Dateien/Umgebungsvariablen.
- Verworfen: Signatur in der KI-App-Sandbox (Geheimnisse würden in fremde Cloud gelangen); Drittanbieter-Passdienste (Datenschutz).
- Entscheidung: Claus 2026-11-20 (Apple-Dev vorhanden, Google gewünscht), Umsetzung Claude.
- Live seit: noch nicht live
- Beleg: test_wallet.py
- Offen: Echttest mit Claus' Pass-Type-Zertifikat und Google-Issuer-Konto; öffentlicher Dienst (A-016).

## E-014 – Nutzung in Claude-App und ChatGPT
- Problem: Sandbox ohne rsvg/fc-list, oft ohne freien Webzugriff.
- Lösung: PNG über resvg-py mit eingebetteten OFL-Schriften, PDF-Raster-Fallback, App-Abschnitt in SKILL.md (CI über eigenes Web-Werkzeug), ZIP-Builder + GitHub-Release.
- Verworfen: cairosvg (Systembibliothek nötig).
- Entscheidung: Claus 2026-11-20 (Claude-App, ChatGPT), Umsetzung Claude.
- Live seit: noch nicht live
- Beleg: test_render.py, test_build_zip.py
- Offen: Test in beiden Apps durch Claus.

## E-015 – LinkedIn-Anmeldung und Teilen
- Problem: Profildaten offiziell übernehmen und Karte posten – für alle Skill-Nutzer.
- Lösung: OpenID Connect (openid, profile, email) und Share on LinkedIn (w_member_social) im Dienst; Bildupload über /v2/assets + /v2/ugcPosts; Posten nur nach ausdrücklicher Bestätigung.
- Verworfen: Anmeldung im Skill selbst (Client-Secret im Chat), Profil-/Headline-Abruf (nicht in Self-Serve-Produkten).
- Entscheidung: Claus 2026-11-20 (öffentlich für alle), Umsetzung Claude.
- Live seit: noch nicht live
- Beleg: test_service.py
- Offen: Echttest nach Einrichtung der LinkedIn-Produkte.

## E-016 – Öffentlicher Dienst auf Vercel
- Problem: Wallet-Signatur und LinkedIn-Login brauchen Server-Geheimnisse; Nutzung aus Claude-/ChatGPT-App.
- Lösung: Zustandsloser Python-Dienst (`api/index.py`, `service/`), Sitzung AES-GCM im Cookie, Origin-Prüfung, CSP, Name nur aus LinkedIn; Geheimnisse nur als Vercel-Umgebungsvariablen, Übertragung per `tools/push_vercel_env.py` ohne Ausgabe; Datenschutzhinweise als Entwurf, Impressum verlinkt.
- Verworfen: Netlify (keine Python-Funktionen), Datenbank/Speicherung (Datenschutz), Hetzner (mehr Betrieb).
- Entscheidung: Claus 2026-11-20 („selbstständig über Vercel oder Netlify“, öffentlich), Umsetzung Claude.
- Live seit: noch nicht live
- Beleg: test_service.py
- Offen: Vercel-Login/Projekt, Secrets, Redirect-URL bei LinkedIn, Rate-Limit-Regel, Prüfung Vercel-Tarif (Hobby schließt gewerbliche Nutzung aus), rechtliche Prüfung der Datenschutzhinweise.

### Nachtrag E-015 – 2026-11-25 (LinkedIn-App eingerichtet)
- Problem: Bestehende App „KI Affairs“ hat die Community Management API; diese muss laut LinkedIn das einzige Produkt einer App sein, OIDC/Share dort nicht anforderbar.
- Lösung: Neue App „Business Card by KI AffAIrs“ (ID 265146809, Client ID 7721qg9o4leqg2) an Unternehmensseite KI AffAIrs; Produkte „Sign In with LinkedIn using OpenID Connect“ und „Share on LinkedIn“ hinzugefügt; Scopes openid, profile, email, w_member_social; Redirect https://business-card-wallet.vercel.app/api/callback; Datenschutz-URL /datenschutz.html.
- Sicherheit: Erstes Client Secret war im Sitzungsprotokoll sichtbar → rotiert, altes entfernt; neues Secret nur in ~/Desktop/business-card-secrets/secrets.env (0600), nie ausgegeben.
- Entscheidung: Claude im Auftrag Claus (Chat 25.11.2026: „LinkedIn selbst machen“), Ego Lite.
- Offen: Echttest Login/Share nach Deploy.

## E-017 – Datenschutzhinweise des Dienstes
- Problem: Alte Hinweise (20.11.) knapp, ohne Verantwortlichen, Cookies, Scopes, Profilfoto-CDN und Widerrufsweg.
- Lösung: public/datenschutz.html neu: Verantwortlicher und Aufsicht (LDI NRW) aus affairs-consulting.de/datenschutz (gelesen 25.11.2026 in Ego Lite), Datenflüsse je Schritt (Aufruf, LinkedIn-Login, Formular, Apple, Google, Teilen), Cookies bc_state 10 Min. / bc_session 1 Std. nach § 25 Abs. 2 Nr. 2 TDDDG, Vercel als Auftragsverarbeiter (DPF-zertifiziert), Serverfunktion in den USA (Standardregion iad1), LinkedIn/Google eigene Verantwortung, Widerruf über „Berechtigte Dienste“. Anrede „du“ wie die App. Linkfarbe in style.css auf Akzentfarbe (Kontrast).
- Verworfen: Verweis nur auf die Haupt-DSE (deckt Vercel und LinkedIn-Login nicht ab); Angabe „Server in Frankfurt“ (stimmt ohne regions-Einstellung nicht).
- Entscheidung: Claude im Auftrag Claus, 2026-11-25.
- Live seit: noch nicht live (Deploy offen)
- Beleg: tests/test_datenschutz.py
- Offen: Vercel-DPA gilt laut Drittquelle nur für Pro/Enterprise → Tarif klären; optional Region fra1; Impressum-E-Mail (kiaffairs-podcast.de) weicht von DSE-E-Mail ab; keine Rechtsberatung, Prüfung durch Claus.

### Nachtrag E-017 – 2026-11-25 (Region)
- Entscheidung Claus (Chat 25.11.2026): Serverfunktion in Frankfurt. vercel.json `regions: ["fra1"]`, Datenschutztext angepasst (Zugriff aus den USA nicht ausgeschlossen). Test test_serverfunktion_in_frankfurt_und_so_beschrieben rot → grün, 233 Tests grün.
