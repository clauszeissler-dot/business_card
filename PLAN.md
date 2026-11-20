# Aktueller Arbeitsplan

**Sichtbares Arbeitsziel:** Claus kann den Skill `linkedin-business-card` aufrufen und erhält Karte + LinkedIn-Einstellungsanleitung; das Repo ist teilbereit.
**Zielort:** lokales Repo `40_Skills-Agenten/linkedin-business-card` + Symlink `~/.claude/skills/linkedin-business-card`.
**Abschlussnachweis:** `uv run pytest` grün, Beispielkarten visuell geprüft, QR-Decode, lokaler Commit.

Stand: 2026-11-20

## Arbeitsschritte

| Schritt | Anforderungs-IDs | Ergebnis | Status | Prüfung |
| --- | --- | --- | --- | --- |
| S1 | A-001 | references/linkedin-native-card.md | erledigt | Quellenabgleich |
| S2 | – (Gate) | Security Contract (DevSecurity develop, S1 wegen URL-Abruf) | erledigt | Missbrauchstests |
| S3 | A-002, A-003, A-004, A-007 | scripts/make_card.py + Tests | erledigt | pytest, QR-Decode, Sichtprüfung |
| S4 | A-005 | scripts/parse_profile.py + Tests | erledigt | pytest |
| S5 | A-006 | scripts/extract_ci.py + Tests | erledigt | pytest inkl. SSRF |
| S6 | A-008 | SKILL.md, evals, Symlink | erledigt (LLM-Eval offen) | Eval-Durchlauf |
| S8 | A-010, A-011, A-012 | scripts/extras.py, Sticker-Rückseite + Tests | erledigt | pytest, Sichtprüfung |
| S9 | A-013 | scripts/wallet.py (Apple .pkpass, Google-Save-Link) + Tests mit Testschlüsseln | erledigt (Echttest offen) | pytest, Signaturprüfung |
| S10 | A-014 | render.py (resvg + Schriften), App-Abschnitt in SKILL.md, ZIP-Builder | erledigt (App-Test offen) | pytest, ZIP-Inhalt |
| S11 | A-015, A-016 | Dienst auf Vercel (Login, Wallet, Share, Rechtstexte) | offen | Deploy-Nachweis, Missbrauchstests |
| S7 | A-009 | README DE/EN, Beispiele, CRA, Commit | lokal erledigt, Push offen | Repo-Standard-Check |

## Aktueller Zielabgleich

- Arbeitsbeginn: 2026-11-20 (Recherche abgeschlossen)
- Zum sichtbaren Ergebnis fehlt: Social Preview; Vercel-Deploy mit vollständigen Secrets; Echttests Login/Apple/Google/Share
- Kürzester nächster Schritt: Claus trägt LinkedIn Client ID/Secret in ~/Desktop/business-card-secrets/secrets.env ein (danach Apple, Google, `push_vercel_env.py --write-env`, Deploy)
- Nächster konkreter Schritt: nach Meldung „Deploy fertig“ /api/health prüfen, Echttests in Ego Lite, Rate-Limit-Regel
