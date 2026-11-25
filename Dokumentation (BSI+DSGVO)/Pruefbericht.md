# Prüfbericht CRA-Dokumentation: business-card 1.1.0

Generiert von cra-dokumentation 1.0.0. Stand der SBOM: 2026-11-20T13:05:43Z. Diese Datei wird automatisch überschrieben.

**Gesamtstatus:** 🟡 gelb

## SBOM (BSI TR-03183-2 v2.1.0)

- Format: CycloneDX 1.7 (JSON) ✅
- Komponenten: 14
- Ersteller (Pflichtfeld): KI AffAIrs, info@affairs-consulting.de, https://affairs-consulting.de ✅
- Keine Schwachstellendaten in der SBOM (BSI §3.1) ✅

### Lücken bei Pflichtfeldern

Nicht erfunden, sondern offen ausgewiesen. Ursache meist: Das Lockfile enthält keine SHA-512-Werte (z. B. Python) oder Lizenzen werden ohne Netzabfrage nicht ermittelt.

- **SHA-512-Hash fehlt:** 14 Komponenten, z. B. cffi@2.1.1, colorama@0.4.6, cryptography@46.0.3, iniconfig@2.3.1, numpy@2.4.6, numpy@2.5.5, opencv-python-headless@4.10.0.84, packaging@26.3, pillow@11.0.0, pluggy@1.7.0, pycparser@3.12, pytest@8.3.4, resvg-py@0.5.0, segno@1.6.6
- **Lizenz unbekannt (NOASSERTION):** 14 Komponenten, z. B. cffi@2.1.1, colorama@0.4.6, cryptography@46.0.3, iniconfig@2.3.1, numpy@2.4.6, numpy@2.5.5, opencv-python-headless@4.10.0.84, packaging@26.3, pillow@11.0.0, pluggy@1.7.0, pycparser@3.12, pytest@8.3.4, resvg-py@0.5.0, segno@1.6.6

## CBOM (Kryptografie)

| Verfahren | Bewertung | Fundstellen |
| --- | --- | --- |
| AES-GCM | ✅ ok | service/core.py:73, service/core.py:76, service/core.py:82, service/core.py:86 |
| CSPRNG | ℹ️ Zufall | service/core.py:75, service/core.py:117 |
| SHA-1 | ⚠️ schwach | scripts/wallet.py:160 |
| SHA-256 | ✅ ok | service/core.py:69 |

Ohne Standard-OID (keine erfunden; cdx-validate meldet das als Hinweis): AES-GCM, CSPRNG.

Methode: statische Mustererkennung. Kein Beweis für Vollständigkeit; dynamisch gewählte Verfahren werden nicht erkannt.

## Lebenszyklus (OWASP CLE 1.0 / ECMA-428)

- Releases erfasst: 1 (neuestes: 1.1.0) ✅
- Support-Ende: [OFFEN] Übergabedatum fehlt. Claus fragen, dann in cra-config.json unter uebergabe eintragen; Support-Ende = Übergabe + 5 Jahre (CRA Art. 13 Abs. 8)
- Versionierte SBOM/CBOM: 1.1.0

## Nicht automatisch abgedeckt

- Schwachstellenbehandlung und Meldeprozess (CRA Art. 14, seit 11.09.2026): siehe `BSI-CRA/CRA-Checkliste.md`.
- DSGVO-Angaben: siehe `DSGVO/README.md`.
