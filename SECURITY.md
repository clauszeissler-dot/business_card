# Sicherheit

## Security Contract (Dev Security AffAIrs, Modus `develop`)

```text
SECURITY CONTRACT
Scope: scripts/extract_ci.py, scripts/parse_profile.py, scripts/make_card.py,
       scripts/common.py; keine Server-, Konto- oder Cloud-Komponenten.
Stack: Python 3.11+ (Standardbibliothek), segno 1.6.6 (QR), optional rsvg-convert
       und pdftotext als lokale Programme.
Daten: Profildaten der nutzenden Person (Name, Headline, ggf. E-Mail/Telefon).
       Bleiben lokal im Ausgabeordner; keine Übertragung an Dritte.
Trust Boundaries:
  1. Website-URL der Nutzerin/des Nutzers -> HTTP-Abruf (SSRF-Risiko)
  2. Fremdes HTML/CSS/Logo der Website -> Parser und SVG-Ausgabe
  3. Profil-Eingaben (CSV, PDF-Text, JSON) -> SVG/HTML-Ausgabe (Injection)
  4. Pfade aus JSON (Foto, Logo, Sticker) -> Dateizugriff
  5. Signaturgeheimnisse (Apple-.p12, Google-Dienstkonto) -> wallet.py
Invarianten:
  - Kein Abruf von Loopback, privaten, Link-Local-, Multicast- oder
    reservierten Adressen, auch nicht über Weiterleitungen oder DNS-Wechsel.
  - Nur http/https; Größen- und Zeitlimit je Antwort.
  - Fremder Text landet ausschließlich XML-escaped in SVG/HTML.
  - Fremde Bilder werden nur als <image> mit data:-URI eingebunden, nie inline
    als SVG-Markup; nur PNG/JPEG/WebP/SVG/GIF mit Größenlimit.
  - LinkedIn-URL im QR-Code ist eine validierte https://www.linkedin.com/in/<slug>-Adresse.
  - Signaturgeheimnisse nur aus Dateien/Umgebungsvariablen, nie als CLI-Wert, nie in Ausgaben,
    nie im Chat einer KI-App; die Skill-Anleitung lehnt Schlüssel im Chat ab.
  - vCard/ICS: Zeilenumbrüche und Trennzeichen in Werten werden maskiert (keine Feld-Injection).
Gate: S1 (URL-Abruf, externe Inputs)
Nachweise: tests/test_security.py (Missbrauch), tests/test_extract_ci.py (Kontrolle)
```

## Kontrollen

| Risiko | Kontrolle | Test |
| --- | --- | --- |
| SSRF auf interne Dienste | DNS-Auflösung, jede Adresse geprüft, Verbindung direkt zur geprüften IP (kein zweiter DNS-Lookup), Weiterleitungen einzeln geprüft, max. 5 | `test_security.py` |
| Ressourcenverbrauch | Timeout 10 s, max. 2 MB HTML/CSS, 1 MB Logo, max. 6 Stylesheets | `test_security.py` |
| Markup-Injection | `xml.sax.saxutils.escape` für alle Texte; Attribute gequotet | `test_security.py` |
| Aktive Inhalte in Logos | Logo nur als `<image href="data:...">`; Browser führen darin keine Skripte aus | `test_security.py` |
| Fälschung von Wallet-Pässen | PKCS#7-Signatur (detached) über manifest.json; Manipulation bricht die Prüfung | `test_wallet.py` (OpenSSL-Verify inkl. Manipulation) |
| vCard-Feld-Injection | Maskierung von CR/LF, `;`, `,` | `test_extras.py` |
| Falsche QR-Ziele | URL-Validierung mit Regex auf LinkedIn-Profilpfad | `test_parse_profile.py`, `test_make_card.py` |

## Restgrenzen

- Kein Pentest, keine Garantie. Geprüft ist der oben genannte Umfang.
- Die Farb- und Schriftauswertung ist heuristisch; Ergebnisse vor dem Druck prüfen.

## Meldungen

Sicherheitsprobleme bitte als vertrauliche Meldung über die Repository-Plattform melden, nicht als öffentliches Issue.

## Online-Dienst (`service/`, Vercel) – Threat Model

| Bedrohung | Gegenmaßnahme | Test |
| --- | --- | --- |
| Fremder erzeugt einen von KI AffAIrs signierten Pass unter fremdem Namen | Name und E-Mail kommen nur aus der LinkedIn-Anmeldung; Formularfelder `name`/`email` werden ignoriert | `test_service.py::test_card_input_requires_session_and_ignores_foreign_name` |
| Login-CSRF / OAuth-State-Fälschung | zufälliger State, verschlüsselt im Cookie (AES-GCM), 10 Min. gültig, zeitkonstanter Vergleich | `test_callback_rejects_wrong_state` |
| Cross-Site-POST mit Sitzungscookie | `SameSite=Lax` plus Origin-Prüfung gegen `PUBLIC_BASE_URL` | `test_http_post_from_foreign_origin_is_rejected` |
| Sitzungsdiebstahl/-fälschung | Cookie `HttpOnly; Secure`, AES-GCM mit Schlüssel aus `SESSION_SECRET`, 1 h Laufzeit | `test_seal_roundtrip_and_tamper`, `test_other_secret_cannot_read_session` |
| Ungewolltes Posten | Posten nur mit ausdrücklicher Bestätigung (`confirm: true`) und Text | `test_share_needs_confirmation_and_text` |
| Ressourcenverbrauch | Body max. 64 KB, Funktionslaufzeit max. 15 s | `test_http_oversized_body` |
| Informationsabfluss in Fehlern | generische Fehlermeldungen, keine Personendaten in Logs | `test_http_internal_errors_do_not_leak` |
| Clickjacking/XSS | CSP ohne Inline-Skripte, `frame-ancestors 'none'`, nosniff | `vercel.json` |

Restgrenzen: Kein serverseitiges Rate-Limit (zustandslos) – Vercel-Firewall-Regel für `/api/*` einrichten. Missbrauch der Apple-Signatur bleibt an ein echtes LinkedIn-Konto gebunden, aber nicht an eine geprüfte Identität (LinkedIn-OIDC prüft keine Identität).
