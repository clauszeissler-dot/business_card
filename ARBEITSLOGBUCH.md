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
