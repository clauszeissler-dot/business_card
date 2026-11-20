# Prüfbericht CRA-Dokumentation: business-card 1.0.0

Generiert von cra-dokumentation 1.0.0. Stand der SBOM: 2026-11-20T12:10:54Z. Diese Datei wird automatisch überschrieben.

**Gesamtstatus:** 🟡 gelb

## SBOM (BSI TR-03183-2 v2.1.0)

- Format: CycloneDX 1.7 (JSON) ✅
- Komponenten: 10
- Ersteller (Pflichtfeld): KI AffAIrs, info@affairs-consulting.de, https://affairs-consulting.de ✅
- Keine Schwachstellendaten in der SBOM (BSI §3.1) ✅

### Lücken bei Pflichtfeldern

Nicht erfunden, sondern offen ausgewiesen. Ursache meist: Das Lockfile enthält keine SHA-512-Werte (z. B. Python) oder Lizenzen werden ohne Netzabfrage nicht ermittelt.

- **SHA-512-Hash fehlt:** 10 Komponenten, z. B. colorama@0.4.6, iniconfig@2.3.1, numpy@2.4.6, numpy@2.5.5, opencv-python-headless@4.10.0.84, packaging@26.3, pillow@11.0.0, pluggy@1.7.0, pytest@8.3.4, segno@1.6.6
- **Lizenz unbekannt (NOASSERTION):** 10 Komponenten, z. B. colorama@0.4.6, iniconfig@2.3.1, numpy@2.4.6, numpy@2.5.5, opencv-python-headless@4.10.0.84, packaging@26.3, pillow@11.0.0, pluggy@1.7.0, pytest@8.3.4, segno@1.6.6

## CBOM (Kryptografie)

- Keine Krypto-Verwendung im eigenen Quelltext gefunden. Hinweis: Krypto in Abhängigkeiten erfasst die SBOM.

## Lebenszyklus (OWASP CLE 1.0 / ECMA-428)

- [OFFEN] Noch kein Release (Git-Tag wie v1.0.0) und kein Übergabedatum. Die CLE-Datei entsteht beim ersten Tag bzw. mit der Übergabe.

## Nicht automatisch abgedeckt

- Schwachstellenbehandlung und Meldeprozess (CRA Art. 14, seit 11.09.2026): siehe `BSI-CRA/CRA-Checkliste.md`.
- DSGVO-Angaben: siehe `DSGVO/README.md`.
