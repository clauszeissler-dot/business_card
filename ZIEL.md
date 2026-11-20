# Projektziel: linkedin-business-card (Agent-Skill)

- Stand: 2026-11-20
- Owner: Claus Zeißler
- Lebensdauer: dauerhaftes, öffentlich geteiltes Werkzeug (Skill-Repository)
- Outcome: Fachleute und Selbstständige erhalten in unter 10 Minuten eine druck- und teilbare Business Card im eigenen CI plus eine konkrete Einstellungsanleitung für die native LinkedIn Business Card, ohne Designer und ohne Handarbeit beim Ablesen von Farben und Schriften.
- Ausgangswert: kein Skill vorhanden; LinkedIn-Karte nur manuell in der App gestaltbar (Stand 20.11.2026).
- Zielwert und Zeitraum: 3 Beispielprofile erzeugen fehlerfrei Vorder-/Rückseite (SVG, PNG, PDF) mit dekodierbarem QR-Code; Zielprüfung 30 Tage nach Veröffentlichung über Repo-Sterne/Rückmeldungen.

## Nutzerablauf und Abnahme

- Nutzerablauf: Wenn jemand „erstelle mir eine Business Card aus meinem LinkedIn-Profil im Stil von example.com“ sagt, liest der Agent Profil (Export/PDF/Text) und Website-CI ein, wählt Layout/Form/Farbe/Muster, rendert die Karte und gibt die passende Einstellung für die native LinkedIn-Karte aus.
- Sichtbares Ergebnis: Ordner mit `front.svg/png`, `back.svg/png`, `card-print.pdf`, `preview.html`, `linkedin-native-card.md`, `report.json`.
- Vereinbarter Zielort: lokales Git-Repository `40_Skills-Agenten/linkedin-business-card`, eingebunden als Skill unter `~/.claude/skills/linkedin-business-card`.
- Abschlussnachweis am Zielort: `uv run pytest` grün; Beispielkarten gerendert und visuell geprüft; QR-Decode = Profil-URL.
- Bereitstellungsumfang: lokaler Commit. Push zu GitHub/Forgejo erst nach ausdrücklichem Auftrag.
- Relevanter Fehler- oder Ablehnungsfall: URL auf localhost/private IP oder `file://` wird abgelehnt; ungültige LinkedIn-URL bricht mit klarer Meldung ab.

## Umfang und Grenzen

- Erlaubte Außenwirkungen: lesender HTTP-Abruf öffentlicher Websites (CI). Keine Anmeldung, kein Scraping von linkedin.com.
- Leitplanken: kein LinkedIn-Logo, kein Partnerschaftsanschein; Demo-Daten fiktiv.
- Nicht gebaut: Apple-/Google-Wallet-Pässe (brauchen Zertifikat/Issuer-Konto; deckt die native LinkedIn-Karte ab), automatisches Ausfüllen der LinkedIn-App (keine API). Erneut prüfen, wenn LinkedIn eine API oder Web-Version anbietet.

## Zielprüfung nach Veröffentlichung

- Termin: 30 Tage nach Push; Owner Claus.
