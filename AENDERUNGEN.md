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
| A-009 | 2026-11-20 Claus, Chat | Repo zum Teilen über LinkedIn, „möglichst perfekt“ | README DE+EN, Banner, Lizenz, Beispielbilder, CRA-Doku, lokaler Commit | umgesetzt | S7 | README DE/EN, Banner, Hero, MIT, CRA-Doku (gelb: Hashes/Lizenzen der Abhängigkeiten); Push wartet auf Auftrag |

## Statusregeln

offen → in Arbeit → umgesetzt → geprüft (nur mit Beleg und E-NNN).

## Letzter Abschlussabgleich

- Stand: 2026-11-20
- Abgeglichene IDs: A-001 bis A-009
- Geprüft erfüllt: A-001 bis A-007
- Nicht erfüllt: A-008 (LLM-Eval offen), A-009 (Push/Social Preview offen, wartet auf Auftrag)
- Neue Wünsche seit dem letzten Abgleich vollständig erfasst: ja
