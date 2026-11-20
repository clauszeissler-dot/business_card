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
  4. Pfade aus JSON (Foto, Logo) -> Dateizugriff
Invarianten:
  - Kein Abruf von Loopback, privaten, Link-Local-, Multicast- oder
    reservierten Adressen, auch nicht über Weiterleitungen oder DNS-Wechsel.
  - Nur http/https; Größen- und Zeitlimit je Antwort.
  - Fremder Text landet ausschließlich XML-escaped in SVG/HTML.
  - Fremde Bilder werden nur als <image> mit data:-URI eingebunden, nie inline
    als SVG-Markup; nur PNG/JPEG/WebP/SVG/GIF mit Größenlimit.
  - LinkedIn-URL im QR-Code ist eine validierte https://www.linkedin.com/in/<slug>-Adresse.
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
| Falsche QR-Ziele | URL-Validierung mit Regex auf LinkedIn-Profilpfad | `test_parse_profile.py`, `test_make_card.py` |

## Restgrenzen

- Kein Pentest, keine Garantie. Geprüft ist der oben genannte Umfang.
- Die Farb- und Schriftauswertung ist heuristisch; Ergebnisse vor dem Druck prüfen.

## Meldungen

Sicherheitsprobleme bitte als vertrauliche Meldung über die Repository-Plattform melden, nicht als öffentliches Issue.
