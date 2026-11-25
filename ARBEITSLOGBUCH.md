# Projekt-Arbeitslogbuch

Ziel: [ZIEL.md](ZIEL.md) · Anforderungen: [AENDERUNGEN.md](AENDERUNGEN.md) · Aktueller Einstieg: [PLAN.md](PLAN.md)

## 2026-11-20 – Recherche und Projektstart

- Anforderungs-IDs: A-001, A-002, A-003, A-004, A-005, A-006, A-007, A-008, A-009
- Ergebnis: Offizielle LinkedIn-Hilfe (answer/a16648713) und News-Beitrag vom 15.10.2026 ausgewertet; Firecrawl kann linkedin.com nicht lesen, WebFetch schon.
- Entscheidung: Zwei Ausgaben – (1) Empfehlung für native LinkedIn-Karte, (2) eigene CI-Karte. Kein LinkedIn-Scraping, keine Wallet-Pässe.
- Versionsbezug: noch nicht committed

## 2026-11-20 – Umsetzung v1.0.0

- Anforderungs-IDs: A-001, A-002, A-003, A-004, A-005, A-006, A-007, A-008, A-009
- Ergebnis: Skripte make_card, extract_ci, parse_profile, native; 174 Tests grün; Evals offline 13/13; Beispiele und Hero gerendert und visuell geprüft.
- Red/Green: jeweils rote Tests vor Implementierung (Importfehler, danach fachliche Fehler: Kontrast 3,6 bei hellem Muster, Namenskürzung, Schrift < 2 mm, falsche Primärfarbe bei Realtests) → behoben, grün.
- Kurskorrektur: Realtests zeigten HTTP 400 (Nicht-ASCII-User-Agent) und schwaches Farbranking → Regressionstests ergänzt.
- Versionsbezug: erster lokaler Commit
- Offen: Push nach Auftrag, LLM-Eval, PDF-Heuristik an echtem LinkedIn-PDF.

## 2026-11-20 – Veröffentlichung

- Anforderungs-IDs: A-009
- Ergebnis: Push nach https://github.com/clauszeissler-dot/business_card (Auftrag Claus); Skill-Name business-card; Beschreibung und Topics gesetzt; frischer Klon: 182 Tests grün, Evals offline 10/10.
- Offen: Social Preview (hero.png) in GitHub-Einstellungen hochladen; LLM-Eval; echtes Profil-PDF testen.

## 2026-11-20 – Phase 1: Handy, Wallet, Apps

- Anforderungs-IDs: A-010, A-011, A-012, A-013, A-014
- Ergebnis: extras.py, wallet.py, render.py, Sticker-Rückseite, ZIP-Builder; 204 Tests grün, Evals offline 13/13.
- Red/Green: neue Tests zuerst rot (Importfehler/fehlende Funktionen), dann grün; resvg-Fehler „invalid size“ bei mm-Einheiten → dpi=96 gesetzt.
- Entscheidung Claus: Dienst öffentlich für alle (A-015, A-016); LinkedIn-Login nur über Server (Client-Secret).
- Offen: A-015/A-016 Dienst; Echttests Wallet und Apps.

## 2026-11-20 – Phase 2: Online-Dienst vorbereitet

- Anforderungs-IDs: A-015, A-016
- Ergebnis: service/ + api/index.py + public/ (Oberfläche, Datenschutz), vercel.json mit CSP; 22 Dienst-Tests (OAuth-State, Sitzung, Origin, fremde Namen, Größenlimit, Share-Flow) + Env-Übertragung ohne Wertausgabe; insgesamt 229 Tests grün.
- Blocker: Vercel-MCP 403 beim Projektanlegen; CLI nicht angemeldet; temporäre Deploys ohne Login nicht möglich → Import-Seite in Ego Lite geöffnet, Claus klickt „Deploy“.
- Vorbereitet: ~/Desktop/business-card-secrets (secrets.env mit SESSION_SECRET, ANLEITUNG.md, Erzeugung vercel-import.env); außerhalb des Repos.
- Offen: Deploy-Nachweis am Zielort, Echttests Login/Apple/Google/Share, Vercel-Tarif, Rate-Limit-Regel.

## 2026-11-20 Sitzungsende

- Anforderungs-IDs: A-013, A-014, A-015, A-016
- Ergebnis: Abschlussabgleich; Claus hat `push_vercel_env.py --write-env` ausgeführt, 8 Werte fehlen noch (LinkedIn, Apple, Google) → vercel-import.env noch nicht verwenden.
- Prüfung: `arbeitsstandard.py verify .` grün (Evals 13/13, Tests grün).
- Offen: Secrets eintragen, Deploy, Echttests, Rate-Limit, Vercel-Tarif.

## 2026-11-25 – Wiederaufnahme

- Anforderungs-IDs: A-013, A-015, A-016
- Ergebnis: Stand geprüft; in secrets.env fehlen weiter LINKEDIN_CLIENT_ID/SECRET, APPLE_PASS_TYPE_ID, APPLE_TEAM_ID, GOOGLE_ISSUER_ID (nur Namen geprüft, keine Werte gelesen). Entscheidung Claus: alles auf einmal eintragen, dann ein Deploy.
- Offen: Secrets durch Claus, Deploy, Echttests.

## 2026-11-25 – LinkedIn-App eingerichtet

- Anforderungs-IDs: A-015, A-016
- Ergebnis: Neue LinkedIn-App mit OIDC + Share, Redirect-URL, Client ID/Secret in secrets.env (Abgleich Datei = aktives Secret: ja). Altes, im Protokoll sichtbares Secret entfernt.
- Offen: Apple, Google, Deploy, Echttests.

## 2026-11-25 – Datenschutzhinweise

- Anforderungs-IDs: A-017
- Red/Green: test_datenschutz.py 4 rot (fehlende Cookies, Scopes, Empfänger) → Seite neu → grün; Gesamtsuite 232 grün.
- Sichtprüfung Ego Lite: Links vorher dunkelblau auf dunklem Grund, nach CSS-Fix #2DD4BF.

## 2026-11-25 – Apple Wallet eingerichtet

- Anforderungs-IDs: A-013, A-016
- Ergebnis: Apple-Lizenzvereinbarung LYL262 nach Freigabe Claus akzeptiert; Pass Type ID pass.de.affairs-consulting.card, Zertifikat aus lokal erzeugter CSR, pass.p12 mit Zufallspasswort in ~/Desktop/business-card-secrets; Team ID, Pass Type ID, Passwort in secrets.env (nicht ausgegeben). Echter Test-Pass über service.core.apple_pkpass signiert, `openssl smime -verify` erfolgreich, Kette WWDR G4.
- Offen: Google Wallet, Deploy, Test auf iPhone.

## 2026-11-25 – Google Wallet eingerichtet

- Anforderungs-IDs: A-013, A-016
- Ergebnis: Issuer-Konto KI AffAIrs (Workspace-Konto), Wallet-API-Bedingungen nach Freigabe akzeptiert, Cloud-Projekt business-card-wallet-515810, Wallet-API aktiv, Dienstkonto als Entwickler eingeladen, JSON-Schlüssel 0600 im Secrets-Ordner. Live-Test: OAuth-Token und GET issuer erfolgreich; google_link signiert.
- Kurskorrektur: Downloads in der Agentensitzung kamen verzögert in ~/Downloads an; zwei als verloren angenommene Schlüssel gelöscht, ein dritter nachträglich gefundener gehörte zu einem gelöschten Schlüssel. Endgültiger Schlüssel per Abgleich Key-ID geprüft.
- Sicherheit: Org-Richtlinie iam.disableServiceAccountKeyCreation nur kurz für das Projekt ausgesetzt und wieder erzwungen, temporäre Rolle entfernt.
- push_vercel_env --dry-run: alle 11 Werte vorhanden.
- Offen: Vercel-Deploy, Echttests, Veröffentlichungszugriff Google.

## 2026-11-25 – Rückmeldung nach erstem Live-Login (A-018 bis A-020)
- Live-Login mit LinkedIn funktioniert (Name, Foto, E-Mail angezeigt; Screenshot von Claus) – Beleg für A-015.
- Claus: zu viel Tippen, private E-Mail auf der Karte, vCard/Sperrbildschirm fehlen im Dienst.
- Umgesetzt mit TDD (17 + 6 Tests erst rot, dann grün; 2 Datenschutztests rot → grün); Gesamtsuite 259 grün.
- Offen: Push/Deploy (Vercel baut aus GitHub), Live-Test Downloads und Rendering-Zeit.
- Push 20e0bbf nach Freigabe Claus; live geprüft: alle vier Downloads 200, Rendering ≤ 1,1 s, QR dekodiert.
