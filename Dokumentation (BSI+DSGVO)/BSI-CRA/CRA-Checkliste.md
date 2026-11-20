# CRA-Checkliste: linkedin-business-card

Diese Datei wird einmalig angelegt und danach **nie automatisch überschrieben**. Haken setzen (`[x]`), offene Punkte mit
Owner und Termin ergänzen. Grundlage: Verordnung (EU) 2024/2847 (Cyber Resilience Act). Orientierung, keine Rechtsberatung.

## 0. Anwendbarkeit

- [ ] Produkt mit digitalen Elementen, das in der EU bereitgestellt wird (Verkauf, kostenlose Abgabe im Rahmen einer Geschäftstätigkeit, Kundenauftrag)? [OFFEN: ja/nein | Owner Claus]
- [ ] Ausnahme geprüft (reine Eigennutzung, nicht-kommerzielle Open Source, SaaS ohne Fernverarbeitungs-Bezug zu einem Produkt)? [OFFEN]
- [ ] Produktklasse: Standard / wichtig Klasse I / wichtig Klasse II / kritisch (Anhang III/IV) [OFFEN]

## 1. Fristen

| Datum | Pflicht |
| --- | --- |
| 11.09.2026 | Meldepflicht für aktiv ausgenutzte Schwachstellen und schwere Vorfälle (Art. 14) über die ENISA-Meldeplattform: Frühwarnung 24 h, Meldung 72 h, Abschlussbericht 14 Tage bzw. 1 Monat |
| 11.12.2027 | Alle übrigen Pflichten: wesentliche Anforderungen Anhang I, SBOM, technische Dokumentation Anhang VII, Konformitätsbewertung, CE-Kennzeichnung |

## 2. Automatisch gepflegt (Ordner `Dokumentation (BSI+DSGVO)`)

- SBOM maschinenlesbar, mindestens oberste Abhängigkeiten (Anhang I Teil II Nr. 1) → `SBOM/sbom.cdx.json`
- Eine SBOM je Version (BSI TR-03183-2) → `SBOM/versionen/<Version>/`
- Krypto-Inventar (Stand der Technik, Anhang I Teil I Nr. 2 e) → `CBOM/cbom.cdx.json`
- Releases und Support-Ende maschinenlesbar → `Lebenszyklus/cle.json`

## 3. Wesentliche Anforderungen Anhang I Teil I (Produkt)

- [ ] Risikobewertung dokumentiert (Art. 13 Abs. 2/3) [OFFEN]
- [ ] Keine bekannten ausnutzbaren Schwachstellen bei Auslieferung [OFFEN: Scan-Befehl/Ergebnis]
- [ ] Sichere Standardkonfiguration, Rücksetzen auf Werkseinstellungen möglich
- [ ] Schutz vor unbefugtem Zugriff (Authentisierung, Rechte)
- [ ] Vertraulichkeit (Verschlüsselung nach Stand der Technik, siehe CBOM/Prüfbericht)
- [ ] Integrität von Daten, Programmen und Konfiguration
- [ ] Datenminimierung (Bezug DSGVO)
- [ ] Verfügbarkeit, Resilienz gegen DoS
- [ ] Minimierung der Angriffsfläche
- [ ] Protokollierung sicherheitsrelevanter Ereignisse (mit Opt-out für Nutzer)
- [ ] Sicherheitsupdates automatisch, getrennt von Funktionsupdates, mit Opt-out

## 4. Schwachstellenbehandlung Anhang I Teil II (Prozess)

- [ ] SBOM vorhanden und aktuell (automatisch, siehe oben)
- [ ] Schwachstellen-Überwachung der Abhängigkeiten (z. B. `cdxgen`-SBOM in Dependency-Track oder `osv-scanner`) [OFFEN]
- [ ] Sicherheitsupdates kostenlos und unverzüglich
- [ ] Regelmäßige Tests und Überprüfungen
- [ ] Veröffentlichung behobener Schwachstellen (Advisory, z. B. CSAF 2.0 nach BSI TR-03183-3)
- [ ] Richtlinie zur koordinierten Offenlegung (CVD) und Kontaktadresse, z. B. `/.well-known/security.txt` (RFC 9116) [OFFEN]
- [ ] Sichere Verteilung der Updates (Signatur/Integrität)

## 5. Hersteller-Pflichten

- [ ] Support-Zeitraum: gesetzliche Mindestfrist 5 Jahre ab Übergabe (Art. 13 Abs. 8) → Übergabedatum in `cra-config.json` unter `uebergabe` eintragen, Support-Ende entsteht automatisch [OFFEN: Übergabedatum]
- [ ] Meldeprozess nach Art. 14 eingerichtet (wer meldet, Zugang zur ENISA-Plattform, 24-h-Bereitschaft) [OFFEN]
- [ ] Technische Dokumentation nach Anhang VII (inkl. SBOM, Risikobewertung, Prüfnachweise) [OFFEN]
- [ ] Informationen und Anleitungen für Nutzer nach Anhang II (Kontakt, Support-Ende, ggf. Fundort der SBOM) [OFFEN]
- [ ] EU-Konformitätserklärung und CE-Kennzeichnung (ab 11.12.2027) [OFFEN]
- [ ] Aufbewahrung der Dokumentation 10 Jahre bzw. für die Dauer des Support-Zeitraums [OFFEN]
